"""
Orion Signals — Pro Dashboard
⚡ Stocks Pro €79/μήνα

Layout:
  ┌──────────────────────┬───────────────────────┐
  │  LEFT — manual       │  RIGHT — Today's Picks │
  │  analyze any ticker  │  auto-scanned, ranked  │
  │  + confirmation/earn │  fuel + target inline  │
  └──────────────────────┴───────────────────────┘

ΣΗΜΕΙΩΣΗ DATA SOURCE: τα δεδομένα έρχονται από load_data()
στο indicators.py (Yahoo Finance τώρα). Για live feed, άλλαξε
ΜΟΝΟ εκείνη τη συνάρτηση — εδώ δεν χρειάζεται καμία αλλαγή.
"""
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import streamlit as st
import yfinance as yf

from indicators import (
    inject_css, load_data, full_analysis, create_chart,
    screen_ticker, run_backtest, get_dow, get_nasdaq100, get_sp500,
    atr_calc, fuel_gauge, fuel_bar, confirmation_entry,
    check_earnings, target_projection,
)


# ============================================================
# TODAY'S PICKS — auto scan + rank
# ============================================================
@st.cache_data(ttl=1800, show_spinner=False)
def scan_todays_picks(universe="dow", top_n=8, min_score=10):
    """
    Σκανάρει το universe, βαθμολογεί, και επιστρέφει τα top picks
    με fuel gauge + target. Cached 30 λεπτά (1 scan για όλους).
    """
    tickers = {"dow": get_dow, "nasdaq100": get_nasdaq100, "sp500": get_sp500}[universe]()
    results = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(screen_ticker, t): t for t in tickers}
        for f in as_completed(futures):
            r = f.result()
            if r:
                results.append(r)

    # Ταξινόμηση όλων με score, κρατάμε τα top με θετικό verdict ΑΝ υπάρχουν
    results.sort(key=lambda x: x["combined"], reverse=True)
    buys = [r for r in results if r["verdict"] in ("BUY", "STRONG BUY") and r["combined"] >= min_score]

    # Αν δεν υπάρχουν καθαρά buys, δείξε τα top scored ούτως ή άλλως (best available)
    pool = buys if buys else results[:top_n]
    top = pool[:top_n]

    # Εμπλούτισε με fuel + target
    enriched = []
    for r in top:
        df = load_data(r["ticker"], "6mo")
        if df is None or len(df) < 60:
            continue
        fg = fuel_gauge(df)
        tp = target_projection(df)
        atr = float(atr_calc(df).iloc[-1])
        entry = r["price"] * 1.015
        sl = entry - 1.5 * atr
        tgt = entry + 3 * atr
        rr = (tgt - entry) / (entry - sl) if (entry - sl) > 0 else 0
        enriched.append({
            **r,
            "fuel":     fg["fuel"] if fg else None,
            "fuel_status": fg["status"] if fg else None,
            "entry":    entry, "sl": sl, "target": tgt, "rr": rr,
            "tgt_low":  tp["low"] if tp else None,
            "tgt_high": tp["high"] if tp else None,
            "tgt_pct_low":  tp["pct_low"] if tp else None,
            "tgt_pct_high": tp["pct_high"] if tp else None,
        })
    return enriched


