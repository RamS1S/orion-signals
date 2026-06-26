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
    screen_ticker, screen_ticker_v2, run_backtest,
    get_dow, get_nasdaq100, get_sp500, get_sp400, get_sp600, get_russell2000,
    get_universe, get_market_regime,
    atr_calc, fuel_gauge, fuel_bar, confirmation_entry,
    check_earnings, target_projection,
    ema, obv, climax_volume, relative_strength,
    short_setup, bearish_fuel_gauge,
    get_fundamentals, vfm_score, pre_breakout_detection,
    scan_pre_breakouts,
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
    tickers = get_universe(universe)
    results = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(screen_ticker_v2, t): t for t in tickers}
        for f in as_completed(futures):
            r = f.result()
            if r:
                results.append(r)

    results.sort(key=lambda x: x["combined"], reverse=True)
    buys = [r for r in results if r["verdict"] in ("BUY", "STRONG BUY") and r["combined"] >= min_score]
    sells = sorted([r for r in results if r["verdict"] in ("SELL", "STRONG SELL")], key=lambda x: x["combined"])[:top_n]
    pool = buys if buys else [r for r in results if r["verdict"] not in ("SELL","STRONG SELL")][:top_n]
    top = pool[:top_n]

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
            "fuel": fg["fuel"] if fg else None,
            "fuel_status": fg["status"] if fg else None,
            "entry": entry, "sl": sl, "target": tgt, "rr": rr,
            "tgt_low": tp["target_1"] if tp else None,
            "tgt_high": tp["target_2"] if tp else None,
            "tgt_pct_low": tp["pct_t1"] if tp else None,
            "tgt_pct_high": tp["pct_t2"] if tp else None,
        })
    return {"buys": enriched, "sells": sells}


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


