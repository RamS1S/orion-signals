"""
Orion Signals — Pro Dashboard
-------------------------------
Pro περιβάλλον — όλα τα features.
"""

import streamlit as st
from entry_app import (inject_css, load_data, get_sp500, get_nasdaq100, get_dow,
                        full_analysis, create_chart, screen_ticker, run_backtest,
                        rsi, macd, bollinger, adx_calc)
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np
import yfinance as yf


def show_pro_dashboard(user):
    inject_css()

    # Pro badge styling
    st.markdown("""
    <style>
    .pro-badge {
        background: rgba(124,58,237,0.2);
        color: #A78BFA;
        border: 1px solid rgba(124,58,237,0.4);
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .pro-feature {
        background: rgba(124,58,237,0.05);
        border: 1px solid rgba(124,58,237,0.2);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        font-size: 0.85rem;
        color: rgba(255,255,255,0.7);
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown(f"""
    <div class="orion-header">
        <div class="orion-logo">🎯 Orion <span>Signals</span></div>
        <span class="pro-badge">⚡ Pro Plan</span>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown(f"**👤 {user['name']}**")
        st.markdown(f"*{user['email']}*")
        st.markdown("---")
        st.markdown("**⚙️ Pro Settings**")
        show_earnings = st.toggle("Earnings Filter", value=True)
        show_atr = st.toggle("ATR / SL / Target", value=True)
        show_stoch = st.toggle("Stochastic", value=True)
        st.markdown("---")
        if st.button("🚪 Logout", key="pro_logout"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

    # Tabs — Pro έχει extra tab
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Single Stock", "🎯 Screener", "📊 Backtest", "💼 Portfolio"])

    # ── TAB 1: SINGLE STOCK (Pro version) ──
    with tab1:
        col1, col2 = st.columns([1, 3])
        with col1:
            ticker = st.text_input("Ticker", value="AAPL").upper()
            period = st.selectbox("Period", ["6mo", "1y", "2y", "5y"], index=1)
            analyze_btn = st.button("Analyze →", use_container_width=True)

        if analyze_btn or ticker:
            with st.spinner(f"Analyzing {ticker}..."):
                df = load_data(ticker, period)

            if df is None:
                st.error(f"Δεν βρέθηκαν δεδομένα για {ticker}")
            else:
                a = full_analysis(df)

                verdict_class = {
                    "STRONG BUY": "verdict-strong-buy",
                    "BUY": "verdict-buy",
                    "STRONG SELL": "verdict-sell",
                    "SELL": "verdict-sell",
                }.get(a['verdict'], "verdict-neutral")

                icon = {"STRONG BUY": "🟢", "BUY": "🟢", "STRONG SELL": "🔴",
                        "SELL": "🔴", "MIXED SIGNALS": "🟡"}.get(a['verdict'], "⚪")

                st.markdown(f"""
                <div class="verdict-banner {verdict_class}">
                    {icon} {a['verdict']} — {ticker}
                </div>
                """, unsafe_allow_html=True)

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Price", f"${a['current']:.2f}")
                c2.metric("Combined", f"{a['combined']:+.1f}")
                c3.metric("Momentum", f"{a['mom_score']:+.1f}")
                c4.metric("Technical", f"{a['tech_score']:+.1f}")
                c5.metric("Agreement", "✅ YES" if a['agreement'] else "⚠️ NO")

                # Pro extra — ATR / SL / Target
                if show_atr:
                    close = df['Close']
                    high = df['High']
                    low = df['Low']
                    tr = pd.concat([
                        high - low,
                        (high - close.shift()).abs(),
                        (low - close.shift()).abs()
                    ], axis=1).max(axis=1)
                    atr = tr.rolling(14).mean().iloc[-1]
                    entry = a['current'] * 1.015
                    sl = entry - (1.5 * atr)
                    target = entry + (3 * atr)
                    rr = (target - entry) / (entry - sl)

                    st.markdown("#### ⚡ Pro — Entry / Stop Loss / Target")
                    p1, p2, p3, p4 = st.columns(4)
                    p1.metric("Entry (confirm +1.5%)", f"${entry:.2f}")
                    p2.metric("Stop Loss", f"${sl:.2f}", f"{((sl-entry)/entry*100):.1f}%")
                    p3.metric("Target", f"${target:.2f}", f"{((target-entry)/entry*100):.1f}%")
                    p4.metric("Risk/Reward", f"1:{rr:.1f}")

                st.markdown("#### Returns")
                rcols = st.columns(len(a['returns']))
                for col, (tf, ret) in zip(rcols, a['returns'].items()):
                    col.metric(tf, f"{ret:+.2f}%")

                st.plotly_chart(create_chart(df, a), use_container_width=True)

                st.markdown("#### Signals")
                s1, s2 = st.columns(2)
                for i, (text, direction) in enumerate(a['signals']):
                    icon2 = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}[direction]
                    target2 = s1 if i % 2 == 0 else s2
                    target2.write(f"{icon2} {text}")

    # ── TAB 2: SCREENER (Pro — S&P500, top 30) ──
    with tab2:
        st.markdown("Σαρώνει universe μετοχών και βρίσκει τις πιο bullish.")
        col1, col2, col3 = st.columns(3)
        universe = col1.selectbox("Universe", ["dow", "nasdaq100", "sp500"],
                                   format_func=lambda x: {"dow": "Dow 30 (γρήγορο)",
                                                           "nasdaq100": "NASDAQ 100",
                                                           "sp500": "S&P 500 (αργό)"}[x])
        top_n = col2.number_input("Top N", min_value=5, max_value=50, value=20)
        min_score = col3.number_input("Min Score", min_value=-100, max_value=100, value=20)

        if show_earnings:
            st.info("🔔 Earnings Filter: ON — μετοχές με earnings αποκλείονται")

        if st.button("🚀 Run Screener", use_container_width=True):
            tickers = get_sp500() if universe == "sp500" else \
                      get_nasdaq100() if universe == "nasdaq100" else get_dow()

            st.info(f"Σαρώνω {len(tickers)} μετοχές...")
            progress = st.progress(0)
            results = []

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(screen_ticker, t): t for t in tickers}
                done = 0
                for future in as_completed(futures):
                    done += 1
                    result = future.result()
                    if result: results.append(result)
                    progress.progress(done / len(tickers))

            progress.empty()

            if results:
                df_r = pd.DataFrame(results)
                df_f = df_r[df_r['combined'] >= min_score].sort_values('combined', ascending=False).head(top_n)

                if df_f.empty:
                    st.warning(f"Καμία μετοχή με score >= {min_score}")
                else:
                    df_display = df_f.copy()
                    df_display['price'] = df_display['price'].apply(lambda x: f"${x:.2f}")
                    df_display['combined'] = df_display['combined'].apply(lambda x: f"{x:+.1f}")
                    df_display['ret_1m'] = df_display['ret_1m'].apply(lambda x: f"{x:+.1f}%")
                    df_display['ret_3m'] = df_display['ret_3m'].apply(lambda x: f"{x:+.1f}%")
                    df_display['macd_cross'] = df_display['macd_cross'].apply(lambda x: "🔔" if x else "")
                    df_display['above_ma200'] = df_display['above_ma200'].apply(lambda x: "✓" if x else "")
                    df_display = df_display[['ticker','price','verdict','combined','rsi','ret_1m','ret_3m','macd_cross','above_ma200']]
                    df_display.columns = ['Ticker','Price','Verdict','Score','RSI','1M%','3M%','MACD↑','MA200']
                    st.dataframe(df_display, use_container_width=True, hide_index=True)

                    csv = df_f.to_csv(index=False)
                    st.download_button("📥 Download CSV", csv, "pro_signals.csv", "text/csv")

    # ── TAB 3: BACKTEST (Pro — 10 χρόνια) ──
    with tab3:
        st.markdown("Δοκίμασε αν η στρατηγική έχει edge πάνω από random entry.")
        st.success("⚡ Pro: έως 10 χρόνια ιστορικό")

        col1, col2, col3, col4 = st.columns(4)
        bt_ticker = col1.text_input("Ticker", value="AAPL", key="bt").upper()
        bt_years = col2.selectbox("History", [1, 3, 5, 10], index=3)
        bt_target = col3.number_input("Target %", min_value=1, max_value=50, value=10)
        bt_horizon = col4.number_input("Horizon (days)", min_value=5, max_value=252, value=60)

        if st.button("📊 Run Backtest", use_container_width=True):
            with st.spinner(f"Backtesting {bt_ticker} ({bt_years}y)..."):
                df = load_data(bt_ticker, period=f"{bt_years}y")
                if df is None or len(df) < 300:
                    st.error("Ανεπαρκή δεδομένα")
                else:
                    result = run_backtest(df, target_pct=bt_target, horizon=bt_horizon)
                    if result is None:
                        st.warning("Δεν εμφανίστηκαν σήματα στο διάστημα")
                    else:
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Signals", result['n_trades'])
                        c2.metric("Win Rate", f"{result['win_rate']:.1f}%",
                                  f"{result['win_rate'] - result['baseline_win_rate']:+.1f}pp vs random")
                        c3.metric("Avg Return", f"{result['avg_return']:+.2f}%")
                        c4.metric("Baseline", f"{result['baseline_win_rate']:.1f}%")

                        edge_wr = result['win_rate'] - result['baseline_win_rate']
                        edge_ret = result['avg_return'] - result['baseline_avg']

                        if edge_wr > 5 and edge_ret > 1:
                            st.success("✅ Η στρατηγική έχει θετικό edge")
                        elif edge_wr > 0:
                            st.warning("🟡 Οριακό edge")
                        else:
                            st.error("❌ Δεν υπάρχει edge")

    # ── TAB 4: PORTFOLIO TRACKER ──
    with tab4:
        st.markdown("#### 💼 Portfolio Tracker")
        st.info("Καταγραφή ανοιχτών θέσεων — coming soon στην επόμενη έκδοση!")

        st.markdown("""
        <div class="pro-feature">
            ✅ Προσθήκη θέσης (ticker, entry price, shares)<br>
            ✅ Real-time P&L<br>
            ✅ Stop Loss / Target alerts<br>
            ✅ "Πούλησα" button — ελευθερώνει τη θέση<br>
            ✅ Ιστορικό trades
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("⚠️ Educational tool only. Not financial advice.")