def render_pick_card(p, idx):
    """Ένα pick card στο δεξί panel."""
    fuel = p.get("fuel")
    fuel_status = p.get("fuel_status", "")
    bar = fuel_bar(fuel) if fuel is not None else "░░░░░░░░░░"
    fuel_color = ("#00C853" if fuel and fuel >= 65 else
                  "#F59E0B" if fuel and fuel >= 35 else "#FF3D57")
    status_label = {"healthy": "healthy", "slowing": "⚠️ slowing",
                    "exhausted": "🛑 exhausted"}.get(fuel_status, "")
    verdict_color = "#00C853" if "STRONG" in p["verdict"] else "#69F0AE"

    tgt_txt = ""
    if p.get("tgt_pct_low") is not None:
        tgt_txt = (f"<div class='pick-target'>🎯 Est. ${p['tgt_low']:.0f}–${p['tgt_high']:.0f} "
                   f"({p['tgt_pct_low']:+.0f}% to {p['tgt_pct_high']:+.0f}%)</div>")

    st.markdown(f"""
    <div class="pick-card">
        <div class="pick-top">
            <span class="pick-ticker">{p['ticker']}</span>
            <span class="pick-verdict" style="color:{verdict_color}">{p['verdict']}</span>
        </div>
        <div class="pick-price">${p['price']:.2f}
            <span class="pick-score">Score {p['combined']:+.0f}</span>
        </div>
        <div class="pick-fuel">
            <span class="fuel-bar" style="color:{fuel_color}">{bar}</span>
            <span class="fuel-pct" style="color:{fuel_color}">{fuel if fuel is not None else '–'}%</span>
            <span class="fuel-status">{status_label}</span>
        </div>
        <div class="pick-levels">
            ⚡ ${p['entry']:.2f} · 🛑 ${p['sl']:.2f} · 🎯 ${p['target']:.2f} · R/R 1:{p['rr']:.1f}
        </div>
        {tgt_txt}
    </div>
    """, unsafe_allow_html=True)

    if st.button(f"🔍 Analyze {p['ticker']}", key=f"pick_analyze_{idx}", use_container_width=True):
        st.session_state.pro_picked = p["ticker"]
        st.session_state.pro_last_scanned = p["ticker"]
        st.rerun()


# ============================================================
# PORTFOLIO
# ============================================================
def portfolio_tab_pro():
    if "portfolio_pro" not in st.session_state:
        st.session_state.portfolio_pro = []
    portfolio = st.session_state.portfolio_pro
    st.markdown("#### 💼 Portfolio Tracker")
    st.caption("Pro plan: unlimited positions")
    open_pos = [p for p in portfolio if p['status'] == 'open']
    with st.expander("➕ Add New Position", expanded=len(open_pos) == 0):
        c1, c2, c3 = st.columns(3)
        t = c1.text_input("Ticker", placeholder="AAPL", key="pro_pt").upper()
        ep = c2.number_input("Entry Price ($)", min_value=0.01, value=100.0, key="pro_pep")
        sh = c3.number_input("Shares", min_value=1, value=10, key="pro_psh")
        c4, c5 = st.columns(2)
        sl = c4.number_input("Stop Loss ($)", min_value=0.01, value=round(ep*0.95, 2), key="pro_psl")
        tgt = c5.number_input("Target ($)", min_value=0.01, value=round(ep*1.10, 2), key="pro_ptgt")
        if st.button("Add Position →", key="pro_padd"):
            if t:
                st.session_state.portfolio_pro.append({
                    'ticker': t, 'entry': ep, 'shares': sh, 'sl': sl, 'target': tgt,
                    'status': 'open', 'date_in': datetime.now().strftime("%d/%m/%Y"),
                    'date_out': None, 'exit_price': None, 'pnl': None
                })
                st.success(f"✅ {t} added!")
                st.rerun()
    st.markdown("---")
    if not open_pos:
        st.info("No open positions yet.")
    else:
        st.markdown(f"**Open Positions: {len(open_pos)}**")
        for i, pos in enumerate(portfolio):
            if pos['status'] != 'open':
                continue
            try:
                cp = float(yf.download(pos['ticker'], period="1d", progress=False, auto_adjust=True)['Close'].iloc[-1])
            except:
                cp = pos['entry']
            pnl_pct = (cp-pos['entry'])/pos['entry']*100
            pnl_usd = (cp-pos['entry'])*pos['shares']
            cls = "pnl-pos" if pnl_pct >= 0 else "pnl-neg"
            ico = "🟢" if pnl_pct >= 0 else "🔴"
            c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
            c1.markdown(f"**{pos['ticker']}**\n\n`{pos['shares']} shares`")
            c2.markdown(f"Entry: **${pos['entry']:.2f}**\n\nNow: **${cp:.2f}**")
            c3.markdown(f"SL: `${pos['sl']:.2f}`\n\nTarget: `${pos['target']:.2f}`")
            c4.markdown(f"<span class='{cls}'>{ico} {pnl_pct:+.2f}%<br>${pnl_usd:+.2f}</span>", unsafe_allow_html=True)
            if c5.button("Sold", key=f"pro_sold_{i}"):
                st.session_state.portfolio_pro[i].update({'status': 'closed', 'exit_price': cp,
                    'date_out': datetime.now().strftime("%d/%m/%Y"), 'pnl': pnl_usd})
                st.rerun()
            if cp <= pos['sl']:
                st.error(f"⚠️ {pos['ticker']} hit Stop Loss!")
            if cp >= pos['target']:
                st.success(f"🎯 {pos['ticker']} hit Target!")
            st.markdown("---")
    closed = [p for p in portfolio if p['status'] == 'closed']
    if closed:
        st.markdown("**Closed Positions**")
        total = sum(p['pnl'] for p in closed if p['pnl'])
        cls = "pnl-pos" if total >= 0 else "pnl-neg"
        st.markdown(f"Total P&L: <span class='{cls}'>${total:+.2f}</span>", unsafe_allow_html=True)
        df_c = pd.DataFrame([{
            'Ticker': p['ticker'], 'Entry': f"${p['entry']:.2f}",
            'Exit': f"${p['exit_price']:.2f}" if p['exit_price'] else '-',
            'Shares': p['shares'], 'P&L': f"${p['pnl']:+.2f}" if p['pnl'] else '-',
            'In': p['date_in'], 'Out': p['date_out'] or '-'
        } for p in closed])
        st.dataframe(df_c, use_container_width=True, hide_index=True)


