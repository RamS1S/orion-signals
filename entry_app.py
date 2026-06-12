"""
Orion Signals — Entry Dashboard
📈 Stocks Entry €29/μήνα
"""
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import streamlit as st
import yfinance as yf

from indicators import (
    inject_css, load_data, full_analysis, create_chart,
    screen_ticker, run_backtest, get_sp500, get_nasdaq100, get_dow
)

MAX_POSITIONS = 5

def init_portfolio():
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = []

def portfolio_tab():
    init_portfolio()
    portfolio = st.session_state.portfolio
    st.markdown("#### 💼 Portfolio Tracker")
    st.caption(f"Entry plan: max {MAX_POSITIONS} open positions")
    open_pos = [p for p in portfolio if p['status']=='open']
    if len(open_pos) < MAX_POSITIONS:
        with st.expander("➕ Add New Position", expanded=len(open_pos)==0):
            c1,c2,c3 = st.columns(3)
            t   = c1.text_input("Ticker", placeholder="AAPL", key="pt").upper()
            ep  = c2.number_input("Entry Price ($)", min_value=0.01, value=100.0, key="pep")
            sh  = c3.number_input("Shares", min_value=1, value=10, key="psh")
            c4,c5 = st.columns(2)
            sl  = c4.number_input("Stop Loss ($)",  min_value=0.01, value=round(ep*0.95,2), key="psl")
            tgt = c5.number_input("Target ($)",     min_value=0.01, value=round(ep*1.10,2), key="ptgt")
            if st.button("Add Position →", key="padd"):
                if t:
                    st.session_state.portfolio.append({
                        'ticker':t,'entry':ep,'shares':sh,'sl':sl,'target':tgt,
                        'status':'open','date_in':datetime.now().strftime("%d/%m/%Y"),
                        'date_out':None,'exit_price':None,'pnl':None
                    })
                    st.success(f"✅ {t} added!")
                    st.rerun()
    else:
        st.markdown(f"""<div class="upgrade-banner">
            ⚠️ Max <strong>{MAX_POSITIONS} positions</strong> for Entry plan.
            Upgrade to <strong>Pro</strong> for unlimited.
        </div>""", unsafe_allow_html=True)
    st.markdown("---")
    if not open_pos:
        st.info("No open positions yet.")
    else:
        st.markdown(f"**Open ({len(open_pos)}/{MAX_POSITIONS})**")
        for i,pos in enumerate(portfolio):
            if pos['status']!='open': continue
            try:
                cp = float(yf.download(pos['ticker'],period="1d",progress=False,auto_adjust=True)['Close'].iloc[-1])
            except:
                cp = pos['entry']
            pnl_pct = (cp-pos['entry'])/pos['entry']*100
            pnl_usd = (cp-pos['entry'])*pos['shares']
            cls = "pnl-pos" if pnl_pct>=0 else "pnl-neg"
            ico = "🟢" if pnl_pct>=0 else "🔴"
            c1,c2,c3,c4,c5 = st.columns([2,2,2,2,1])
            c1.markdown(f"**{pos['ticker']}**\n\n`{pos['shares']} shares`")
            c2.markdown(f"Entry: **${pos['entry']:.2f}**\n\nNow: **${cp:.2f}**")
            c3.markdown(f"SL: `${pos['sl']:.2f}`\n\nTarget: `${pos['target']:.2f}`")
            c4.markdown(f"<span class='{cls}'>{ico} {pnl_pct:+.2f}%<br>${pnl_usd:+.2f}</span>",unsafe_allow_html=True)
            if c5.button("Sold", key=f"entry_sold_{i}"):
                st.session_state.portfolio[i].update({'status':'closed','exit_price':cp,
                    'date_out':datetime.now().strftime("%d/%m/%Y"),'pnl':pnl_usd})
                st.rerun()
            if cp<=pos['sl']: st.error(f"⚠️ {pos['ticker']} hit Stop Loss!")
            if cp>=pos['target']: st.success(f"🎯 {pos['ticker']} hit Target!")
            st.markdown("---")
    closed = [p for p in portfolio if p['status']=='closed']
    if closed:
        st.markdown("**Closed Positions**")
        total = sum(p['pnl'] for p in closed if p['pnl'])
        cls = "pnl-pos" if total>=0 else "pnl-neg"
        st.markdown(f"Total P&L: <span class='{cls}'>${total:+.2f}</span>",unsafe_allow_html=True)
        df_c = pd.DataFrame([{
            'Ticker':p['ticker'],'Entry':f"${p['entry']:.2f}",
            'Exit':f"${p['exit_price']:.2f}" if p['exit_price'] else '-',
            'Shares':p['shares'],'P&L':f"${p['pnl']:+.2f}" if p['pnl'] else '-',
            'In':p['date_in'],'Out':p['date_out'] or '-'
        } for p in closed])
        st.dataframe(df_c, use_container_width=True, hide_index=True)