def render_sell_card(p, idx):
    """Card για SELL/STRONG SELL signals."""
    verdict_color = "#FF3D57" if "STRONG" in p["verdict"] else "#FF8A95"
    ticker    = p["ticker"]
    price     = p["price"]
    combined  = p["combined"]
    rsi_val   = p["rsi"]
    ret_1m    = p["ret_1m"]
    ret_3m    = p["ret_3m"]
    verdict   = p["verdict"]
    above_ma200 = p.get("above_ma200", False)
    sector    = p.get("sector", "")
    ma200_txt = "MA200 ✅" if above_ma200 else "MA200 ❌"
    sector_part = f" · {sector}" if sector and sector != "Unknown" else ""

    line1 = f'<div style="background:rgba(255,61,87,0.04);border:1px solid rgba(255,61,87,0.25);border-radius:12px;padding:0.85rem 1rem;margin-bottom:0.4rem;">'
    line2 = f'<div style="display:flex;justify-content:space-between;align-items:center;"><span style="font-family:Syne,sans-serif;font-size:1.1rem;font-weight:800;color:#fff;">{ticker}</span><span style="font-size:0.7rem;font-weight:700;color:{verdict_color};">{verdict}</span></div>'
    line3 = f'<div style="font-size:0.85rem;color:rgba(255,255,255,0.7);margin:0.2rem 0;">${price:.2f} · Score <strong style="color:{verdict_color}">{combined:+.0f}</strong><span style="color:rgba(255,255,255,0.4);font-size:0.68rem">{sector_part}</span></div>'
    line4 = f'<div style="font-size:0.72rem;color:rgba(255,255,255,0.45);margin-top:0.3rem;">RSI {rsi_val:.0f} · 1M {ret_1m:+.1f}% · 3M {ret_3m:+.1f}% · {ma200_txt}</div>'
    line5 = '<div style="font-size:0.68rem;color:rgba(255,61,87,0.6);margin-top:0.3rem;">⚠️ Avoid / Exit if holding</div></div>'

    st.markdown(line1 + line2 + line3 + line4 + line5, unsafe_allow_html=True)

    if st.button(f"🔍 Analyze {ticker}", key=f"sell_analyze_{idx}", use_container_width=True):
        st.session_state.pro_picked = ticker
        st.session_state.pro_last_scanned = ticker
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

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["⚡ Today's Picks", "🔍 Single Stock", "👀 Watchlist", "🎯 Screener", "📊 Backtest", "💼 Portfolio"])

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

            uni = st.selectbox("Universe",
                               ["dow","nasdaq100","sp500","sp400","sp600","russell2000"],
                               format_func=lambda x: {
                                   "dow":"Dow 30 (γρήγορο)","nasdaq100":"NASDAQ 100",
                                   "sp500":"S&P 500","sp400":"S&P 400 Mid Cap",
                                   "sp600":"S&P 600 Small Cap","russell2000":"Russell 2000",
                               }[x],
                               key="picks_universe", label_visibility="collapsed")
            sector_filter = st.selectbox("Sector",
                               ["All Sectors","Technology","Healthcare","Financials",
                                "Consumer Discretionary","Consumer Staples","Energy",
                                "Industrials","Materials","Real Estate","Utilities",
                                "Communication Services"],
                               key="sector_filter", label_visibility="collapsed")

            if st.button("🔄 Refresh scan", key="refresh_picks", use_container_width=True):
                scan_todays_picks.clear()
                st.rerun()

            with st.spinner("Scanning the market..."):
                picks = scan_todays_picks(universe=uni)

            if not picks:
                st.info("Scanning returned nothing — rate-limited. Press Refresh.")
            else:
                buys  = picks.get("buys", [])
                sells = picks.get("sells", [])

                # Sector filter
                if sector_filter != "All Sectors":
                    buys  = [p for p in buys  if p.get("sector") == sector_filter]
                    sells = [p for p in sells if p.get("sector") == sector_filter]

                # Market Regime
                regime = get_market_regime()
                rc = {"bull":"#00C853","bear":"#FF3D57","neutral":"#F59E0B"}[regime["regime"]]
                ri = {"bull":"🟢","bear":"🔴","neutral":"🟡"}[regime["regime"]]
                st.markdown(
                    f'<div style="background:rgba(255,255,255,0.03);border:1px solid {rc}44;' +
                    f'border-radius:8px;padding:0.5rem 0.8rem;margin-bottom:0.8rem;font-size:0.78rem;">' +
                    f'{ri} Market: <strong style="color:{rc}">{regime["regime"].upper()}</strong>' +
                    f' · SPY {"✅" if regime["spy_ok"] else "❌"}' +
                    f' · VIX {regime["vix_level"]:.0f} {"✅" if regime["vix_ok"] else "⚠️"}</div>',
                    unsafe_allow_html=True
                )

                # BUY section
                if buys:
                    st.markdown(f"**🟢 BUY signals ({len(buys)})**")
                    for i, p in enumerate(buys):
                        render_pick_card(p, i)
                else:
                    st.info("Δεν βρέθηκαν BUY signals.")

                # SELL section
                if sells:
                    st.markdown(f"**🔴 SELL / AVOID ({len(sells)})**")
                    for i, p in enumerate(sells):
                        render_sell_card(p, i)

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

                    is_bullish = a['verdict'] in ("BUY", "STRONG BUY")

                    # Fuel gauge — ΜΟΝΟ σε bullish setup (μετράει ανοδική εξάντληση)
                    if is_bullish:
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
                                    Status: {fg['status']} — {'healthy momentum, room to run' if fg['status']=='healthy' else 'losing steam, watch closely' if fg['status']=='slowing' else 'exhausted, reversal risk'}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            triggered = [t for t, tr in fg["signals"] if tr]
                            if triggered:
                                st.caption("⚠️ Exhaustion signals: " + " · ".join(triggered))
                    else:
                        st.markdown(f"""
                        <div style="background:rgba(255,61,87,0.05);border:1px solid rgba(255,61,87,0.2);
                                    border-radius:10px;padding:0.85rem 1rem;margin:0.75rem 0;font-size:0.82rem;color:rgba(255,255,255,0.6);">
                            🔋 <strong style="color:#FF8A95;">Fuel Gauge n/a</strong> —
                            this is a <strong>{a['verdict']}</strong> setup. The fuel gauge measures
                            upward momentum exhaustion and only applies to bullish (BUY) signals.
                        </div>
                        """, unsafe_allow_html=True)

                    # ATR levels + target — ΜΟΝΟ σε bullish
                    atr_v = float(atr_calc(df).iloc[-1])
                    entry = a['current'] * 1.015
                    sl = entry - 1.5 * atr_v
                    tgt = entry + 3 * atr_v
                    rr = (tgt - entry) / (entry - sl) if (entry - sl) > 0 else 0

                    if is_bullish:
                        p1, p2, p3, p4 = st.columns(4)
                        p1.metric("Entry (+1.5%)", f"${entry:.2f}")
                        p2.metric("Stop Loss", f"${sl:.2f}")
                        p3.metric("Target", f"${tgt:.2f}")
                        p4.metric("Risk/Reward", f"1:{rr:.1f}")

                        tp = target_projection(df)
                        if tp:
                            st.markdown(f"""
                            <div style="background:rgba(0,200,83,0.05);border:1px solid rgba(0,200,83,0.2);
                                        border-radius:10px;padding:0.7rem 1rem;margin:0.5rem 0;font-size:0.82rem;">
                                🎯 <strong style="color:#00C853;">Est. target ${tp['target_1']:.2f}–${tp['target_2']:.2f}</strong>
                                <span style="color:rgba(255,255,255,0.5);">({tp['pct_t1']:+.1f}% to {tp['pct_t2']:+.1f}%)</span><br>
                                <span style="font-size:0.7rem;color:rgba(255,255,255,0.35);">Estimate — not a guarantee. Based on ATR, resistance & volatility.</span>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        # SHORT SETUP για SELL/STRONG SELL
                        if a['verdict'] in ("SELL", "STRONG SELL"):
                            ss = short_setup(df)
                            bf = bearish_fuel_gauge(df)
                            if ss:
                                st.markdown("""
                                <div style="background:rgba(255,61,87,0.05);border:1px solid rgba(255,61,87,0.25);
                                    border-radius:10px;padding:0.85rem 1rem;margin:0.75rem 0;">
                                    <div style="font-family:Syne,sans-serif;font-weight:700;color:#FF3D57;margin-bottom:0.5rem;">
                                        🔻 Short Setup
                                    </div>
                                    <div style="font-size:0.7rem;color:rgba(255,100,100,0.6);margin-bottom:0.5rem;">
                                        ⚠️ Short selling involves unlimited risk. Only for experienced traders with margin accounts.
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                p1, p2, p3, p4 = st.columns(4)
                                p1.metric("Short Entry", f"${ss['entry']:.2f}")
                                p2.metric("Stop Loss 🛑", f"${ss['stop_loss']:.2f}",
                                          f"{ss['pct_sl']:+.1f}%", delta_color="inverse")
                                p3.metric("Target 🎯", f"${ss['target_1']:.2f}",
                                          f"{ss['pct_t1']:+.1f}%")
                                p4.metric("R/R Ratio", f"1:{ss['rr_ratio']:.1f}")
                                st.caption(f"Target 2 (3:1): ${ss['target_2']:.2f} ({ss['pct_t2']:+.1f}%)")

                            if bf:
                                fcol = ("#FF3D57" if bf["fuel"] >= 65 else
                                        "#F59E0B" if bf["fuel"] >= 35 else "#00C853")
                                status_txt = {
                                    "strong": "Downtrend has momentum — room to fall",
                                    "weakening": "Sell pressure weakening — watch for bounce",
                                    "exhausted": "⚠️ Downtrend exhausted — possible reversal"
                                }.get(bf["status"], "")
                                filled = round(bf["fuel"] / 10)
                                bar = "█" * filled + "░" * (10 - filled)
                                st.markdown(
                                    f'<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,61,87,0.2);' +
                                    f'border-radius:10px;padding:0.85rem 1rem;margin:0.5rem 0;">' +
                                    f'<div style="display:flex;justify-content:space-between;">' +
                                    f'<span style="font-family:Syne;font-weight:700;color:#fff;">🔋 Bearish Fuel</span>' +
                                    f'<span style="color:{fcol};font-weight:800;font-size:1.1rem;">{bf["fuel"]}%</span></div>' +
                                    f'<div style="font-family:monospace;font-size:1.1rem;color:{fcol};letter-spacing:-1px;margin:0.3rem 0;">{bar}</div>' +
                                    f'<div style="font-size:0.75rem;color:rgba(255,255,255,0.5);">{status_txt}</div></div>',
                                    unsafe_allow_html=True
                                )
                                triggered = [t for t, tr in bf["signals"] if tr]
                                if triggered:
                                    st.caption("⚠️ Reversal warnings: " + " · ".join(triggered))
                        else:
                            st.info(f"📉 {a['verdict']} setup — entry levels shown only for BUY/SELL signals.")

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

                    # ── EXTRA INDICATORS (expandable) ──
                    with st.expander("📐 Extra indicators (EMA · OBV · Climax · Relative Strength)"):
                        e9  = float(ema(df['Close'], 9).iloc[-1])
                        e21 = float(ema(df['Close'], 21).iloc[-1])
                        cur = a['current']
                        ec1, ec2, ec3 = st.columns(3)
                        ec1.metric("EMA 9", f"${e9:.2f}",
                                   "above" if cur > e9 else "below")
                        ec2.metric("EMA 21", f"${e21:.2f}",
                                   "above" if cur > e21 else "below")
                        ema_cross = "🟢 EMA9 > EMA21 (bullish)" if e9 > e21 else "🔴 EMA9 < EMA21 (bearish)"
                        ec3.markdown(f"**Cross**\n\n{ema_cross}")

                        # OBV trend
                        o = obv(df)
                        obv_rising = float(o.iloc[-1]) > float(o.iloc[-20]) if len(o) >= 20 else None
                        # Climax volume
                        cv = climax_volume(df)
                        # Relative Strength vs SPY
                        spy = load_data("SPY", "6mo")
                        rs = relative_strength(df, spy) if spy is not None else None

                        st.markdown("---")
                        oc1, oc2 = st.columns(2)
                        with oc1:
                            if obv_rising is not None:
                                st.markdown(f"**OBV (volume flow):** "
                                            f"{'🟢 rising — buyers in control' if obv_rising else '🔴 falling — sellers in control'}")
                            if cv["detected"]:
                                ct = "⚠️ Buying climax (possible top)" if cv["type"] == "buying_climax" else "⚠️ Selling climax (possible bottom)"
                                st.markdown(f"**Climax volume:** {ct} — {cv['ratio']:.1f}x avg")
                            else:
                                st.markdown(f"**Climax volume:** none ({cv['ratio']:.1f}x avg)")
                        with oc2:
                            if rs:
                                rs_txt = ("🟢 Outperforming SPY" if rs["outperform"] else "🔴 Lagging SPY")
                                st.markdown(f"**Relative Strength:** {rs_txt}")
                                st.caption(f"Stock {rs['stock_ret']:+.1f}% vs SPY {rs['bench_ret']:+.1f}% (3mo) · RS ratio {rs['rs_ratio']:.2f}")
                            else:
                                st.caption("Relative Strength unavailable")

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
    # TAB 2 — SINGLE STOCK ANALYSIS
    # ════════════════════════════════════════════════════
    with tab2:
        st.markdown("#### 🔍 Single Stock Analysis")
        c1, c2 = st.columns([1, 3])
        with c1:
            pro_ticker = st.text_input("Ticker", value="AAPL", key="pro_single_ticker").upper()
            pro_period = st.selectbox("Period", ["6mo", "1y", "2y", "5y", "10y"], index=1, key="pro_single_period")
            analyze_btn = st.button("Analyze →", use_container_width=True, key="pro_analyze")

        if analyze_btn or pro_ticker:
            with st.spinner(f"Analyzing {pro_ticker}..."):
                df = load_data(pro_ticker, pro_period)
            if df is None:
                st.error(f"No data for {pro_ticker}")
            else:
                a = full_analysis(df, include_extras=True)
                vfm = vfm_score(df, a)
                fund = get_fundamentals(pro_ticker)
                earnings = check_earnings(pro_ticker)
                tp = target_projection(df)
                fg = fuel_gauge(df)

                # Verdict banner
                vc = {"STRONG BUY":"verdict-strong-buy","BUY":"verdict-buy",
                      "STRONG SELL":"verdict-sell","SELL":"verdict-sell"}.get(a['verdict'],"verdict-neutral")
                ico = {"STRONG BUY":"🟢","BUY":"🟢","STRONG SELL":"🔴","SELL":"🔴","MIXED SIGNALS":"🟡"}.get(a['verdict'],"⚪")
                st.markdown(f'<div class="verdict-banner {vc}">{ico} {a["verdict"]} — {pro_ticker}</div>', unsafe_allow_html=True)

                # Metrics row
                m1,m2,m3,m4,m5 = st.columns(5)
                m1.metric("Price", f"${a['current']:.2f}")
                m2.metric("Score", f"{a['combined']:+.1f}")
                m3.metric("Momentum", f"{a['mom_score']:+.1f}")
                m4.metric("Technical", f"{a['tech_score']:+.1f}")
                m5.metric("Fuel", f"{fg['fuel']}%" if fg else "N/A")

                # VFM Score
                if vfm:
                    vfm_colors = {'excellent':'#00C853','good':'#69F0AE','fair':'#F59E0B','late':'#FF8A65','avoid':'#FF3D57'}
                    vfm_color = vfm_colors.get(vfm['vfm_rating'], '#fff')
                    st.markdown(
                        f'<div style="background:rgba(255,255,255,0.03);border:1px solid {vfm_color}44;' +
                        f'border-radius:10px;padding:0.85rem 1rem;margin:0.5rem 0;">' +
                        f'<div style="display:flex;justify-content:space-between;align-items:center;">' +
                        f'<span style="font-family:Syne;font-weight:700;color:#fff;">💰 VFM Entry Score</span>' +
                        f'<span style="color:{vfm_color};font-weight:800;font-size:1.1rem;">{vfm["vfm_rating"].upper()} — {vfm["vfm_pct"]:.0f}% into tunnel</span></div>' +
                        f'<div style="font-size:0.78rem;color:rgba(255,255,255,0.5);margin-top:0.3rem;">' +
                        f'Support: ${vfm["support"]:.2f} → Resistance: ${vfm["resistance"]:.2f} · ' +
                        f'Pullback: {vfm["pullback_pct"]:.1f}% {"✅" if vfm["has_pullback"] else "❌"} · ' +
                        f'Near MA50: {"✅" if vfm["near_ma50"] else "❌"}</div></div>',
                        unsafe_allow_html=True
                    )

                # Earnings warning
                if earnings and earnings['has_earnings']:
                    st.warning(f"⚠️ {earnings['message']}")

                # Entry/SL/Target
                if tp and a['verdict'] in ('BUY', 'STRONG BUY'):
                    p1,p2,p3,p4 = st.columns(4)
                    p1.metric("Entry", f"${tp['entry']:.2f}")
                    p2.metric("Stop Loss 🛑", f"${tp['stop_loss']:.2f}", f"{tp['pct_sl']:+.1f}%", delta_color="inverse")
                    p3.metric("Target 1 🎯", f"${tp['target_1']:.2f}", f"{tp['pct_t1']:+.1f}%")
                    p4.metric("R/R", f"1:{tp['rr_ratio']:.1f}")
                    st.caption(f"Target 2 (3:1): ${tp['target_2']:.2f} ({tp['pct_t2']:+.1f}%)")

                # Fundamentals
                if fund:
                    st.markdown("#### 📊 Fundamentals")
                    f1,f2,f3,f4 = st.columns(4)
                    f1.metric("P/E", f"{fund['pe']}" if fund['pe'] else "N/A")
                    f2.metric("EPS Growth", f"{fund['eps_growth']}%" if fund['eps_growth'] else "N/A")
                    f3.metric("Rev Growth", f"{fund['rev_growth']}%" if fund['rev_growth'] else "N/A")
                    f4.metric("Short Float", f"{fund['short_float']}%" if fund['short_float'] else "N/A")
                    f5,f6,f7,f8 = st.columns(4)
                    f5.metric("Debt/Equity", f"{fund['debt_equity']}" if fund['debt_equity'] else "N/A")
                    f6.metric("Profit Margin", f"{fund['profit_margin']}%" if fund['profit_margin'] else "N/A")
                    f7.metric("Market Cap", f"${fund['market_cap']}B" if fund['market_cap'] else "N/A")
                    f8.metric("Beta", f"{fund['beta']}" if fund['beta'] else "N/A")
                    if fund['flags']:
                        for flag in fund['flags']:
                            st.caption(flag)

                # Chart
                st.plotly_chart(create_chart(df, a, show_vwap=True, show_ema21=True), use_container_width=True)

                # Signals
                st.markdown("#### Signals")
                s1,s2 = st.columns(2)
                for i,(text,d) in enumerate(a['signals']):
                    ic = {"bullish":"🟢","bearish":"🔴","neutral":"⚪"}[d]
                    (s1 if i%2==0 else s2).write(f"{ic} {text}")

    # ════════════════════════════════════════════════════
    # TAB 3 — WATCHLIST (Pre-breakout)
    # ════════════════════════════════════════════════════
    with tab3:
        st.markdown("#### 👀 Watchlist — Pre-Breakout Setups")
        st.caption("Μετοχές που 'φορτίζουν' πριν από μεγάλη κίνηση. Δεν κινούνται ακόμα — αλλά ετοιμάζονται.")

        wc1,wc2 = st.columns(2)
        wb_universe = wc1.selectbox("Universe",
            ["dow","nasdaq100","sp500","sp400","sp600","russell2000"],
            format_func=lambda x: {"dow":"Dow 30","nasdaq100":"NASDAQ 100","sp500":"S&P 500",
                                   "sp400":"S&P 400 Mid Cap","sp600":"S&P 600 Small Cap","russell2000":"Russell 2000"}[x],
            key="wb_universe")
        wb_top = wc2.number_input("Top N", min_value=5, max_value=50, value=15, key="wb_top")

        if st.button("🔍 Scan for Breakouts", use_container_width=True, key="wb_scan"):
            with st.spinner(f"Scanning {wb_universe} for pre-breakout setups..."):
                wb_results = scan_pre_breakouts(universe=wb_universe, top_n=wb_top)

            if not wb_results:
                st.info("No pre-breakout setups found. Try a different universe.")
            else:
                ready = [r for r in wb_results if r['status'] == 'ready']
                building = [r for r in wb_results if r['status'] == 'building']
                early = [r for r in wb_results if r['status'] == 'early']

                for section, items, color, icon in [
                    ("🚀 Ready to Break Out", ready, "#00C853", "ready"),
                    ("🔋 Building Energy", building, "#F59E0B", "building"),
                    ("⏳ Early Stage", early, "#A78BFA", "early"),
                ]:
                    if items:
                        st.markdown(f"**{section} ({len(items)})**")
                        for r in items:
                            sigs = " · ".join(r['signals'][:2])
                            st.markdown(
                                f'<div style="background:rgba(255,255,255,0.02);border:1px solid {color}33;' +
                                f'border-radius:10px;padding:0.7rem 1rem;margin:0.3rem 0;display:flex;justify-content:space-between;">' +
                                f'<div><span style="font-family:Syne;font-weight:800;font-size:1rem;color:#fff;">{r["ticker"]}</span>' +
                                f' <span style="color:rgba(255,255,255,0.4);font-size:0.75rem;">${r["price"]:.2f}</span>' +
                                f'<div style="font-size:0.72rem;color:rgba(255,255,255,0.5);margin-top:0.2rem;">{sigs}</div>' +
                                f'<div style="font-size:0.68rem;color:rgba(255,255,255,0.35);">Resistance: ${r["resistance"]:.2f} ({r["dist_res"]:.1f}% away) · ' +
                                f'MA50: {"✅" if r["above_ma50"] else "❌"} · MA200: {"✅" if r["above_ma200"] else "❌"}</div></div>' +
                                f'<div style="text-align:right;"><span style="color:{color};font-weight:800;font-size:1.2rem;">{r["pb_score"]}</span>' +
                                f'<div style="font-size:0.65rem;color:rgba(255,255,255,0.3);">score</div></div></div>',
                                unsafe_allow_html=True
                            )
                            if st.button(f"Analyze {r['ticker']}", key=f"wb_{r['ticker']}", use_container_width=False):
                                st.session_state.pro_picked = r['ticker']
                                st.rerun()

    # ════════════════════════════════════════════════════
    # TAB 4 — SCREENER
    # ════════════════════════════════════════════════════
    with tab4:
        st.markdown("#### 🎯 Stock Screener")
        sc1,sc2,sc3 = st.columns(3)
        sc_universe = sc1.selectbox("Universe",
            ["dow","nasdaq100","sp500","sp400","sp600","russell2000"],
            format_func=lambda x: {"dow":"Dow 30","nasdaq100":"NASDAQ 100","sp500":"S&P 500",
                                   "sp400":"S&P 400","sp600":"S&P 600","russell2000":"Russell 2000"}[x],
            key="sc_universe")
        sc_filter = sc2.selectbox("Show",
            ["All signals","BUY only","SELL only"],
            key="sc_filter")
        sc_sector = sc3.selectbox("Sector",
            ["All Sectors","Technology","Healthcare","Financials","Consumer Discretionary",
             "Consumer Staples","Energy","Industrials","Materials","Real Estate",
             "Utilities","Communication Services"],
            key="sc_sector")
        if st.button("🚀 Run Screener", use_container_width=True, key="sc_run"):
            tickers = get_universe(sc_universe)
            st.info(f"Scanning {len(tickers)} stocks...")
            prog = st.progress(0)
            sc_results = []
            with ThreadPoolExecutor(max_workers=10) as ex:
                futures = {ex.submit(screen_ticker_v2, t): t for t in tickers}
                done = 0
                for fut in as_completed(futures):
                    done += 1
                    r = fut.result()
                    if r: sc_results.append(r)
                    prog.progress(done/len(tickers))
            prog.empty()
            if sc_results:
                sc_df = pd.DataFrame(sc_results)
                if sc_filter == "BUY only":
                    sc_df = sc_df[sc_df['verdict'].isin(['BUY','STRONG BUY'])]
                elif sc_filter == "SELL only":
                    sc_df = sc_df[sc_df['verdict'].isin(['SELL','STRONG SELL'])]
                sc_df = sc_df.sort_values('combined', ascending=False)
                buys_sc = sc_df[sc_df['verdict'].isin(['BUY','STRONG BUY'])]
                sells_sc = sc_df[sc_df['verdict'].isin(['SELL','STRONG SELL'])]
                if not buys_sc.empty:
                    st.markdown(f"**🟢 BUY signals ({len(buys_sc)})**")
                    dd = buys_sc[['ticker','price','verdict','combined','rsi','ret_1m','ret_3m','above_ma200']].copy()
                    dd.columns = ['Ticker','Price','Verdict','Score','RSI','1M%','3M%','MA200']
                    st.dataframe(dd, use_container_width=True, hide_index=True)
                if not sells_sc.empty:
                    st.markdown(f"**🔴 SELL / AVOID ({len(sells_sc)})**")
                    dd2 = sells_sc[['ticker','price','verdict','combined','rsi','ret_1m','ret_3m','above_ma200']].copy()
                    dd2.columns = ['Ticker','Price','Verdict','Score','RSI','1M%','3M%','MA200']
                    st.dataframe(dd2, use_container_width=True, hide_index=True)
            else:
                st.warning("No results found.")

    # ════════════════════════════════════════════════════
    # TAB 5 — BACKTEST
    # ════════════════════════════════════════════════════
    with tab5:
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