# ============================================================
# MAIN DASHBOARD
# ============================================================
def show_pro_dashboard(user):
    inject_css()

    st.markdown("""
    <style>
    .pro-badge{background:rgba(124,58,237,0.2);color:#A78BFA;
        border:1px solid rgba(124,58,237,0.4);padding:0.25rem 0.75rem;
        border-radius:20px;font-size:0.75rem;font-weight:600;letter-spacing:0.08em}
    .pnl-pos{color:#00C853;font-weight:700}
    .pnl-neg{color:#FF3D57;font-weight:700}
    /* Picks panel */
    .picks-title{font-family:'Syne',sans-serif;font-size:1rem;font-weight:800;
        color:#fff;margin-bottom:0.2rem}
    .picks-sub{font-size:0.72rem;color:rgba(255,255,255,0.35);margin-bottom:1rem}
    .pick-card{background:rgba(255,255,255,0.025);border:1px solid rgba(124,58,237,0.2);
        border-radius:12px;padding:0.85rem 1rem;margin-bottom:0.4rem}
    .pick-top{display:flex;justify-content:space-between;align-items:center}
    .pick-ticker{font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:800;color:#fff}
    .pick-verdict{font-size:0.7rem;font-weight:700;letter-spacing:0.05em}
    .pick-price{font-size:0.9rem;color:rgba(255,255,255,0.85);margin:0.2rem 0}
    .pick-score{font-size:0.72rem;color:rgba(167,139,250,0.8);margin-left:0.5rem}
    .pick-fuel{display:flex;align-items:center;gap:0.5rem;margin:0.4rem 0}
    .fuel-bar{font-family:monospace;font-size:0.85rem;letter-spacing:-1px}
    .fuel-pct{font-size:0.78rem;font-weight:700}
    .fuel-status{font-size:0.68rem;color:rgba(255,255,255,0.4)}
    .pick-levels{font-size:0.7rem;color:rgba(255,255,255,0.55);margin-top:0.3rem}
    .pick-target{font-size:0.7rem;color:rgba(0,200,83,0.7);margin-top:0.2rem}
    .toggle-row{background:rgba(124,58,237,0.05);border:1px solid rgba(124,58,237,0.15);
        border-radius:10px;padding:0.5rem 0.85rem;margin:0.5rem 0}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="orion-header">
        <div class="orion-logo">🎯 Orion <span>Signals</span></div>
        <span class="pro-badge">⚡ Stocks Pro</span>
    </div>""", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f"**👤 {user['name']}**")
        st.markdown(f"*{user['email']}*")
        st.markdown("---")
        if st.button("🚪 Logout", key="pro_logout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["⚡ Today's Picks", "📊 Backtest", "💼 Portfolio"])

    # ════════════════════════════════════════════════════
    # TAB 1 — TODAY'S PICKS (two-column)
    # ════════════════════════════════════════════════════
    with tab1:
        left, right = st.columns([3, 2], gap="large")

        # ── RIGHT: auto picks ──
        with right:
            st.markdown('<div class="picks-title">⚡ Today\'s Picks</div>', unsafe_allow_html=True)
            st.markdown('<div class="picks-sub">Auto-scanned · ranked by score · with fuel & target</div>',
                        unsafe_allow_html=True)

            uni = st.selectbox("Universe", ["dow", "nasdaq100", "sp500"],
                               format_func=lambda x: {"dow": "Dow 30 (fast)", "nasdaq100": "NASDAQ 100",
                                                      "sp500": "S&P 500 (slow)"}[x],
                               key="picks_universe", label_visibility="collapsed")

            if st.button("🔄 Refresh scan", key="refresh_picks", use_container_width=True):
                scan_todays_picks.clear()
                st.rerun()

            with st.spinner("Scanning the market..."):
                picks = scan_todays_picks(universe=uni)

            if not picks:
                st.info("Scanning returned nothing — the market data source may be rate-limited. Press Refresh in a moment.")
            else:
                buys = [p for p in picks if p["verdict"] in ("BUY", "STRONG BUY")]
                if buys:
                    st.caption(f"Found {len(buys)} strong setups")
                else:
                    st.caption("No strong buys today — showing best-scored stocks")
                for i, p in enumerate(picks):
                    render_pick_card(p, i)

        # ── LEFT: manual analysis ──
        with left:
            # Αν διάλεξε από picks, γέμισε το πεδίο μ' αυτό (μία φορά)
            if "pro_picked" in st.session_state:
                st.session_state.pro_manual_ticker = st.session_state.pop("pro_picked")

            c1, c2 = st.columns([2, 1])
            ticker = c1.text_input("Analyze any ticker", key="pro_manual_ticker",
                                   placeholder="e.g. GME").upper().strip()
            period = c2.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
                                  index=3, key="pro_period")

            # User-controlled toggles
            st.markdown('<div class="toggle-row">', unsafe_allow_html=True)
            tc1, tc2 = st.columns(2)
            use_confirmation = tc1.checkbox("✅ Confirmation entry (+1.5%)", value=False,
                                            help="Shows whether the stock has already started moving (+1.5%) before you enter — avoids premature entries")
            use_earnings = tc2.checkbox("📅 Check earnings", value=False,
                                        help="Warns if earnings are within the next 7 days — earnings can cause unpredictable swings")
            st.markdown('</div>', unsafe_allow_html=True)

            # Scan button (χειροκίνητο)
            do_scan = st.button("🔍 Scan this ticker", key="manual_scan", use_container_width=True)

            if ticker and (do_scan or st.session_state.get("pro_last_scanned") == ticker):
                st.session_state.pro_last_scanned = ticker
                with st.spinner(f"Analyzing {ticker}..."):
                    df = load_data(ticker, period)
                if df is None:
                    st.error(f"No data for {ticker}")
                else:
                    a = full_analysis(df)
                    vc = {"STRONG BUY": "verdict-strong-buy", "BUY": "verdict-buy",
                          "STRONG SELL": "verdict-sell", "SELL": "verdict-sell"}.get(a['verdict'], "verdict-neutral")
                    ico = {"STRONG BUY": "🟢", "BUY": "🟢", "STRONG SELL": "🔴", "SELL": "🔴",
                           "MIXED SIGNALS": "🟡"}.get(a['verdict'], "⚪")
                    st.markdown(f'<div class="verdict-banner {vc}">{ico} {a["verdict"]} — {ticker}</div>',
                                unsafe_allow_html=True)

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Price", f"${a['current']:.2f}")
                    m2.metric("Score", f"{a['combined']:+.1f}")
                    m3.metric("Momentum", f"{a['mom_score']:+.1f}")
                    m4.metric("Technical", f"{a['tech_score']:+.1f}")

                    # Fuel gauge
                    fg = fuel_gauge(df)
                    if fg:
                        fcol = ("#00C853" if fg["fuel"] >= 65 else
                                "#F59E0B" if fg["fuel"] >= 35 else "#FF3D57")
                        st.markdown(f"""
                        <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(124,58,237,0.2);
                                    border-radius:10px;padding:0.85rem 1rem;margin:0.75rem 0;">
                            <div style="display:flex;justify-content:space-between;align-items:center;">
                                <span style="font-family:'Syne';font-weight:700;color:#fff;">🔋 Fuel Gauge</span>
                                <span style="color:{fcol};font-weight:800;font-size:1.1rem;">{fg['fuel']}%</span>
                            </div>
                            <div style="font-family:monospace;font-size:1.1rem;color:{fcol};letter-spacing:-1px;margin:0.3rem 0;">
                                {fuel_bar(fg['fuel'])}
                            </div>
                            <div style="font-size:0.75rem;color:rgba(255,255,255,0.5);">
                                Status: {fg['status']} — {'healthy momentum' if fg['status']=='healthy' else 'losing steam, watch closely' if fg['status']=='slowing' else 'exhausted, reversal risk'}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        # Fuel signals
                        triggered = [t for t, tr in fg["signals"] if tr]
                        if triggered:
                            st.caption("⚠️ Exhaustion signals: " + " · ".join(triggered))

                    # ATR levels
                    atr_v = float(atr_calc(df).iloc[-1])
                    entry = a['current'] * 1.015
                    sl = entry - 1.5 * atr_v
                    tgt = entry + 3 * atr_v
                    rr = (tgt - entry) / (entry - sl) if (entry - sl) > 0 else 0
                    p1, p2, p3, p4 = st.columns(4)
                    p1.metric("Entry (+1.5%)", f"${entry:.2f}")
                    p2.metric("Stop Loss", f"${sl:.2f}")
                    p3.metric("Target", f"${tgt:.2f}")
                    p4.metric("Risk/Reward", f"1:{rr:.1f}")

                    # Target projection
                    tp = target_projection(df)
                    if tp:
                        st.markdown(f"""
                        <div style="background:rgba(0,200,83,0.05);border:1px solid rgba(0,200,83,0.2);
                                    border-radius:10px;padding:0.7rem 1rem;margin:0.5rem 0;font-size:0.82rem;">
                            🎯 <strong style="color:#00C853;">Est. target ${tp['low']:.2f}–${tp['high']:.2f}</strong>
                            <span style="color:rgba(255,255,255,0.5);">({tp['pct_low']:+.1f}% to {tp['pct_high']:+.1f}%)</span><br>
                            <span style="font-size:0.7rem;color:rgba(255,255,255,0.35);">Estimate — not a guarantee. Based on ATR, resistance & volatility.</span>
                        </div>
                        """, unsafe_allow_html=True)

                    # Confirmation entry (user toggle)
                    if use_confirmation:
                        ce = confirmation_entry(df)
                        col = "#00C853" if ce["confirmed"] else "#F59E0B"
                        st.markdown(f"""
                        <div style="background:rgba(124,58,237,0.05);border:1px solid rgba(124,58,237,0.2);
                                    border-radius:10px;padding:0.7rem 1rem;margin:0.5rem 0;font-size:0.85rem;color:{col};">
                            {ce['message']}
                        </div>
                        """, unsafe_allow_html=True)

                    # Earnings (user toggle)
                    if use_earnings:
                        ern = check_earnings(ticker)
                        if ern["has_earnings"] is True:
                            st.warning(ern["message"] + " — consider waiting until after earnings.")
                        elif ern["has_earnings"] is False:
                            st.success(ern["message"])
                        else:
                            st.caption(ern["message"])

                    # Αποθήκευση για full-width chart κάτω από τα columns
                    st.session_state.pro_chart_data = {
                        "df": df, "a": a, "ticker": ticker,
                        "entry": entry, "sl": sl, "tgt": tgt,
                    }

    # ── FULL-WIDTH CHART (έξω από τα columns) ──
    chart_data = st.session_state.get("pro_chart_data")
    if chart_data is not None:
        st.markdown("---")
        st.markdown(f"#### 📈 {chart_data['ticker']} — Full Chart")
        st.plotly_chart(create_chart(chart_data["df"], chart_data["a"], height=820),
                        use_container_width=True,
                        config={"displayModeBar": True, "scrollZoom": True,
                                "displaylogo": False})

        if st.button(f"➕ Add {chart_data['ticker']} to Portfolio", key="add_from_analysis"):
            if "portfolio_pro" not in st.session_state:
                st.session_state.portfolio_pro = []
            st.session_state.portfolio_pro.append({
                'ticker': chart_data['ticker'], 'entry': round(chart_data['entry'], 2),
                'shares': 10, 'sl': round(chart_data['sl'], 2), 'target': round(chart_data['tgt'], 2),
                'status': 'open', 'date_in': datetime.now().strftime("%d/%m/%Y"),
                'date_out': None, 'exit_price': None, 'pnl': None
            })
            st.success(f"✅ {chart_data['ticker']} added to portfolio (10 shares @ ${chart_data['entry']:.2f})")

    # ════════════════════════════════════════════════════
    # TAB 2 — BACKTEST
    # ════════════════════════════════════════════════════
    with tab2:
        st.markdown("Test strategy edge over random entry.")
        st.success("⚡ Pro: up to 10 years history")
        c1, c2, c3, c4 = st.columns(4)
        bt = c1.text_input("Ticker", value="AAPL", key="pro_bt").upper()
        yrs = c2.selectbox("History", [1, 3, 5, 10], index=3)
        tp_ = c3.number_input("Target %", min_value=1, max_value=50, value=10, key="pro_tp")
        hz = c4.number_input("Horizon (days)", min_value=5, max_value=252, value=60, key="pro_hz")
        if st.button("📊 Run Backtest", use_container_width=True, key="pro_backtest"):
            with st.spinner(f"Backtesting {bt} ({yrs}y)..."):
                df = load_data(bt, period=f"{yrs}y")
                if df is None or len(df) < 100:
                    st.error("Insufficient data")
                else:
                    res = run_backtest(df, target_pct=tp_, horizon=hz)
                    if res is None:
                        st.warning("No signals found")
                    else:
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Signals", res['n_trades'])
                        c2.metric("Win Rate", f"{res['win_rate']:.1f}%",
                                  f"{res['win_rate']-res['baseline_win_rate']:+.1f}pp vs random")
                        c3.metric("Avg Return", f"{res['avg_return']:+.2f}%")
                        c4.metric("Baseline", f"{res['baseline_win_rate']:.1f}%")
                        ew = res['win_rate']-res['baseline_win_rate']
                        er = res['avg_return']-res['baseline_avg']
                        if ew > 5 and er > 1:
                            st.success("✅ Positive edge")
                        elif ew > 0:
                            st.warning("🟡 Marginal edge")
                        else:
                            st.error("❌ No edge detected")

    # ════════════════════════════════════════════════════
    # TAB 3 — PORTFOLIO
    # ════════════════════════════════════════════════════
    with tab3:
        portfolio_tab_pro()

    st.markdown("---")
    st.caption("⚠️ Educational tool only. Not financial advice. Estimates and backtests do not guarantee future results.")
