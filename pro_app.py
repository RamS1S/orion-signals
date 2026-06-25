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
    ema, obv, climax_volume, relative_strength,
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
            "tgt_low":  tp["target_1"] if tp else None,
            "tgt_high": tp["target_2"] if tp else None,
            "tgt_pct_low":  tp["pct_t1"] if tp else None,
            "tgt_pct_high": tp["pct_t2"] if tp else None,
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