def show_entry_dashboard(user):
    inject_css()
    st.markdown(f"""
    <div class="orion-header">
        <div class="orion-logo">🎯 Orion <span>Signals</span></div>
        <span style="background:rgba(255,255,255,0.08);color:rgba(255,255,255,0.6);
            border:1px solid rgba(255,255,255,0.1);padding:0.25rem 0.75rem;
            border-radius:20px;font-size:0.75rem;font-weight:600;">📈 Stocks Entry</span>
    </div>""", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f"**👤 {user['name']}**")
        st.markdown(f"*{user['email']}*")
        st.markdown("---")
        st.markdown("""<div class="upgrade-banner">
            <strong>⚡ Upgrade to Pro €79</strong><br>
            <span style="color:rgba(255,255,255,0.5);font-size:0.75rem;">
            ATR/SL/Target · Fuel Gauge · Earnings Filter · Unlimited portfolio
            </span></div>""", unsafe_allow_html=True)
        st.markdown("")
        if st.button("🚪 Logout", key="entry_logout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    tab1,tab2,tab3,tab4 = st.tabs(["🔍 Single Stock","🎯 Screener","📊 Backtest","💼 Portfolio"])

    with tab1:
        c1,c2 = st.columns([1,3])
        with c1:
            ticker = st.text_input("Ticker",value="AAPL").upper()
            period = st.selectbox("Period",["6mo","1y"],index=1)
            btn = st.button("Analyze →",use_container_width=True)
        if btn or ticker:
            with st.spinner(f"Analyzing {ticker}..."):
                df = load_data(ticker,period)
            if df is None:
                st.error(f"No data for {ticker}")
            else:
                a = full_analysis(df)
                vc = {"STRONG BUY":"verdict-strong-buy","BUY":"verdict-buy",
                      "STRONG SELL":"verdict-sell","SELL":"verdict-sell"}.get(a['verdict'],"verdict-neutral")
                ico = {"STRONG BUY":"🟢","BUY":"🟢","STRONG SELL":"🔴","SELL":"🔴","MIXED SIGNALS":"🟡"}.get(a['verdict'],"⚪")
                st.markdown(f'<div class="verdict-banner {vc}">{ico} {a["verdict"]} — {ticker}</div>',unsafe_allow_html=True)
                c1,c2,c3,c4,c5 = st.columns(5)
                c1.metric("Price",f"${a['current']:.2f}")
                c2.metric("Score",f"{a['combined']:+.1f}")
                c3.metric("Momentum",f"{a['mom_score']:+.1f}")
                c4.metric("Technical",f"{a['tech_score']:+.1f}")
                c5.metric("Agreement","✅ YES" if a['agreement'] else "⚠️ NO")
                st.markdown("#### Returns")
                rcols = st.columns(len(a['returns']))
                for col,(tf,ret) in zip(rcols,a['returns'].items()):
                    col.metric(tf,f"{ret:+.2f}%")
                st.plotly_chart(create_chart(df,a),use_container_width=True)
                st.markdown("#### Signals")
                s1,s2 = st.columns(2)
                for i,(text,d) in enumerate(a['signals']):
                    ic = {"bullish":"🟢","bearish":"🔴","neutral":"⚪"}[d]
                    (s1 if i%2==0 else s2).write(f"{ic} {text}")
                st.markdown("""<div class="upgrade-banner">
                    ⚡ <strong>Pro</strong>: ATR Entry/SL/Target · Fuel Gauge · EMA21 · Stochastic · VWAP · Earnings Filter
                </div>""",unsafe_allow_html=True)

    with tab2:
        st.markdown("Scans universe and surfaces top bullish candidates.")
        st.caption("⚠️ Entry plan: top 10 results only.")
        c1,c2 = st.columns(2)
        universe = c1.selectbox("Universe",["dow","nasdaq100","sp500"],
                                 format_func=lambda x:{"dow":"Dow 30","nasdaq100":"NASDAQ 100","sp500":"S&P 500"}[x])
        min_score = c2.number_input("Min Score",min_value=-100,max_value=100,value=20)
        if st.button("🚀 Run Screener",use_container_width=True):
            tickers = get_sp500() if universe=="sp500" else get_nasdaq100() if universe=="nasdaq100" else get_dow()
            st.info(f"Scanning {len(tickers)} stocks...")
            prog = st.progress(0); results = []
            with ThreadPoolExecutor(max_workers=10) as ex:
                futures = {ex.submit(screen_ticker,t):t for t in tickers}
                done = 0
                for f in as_completed(futures):
                    done+=1; r=f.result()
                    if r: results.append(r)
                    prog.progress(done/len(tickers))
            prog.empty()
            if results:
                import pandas as pd
                dfr = pd.DataFrame(results)
                dff = dfr[dfr['combined']>=min_score].sort_values('combined',ascending=False).head(10)
                if dff.empty:
                    st.warning(f"No stocks with score >= {min_score}")
                else:
                    dd = dff.copy()
                    dd['price']      = dd['price'].apply(lambda x:f"${x:.2f}")
                    dd['combined']   = dd['combined'].apply(lambda x:f"{x:+.1f}")
                    dd['ret_1m']     = dd['ret_1m'].apply(lambda x:f"{x:+.1f}%")
                    dd['ret_3m']     = dd['ret_3m'].apply(lambda x:f"{x:+.1f}%")
                    dd['macd_cross'] = dd['macd_cross'].apply(lambda x:"🔔" if x else "")
                    dd['above_ma200']= dd['above_ma200'].apply(lambda x:"✓" if x else "")
                    dd = dd[['ticker','price','verdict','combined','rsi','ret_1m','ret_3m','macd_cross','above_ma200']]
                    dd.columns = ['Ticker','Price','Verdict','Score','RSI','1M%','3M%','MACD↑','MA200']
                    st.dataframe(dd,use_container_width=True,hide_index=True)

    with tab3:
        st.markdown("Test if the strategy has edge over random entry.")
        st.info("⚠️ Entry plan: 1 year history max.")
        c1,c2,c3 = st.columns(3)
        bt = c1.text_input("Ticker",value="AAPL",key="bt").upper()
        tp = c2.number_input("Target %",min_value=1,max_value=50,value=10)
        hz = c3.number_input("Horizon (days)",min_value=5,max_value=60,value=30)
        if st.button("📊 Run Backtest",use_container_width=True):
            with st.spinner(f"Backtesting {bt}..."):
                df = load_data(bt,period="1y")
                if df is None or len(df)<100:
                    st.error("Insufficient data")
                else:
                    res = run_backtest(df,target_pct=tp,horizon=hz)
                    if res is None:
                        st.warning("No signals found")
                    else:
                        c1,c2,c3,c4 = st.columns(4)
                        c1.metric("Signals",res['n_trades'])
                        c2.metric("Win Rate",f"{res['win_rate']:.1f}%",
                                  f"{res['win_rate']-res['baseline_win_rate']:+.1f}pp vs random")
                        c3.metric("Avg Return",f"{res['avg_return']:+.2f}%")
                        c4.metric("Baseline",f"{res['baseline_win_rate']:.1f}%")
                        ew = res['win_rate']-res['baseline_win_rate']
                        er = res['avg_return']-res['baseline_avg']
                        if ew>5 and er>1: st.success("✅ Positive edge over random entry")
                        elif ew>0: st.warning("🟡 Marginal edge")
                        else: st.error("❌ No edge detected")

    with tab4:
        portfolio_tab()

    st.markdown("---")
    st.caption("⚠️ Educational tool only. Not financial advice.")
