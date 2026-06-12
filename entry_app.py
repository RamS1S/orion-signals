"""
Orion Signals — Entry Dashboard (COMPLETE)
-------------------------------------------
Entry Plan €29/μήνα
- Scanner Top 10
- 13 βασικοί δείκτες
- Backtesting 1 χρόνο
- Portfolio tracker max 5
- Telegram daily (placeholder)
"""

import time
import warnings
warnings.filterwarnings('ignore')
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=Inter:wght@300;400;500&display=swap');
    #MainMenu,footer,.stDeployButton{display:none!important}
    [data-testid="stToolbar"]{display:none!important}
    .stApp{background:#080810;font-family:'Inter',sans-serif;color:#E2E8F0}
    [data-testid="stSidebar"]{background:#0D0D1A!important;border-right:1px solid rgba(124,58,237,0.15)!important}
    [data-testid="stSidebar"] *{color:#E2E8F0!important}
    .orion-header{display:flex;align-items:center;justify-content:space-between;padding:1rem 0 1.5rem;border-bottom:1px solid rgba(124,58,237,0.2);margin-bottom:1.5rem}
    .orion-logo{font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;color:#fff}
    .orion-logo span{color:#7C3AED}
    .plan-badge{background:rgba(255,255,255,0.08);color:rgba(255,255,255,0.6);border:1px solid rgba(255,255,255,0.1);padding:0.25rem 0.75rem;border-radius:20px;font-size:0.75rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase}
    [data-testid="metric-container"]{background:rgba(255,255,255,0.03)!important;border:1px solid rgba(124,58,237,0.15)!important;border-radius:12px!important;padding:1rem!important}
    [data-testid="metric-container"] label{color:rgba(255,255,255,0.5)!important;font-size:0.75rem!important;text-transform:uppercase!important;letter-spacing:0.08em!important}
    [data-testid="metric-container"] [data-testid="stMetricValue"]{color:#fff!important;font-family:'Syne',sans-serif!important;font-size:1.4rem!important}
    .verdict-banner{padding:1rem 1.5rem;border-radius:12px;margin:1rem 0;font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:700}
    .verdict-strong-buy{background:rgba(0,200,83,0.1);border:1px solid rgba(0,200,83,0.3);color:#00C853}
    .verdict-buy{background:rgba(0,200,83,0.06);border:1px solid rgba(0,200,83,0.2);color:#69F0AE}
    .verdict-neutral{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:rgba(255,255,255,0.6)}
    .verdict-sell{background:rgba(255,61,87,0.08);border:1px solid rgba(255,61,87,0.2);color:#FF3D57}
    .stTabs [data-baseweb="tab-list"]{background:transparent!important;border-bottom:1px solid rgba(124,58,237,0.2)!important;gap:0!important}
    .stTabs [data-baseweb="tab"]{background:transparent!important;color:rgba(255,255,255,0.4)!important;font-family:'Inter',sans-serif!important;font-size:0.9rem!important;padding:0.75rem 1.5rem!important;border:none!important}
    .stTabs [aria-selected="true"]{color:#7C3AED!important;border-bottom:2px solid #7C3AED!important}
    .stTextInput>div>div>input,.stSelectbox>div>div,.stNumberInput>div>div>input{background:rgba(255,255,255,0.05)!important;border:1px solid rgba(124,58,237,0.3)!important;border-radius:8px!important;color:#fff!important}
    .stButton>button{background:linear-gradient(135deg,#7C3AED,#5B21B6)!important;color:white!important;border:none!important;border-radius:8px!important;font-family:'Syne',sans-serif!important;font-weight:700!important;transition:all 0.2s!important;box-shadow:0 4px 15px rgba(124,58,237,0.3)!important}
    .stButton>button:hover{transform:translateY(-1px)!important;box-shadow:0 6px 20px rgba(124,58,237,0.5)!important}
    .upgrade-banner{background:rgba(124,58,237,0.08);border:1px solid rgba(124,58,237,0.25);border-radius:12px;padding:1rem 1.5rem;margin:1rem 0;font-size:0.85rem;color:rgba(255,255,255,0.6)}
    .upgrade-banner strong{color:#A78BFA}
    .pnl-pos{color:#00C853;font-weight:700}
    .pnl-neg{color:#FF3D57;font-weight:700}
    </style>
    """, unsafe_allow_html=True)


def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta>0,0).rolling(period).mean()
    loss = (-delta.where(delta<0,0)).rolling(period).mean()
    return 100-(100/(1+gain/loss))

def macd(series, fast=12, slow=26, signal=9):
    ef = series.ewm(span=fast,adjust=False).mean()
    es = series.ewm(span=slow,adjust=False).mean()
    ml = ef-es
    sl = ml.ewm(span=signal,adjust=False).mean()
    return ml, sl, ml-sl

def bollinger(series, period=20, std=2):
    ma = series.rolling(period).mean()
    sd = series.rolling(period).std()
    return ma+sd*std, ma, ma-sd*std

def adx_calc(df, period=14):
    h,l,c = df['High'],df['Low'],df['Close']
    pdm = h.diff().clip(lower=0)
    mdm = (-l.diff()).clip(lower=0)
    tr = pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    pdi = 100*(pdm.rolling(period).mean()/atr)
    mdi = 100*(mdm.rolling(period).mean()/atr)
    dx = 100*(pdi-mdi).abs()/(pdi+mdi)
    return dx.rolling(period).mean()


@st.cache_data(ttl=600)
def load_data(ticker, period="1y"):
    df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

@st.cache_data(ttl=3600)
def get_sp500():
    try:
        t = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]['Symbol'].tolist()
        return [x.replace('.', '-') for x in t]
    except:
        return ['AAPL','MSFT','NVDA','GOOGL','AMZN','META','TSLA','JPM','V','UNH']

@st.cache_data(ttl=3600)
def get_nasdaq100():
    try:
        tables = pd.read_html("https://en.wikipedia.org/wiki/Nasdaq-100")
        for tbl in tables:
            for col in ['Ticker','Symbol']:
                if col in tbl.columns:
                    return [x.replace('.', '-') for x in tbl[col].tolist()]
    except: pass
    return ['AAPL','MSFT','NVDA','GOOGL','AMZN','META','TSLA','AVGO','COST','NFLX']

def get_dow():
    return ['AAPL','AMGN','AXP','BA','CAT','CRM','CSCO','CVX','DIS','GS',
            'HD','HON','IBM','JNJ','JPM','KO','MCD','MMM','MRK','MSFT',
            'NKE','PG','SHW','TRV','UNH','V','VZ','WMT','NVDA','AMZN']


def full_analysis(df):
    close = df['Close']
    volume = df['Volume']
    current = float(close.iloc[-1])

    timeframes = {'1w':5,'1m':21,'3m':63,'6m':126,'12m':252}
    returns = {}
    for name,days in timeframes.items():
        if len(close) > days:
            returns[name] = float((current-float(close.iloc[-days-1]))/float(close.iloc[-days-1])*100)

    weights = {'1w':0.1,'1m':0.2,'3m':0.3,'6m':0.2,'12m':0.2}
    mom_score = sum(np.clip(returns.get(tf,0)*5,-100,100)*w for tf,w in weights.items())

    ma20  = float(close.rolling(20).mean().iloc[-1])
    ma50  = float(close.rolling(50).mean().iloc[-1])
    ma200 = float(close.rolling(200).mean().iloc[-1]) if len(close)>=200 else None
    rsi_v = float(rsi(close).iloc[-1])
    ml,sl,_ = macd(close)
    mb = float(ml.iloc[-1]) > float(sl.iloc[-1])
    mc = (float(ml.iloc[-2]) <= float(sl.iloc[-2])) and mb
    bbu,bbm,bbl = bollinger(close)
    bb_pos = float((current-float(bbl.iloc[-1]))/(float(bbu.iloc[-1])-float(bbl.iloc[-1]))*100)
    adx_v = float(adx_calc(df).iloc[-1])
    vol_r = float(volume.iloc[-1])/float(volume.tail(20).mean())

    sigs = []; bull = bear = 0
    def add(t,d,w=1):
        nonlocal bull,bear
        sigs.append((t,d))
        if d=='bullish': bull+=w
        elif d=='bearish': bear+=w

    add(f"Price ${current:.2f} vs MA20 ${ma20:.2f}","bullish" if current>ma20 else "bearish")
    add(f"Price vs MA50 ${ma50:.2f}","bullish" if current>ma50 else "bearish")
    if ma200:
        add(f"Price vs MA200 ${ma200:.2f}","bullish" if current>ma200 else "bearish")
        add("Golden Cross ✓" if ma50>ma200 else "Death Cross ✗","bullish" if ma50>ma200 else "bearish")
    if rsi_v>70: add(f"RSI {rsi_v:.1f} — overbought","bearish")
    elif rsi_v<30: add(f"RSI {rsi_v:.1f} — oversold","bullish")
    elif rsi_v>50: add(f"RSI {rsi_v:.1f} — bullish momentum","bullish")
    else: add(f"RSI {rsi_v:.1f} — bearish momentum","bearish")
    if mc: add("MACD fresh bullish crossover 🔔","bullish",w=2)
    elif mb: add("MACD above signal line","bullish")
    else: add("MACD below signal line","bearish")
    add(f"ADX {adx_v:.1f} — {'strong' if adx_v>25 else 'weak'} trend","neutral")
    if vol_r>1.5: add(f"Volume {vol_r:.1f}x avg — high interest","bullish")
    elif vol_r<0.5: add(f"Volume {vol_r:.1f}x avg — low interest","bearish")
    if bb_pos>100: add("Price above upper Bollinger","bearish")
    elif bb_pos<0: add("Price below lower Bollinger","bullish")

    tech = ((bull-bear)/max(bull+bear,1))*100
    combined = (mom_score+tech)/2
    agree = (mom_score>0 and tech>0) or (mom_score<0 and tech<0)

    if combined>50 and agree: verdict="STRONG BUY"
    elif combined>20 and agree: verdict="BUY"
    elif combined<-50 and agree: verdict="STRONG SELL"
    elif combined<-20 and agree: verdict="SELL"
    elif not agree and abs(combined)>10: verdict="MIXED SIGNALS"
    else: verdict="NEUTRAL"

    h52 = float(close.tail(252).max())
    l52 = float(close.tail(252).min())

    return {'current':current,'returns':returns,'mom_score':mom_score,'tech_score':tech,
            'combined':combined,'verdict':verdict,'agreement':agree,
            'ma20':ma20,'ma50':ma50,'ma200':ma200,'rsi':rsi_v,'adx':adx_v,
            'bb_pos':bb_pos,'vol_ratio':vol_r,'macd_cross':mc,'signals':sigs,
            'bb_upper':bbu,'bb_mid':bbm,'bb_lower':bbl,'macd_line':ml,'signal_line':sl,
            'pct_from_high':(current-h52)/h52*100,'pct_from_low':(current-l52)/l52*100}


def create_chart(df,a):
    fig = make_subplots(rows=3,cols=1,shared_xaxes=True,vertical_spacing=0.03,
                        row_heights=[0.6,0.2,0.2],
                        subplot_titles=("Price + MAs + Bollinger","RSI","MACD"))
    fig.add_trace(go.Candlestick(x=df.index,open=df['Open'],high=df['High'],
                                  low=df['Low'],close=df['Close'],name='Price',showlegend=False,
                                  increasing_line_color='#00C853',decreasing_line_color='#FF3D57'),row=1,col=1)
    ma20=df['Close'].rolling(20).mean()
    ma50=df['Close'].rolling(50).mean()
    ma200=df['Close'].rolling(200).mean()
    fig.add_trace(go.Scatter(x=df.index,y=ma20,name='MA20',line=dict(color='#F59E0B',width=1)),row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=ma50,name='MA50',line=dict(color='#3B82F6',width=1)),row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=ma200,name='MA200',line=dict(color='#EF4444',width=1.5)),row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=a['bb_upper'],name='BB',line=dict(color='rgba(124,58,237,0.5)',width=1,dash='dot'),showlegend=False),row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=a['bb_lower'],name='BB',line=dict(color='rgba(124,58,237,0.5)',width=1,dash='dot'),fill='tonexty',fillcolor='rgba(124,58,237,0.03)',showlegend=False),row=1,col=1)
    rs=rsi(df['Close'])
    fig.add_trace(go.Scatter(x=df.index,y=rs,name='RSI',line=dict(color='#7C3AED')),row=2,col=1)
    fig.add_hline(y=70,line_dash="dash",line_color="rgba(255,61,87,0.5)",row=2,col=1)
    fig.add_hline(y=30,line_dash="dash",line_color="rgba(0,200,83,0.5)",row=2,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=a['macd_line'],name='MACD',line=dict(color='#3B82F6')),row=3,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=a['signal_line'],name='Signal',line=dict(color='#F59E0B')),row=3,col=1)
    hist=a['macd_line']-a['signal_line']
    fig.add_trace(go.Bar(x=df.index,y=hist,name='Hist',
                          marker_color=['#00C853' if v>0 else '#FF3D57' for v in hist],showlegend=False),row=3,col=1)
    fig.update_layout(height=680,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                      xaxis_rangeslider_visible=False,hovermode='x unified',
                      margin=dict(t=40,b=20),font=dict(color='#E2E8F0'),
                      legend=dict(bgcolor='rgba(0,0,0,0)'))
    fig.update_xaxes(gridcolor='rgba(255,255,255,0.05)',showgrid=True)
    fig.update_yaxes(gridcolor='rgba(255,255,255,0.05)',showgrid=True)
    return fig


def screen_ticker(ticker):
    try:
        df = yf.download(ticker,period="1y",progress=False,auto_adjust=True,threads=False)
        if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        if df.empty or len(df)<252: return None
        close=df['Close']; volume=df['Volume']
        current=float(close.iloc[-1])
        if current<5 or float(volume.tail(20).mean())<100_000: return None
        a=full_analysis(df)
        return {'ticker':ticker,'price':current,'verdict':a['verdict'],'combined':a['combined'],
                'mom_score':a['mom_score'],'tech_score':a['tech_score'],'rsi':a['rsi'],
                'ret_1m':a['returns'].get('1m',0),'ret_3m':a['returns'].get('3m',0),
                'ret_12m':a['returns'].get('12m',0),'macd_cross':a['macd_cross'],
                'above_ma200':current>a['ma200'] if a['ma200'] else False}
    except: return None


def run_backtest(df, target_pct=10, horizon=30):
    close=df['Close']
    ma20=close.rolling(20).mean(); ma50=close.rolling(50).mean(); ma200=close.rolling(200).mean()
    rv=rsi(close); ml,sl,_=macd(close); bbu,_,bbl=bollinger(close)
    bbp=((close-bbl)/(bbu-bbl))*100; vr=df['Volume']/df['Volume'].rolling(20).mean()
    r1w=(close/close.shift(5)-1)*100; r1m=(close/close.shift(21)-1)*100
    r3m=(close/close.shift(63)-1)*100; r6m=(close/close.shift(126)-1)*100
    r12m=(close/close.shift(252)-1)*100
    mom=(np.clip(r1w*5,-100,100)*0.1+np.clip(r1m*5,-100,100)*0.2+
         np.clip(r3m*5,-100,100)*0.3+np.clip(r6m*5,-100,100)*0.2+np.clip(r12m*5,-100,100)*0.2)
    bull=((close>ma20).astype(int)+(close>ma50).astype(int)+(close>ma200).astype(int)+
          (ma50>ma200).astype(int)+((rv>50)&(rv<=70)).astype(int)+(rv<30).astype(int)+
          (ml>sl).astype(int)+(vr>1.5).astype(int)+(bbp<0).astype(int))
    bear=((close<=ma20).astype(int)+(close<=ma50).astype(int)+(close<=ma200).astype(int)+
          (ma50<=ma200).astype(int)+(rv>70).astype(int)+((rv<=50)&(rv>=30)).astype(int)+
          (ml<=sl).astype(int)+(vr<0.5).astype(int)+(bbp>100).astype(int))
    tech=((bull-bear)/(bull+bear).replace(0,1))*100
    combined=(mom+tech)/2; agreement=((mom>0)&(tech>0))|((mom<0)&(tech<0))
    sig=pd.Series('NEUTRAL',index=close.index)
    sig[(combined>50)&agreement]='STRONG_BUY'; sig[(combined>20)&(combined<=50)&agreement]='BUY'
    is_s=sig.isin(['BUY','STRONG_BUY']); fresh=is_s&~is_s.shift(1).fillna(False)
    trades=[]
    for date in close.index[fresh]:
        idx=close.index.get_loc(date)
        if idx+1>=len(close): continue
        e=float(close.iloc[idx+1]); end=min(idx+1+horizon,len(close)-1)
        f=close.iloc[idx+1:end+1]
        mg=float((f.max()-e)/e*100); fr=float((f.iloc[-1]-e)/e*100)
        trades.append({'mg':mg,'fr':fr,'hit':mg>=target_pct})
    if not trades: return None
    dt=pd.DataFrame(trades)
    bl_r=[]; bl_h=0
    for i in range(len(close)-horizon-1):
        e=float(close.iloc[i+1]); f=close.iloc[i+1:i+1+horizon]
        r=float((f.iloc[-1]-e)/e*100); g=float((f.max()-e)/e*100)
        bl_r.append(r)
        if g>=target_pct: bl_h+=1
    return {'n_trades':len(trades),'win_rate':dt['hit'].mean()*100,
            'avg_return':dt['fr'].mean(),
            'baseline_win_rate':bl_h/len(bl_r)*100 if bl_r else 0,
            'baseline_avg':np.mean(bl_r) if bl_r else 0}


# ── PORTFOLIO ──
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
            t   = c1.text_input("Ticker",   placeholder="AAPL", key="pt").upper()
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
        st.markdown(f"""
        <div class="upgrade-banner">
            ⚠️ You've reached <strong>max {MAX_POSITIONS} positions</strong> for Entry plan.
            Upgrade to <strong>Pro</strong> for unlimited tracking.
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
            if c5.button("Sold",key=f"sold_{i}"):
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
        df_c = pd.DataFrame([{'Ticker':p['ticker'],'Entry':f"${p['entry']:.2f}",
            'Exit':f"${p['exit_price']:.2f}" if p['exit_price'] else '-',
            'Shares':p['shares'],'P&L':f"${p['pnl']:+.2f}" if p['pnl'] else '-',
            'In':p['date_in'],'Out':p['date_out'] or '-'} for p in closed])
        st.dataframe(df_c,use_container_width=True,hide_index=True)


# ── MAIN ──
def show_entry_dashboard(user):
    inject_css()

    st.markdown(f"""
    <div class="orion-header">
        <div class="orion-logo">🎯 Orion <span>Signals</span></div>
        <span class="plan-badge">Entry Plan</span>
    </div>""", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f"**👤 {user['name']}**")
        st.markdown(f"*{user['email']}*")
        st.markdown("---")
        st.markdown("""
        <div style="background:rgba(124,58,237,0.1);border:1px solid rgba(124,58,237,0.2);
                    border-radius:10px;padding:0.8rem;font-size:0.8rem;color:#A78BFA;">
            <strong>⚡ Upgrade to Pro €79</strong><br>
            <span style="color:rgba(255,255,255,0.5);font-size:0.75rem;">
            ATR/SL/Target · Fuel Gauge · Earnings Filter · Unlimited portfolio · Real-time alerts
            </span>
        </div>""", unsafe_allow_html=True)
        st.markdown("")
        if st.button("🚪 Logout", key="entry_logout"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

    tab1,tab2,tab3,tab4 = st.tabs(["🔍 Single Stock","🎯 Screener","📊 Backtest","💼 Portfolio"])

    # ── SINGLE STOCK ──
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

    # ── SCREENER ──
    with tab2:
        st.markdown("Scans universe and surfaces top bullish candidates.")
        st.caption("⚠️ Entry plan: top 10 results only.")
        c1,c2 = st.columns(2)
        universe = c1.selectbox("Universe",["dow","nasdaq100","sp500"],
                                 format_func=lambda x:{"dow":"Dow 30 (fast)","nasdaq100":"NASDAQ 100","sp500":"S&P 500"}[x])
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

    # ── BACKTEST ──
    with tab3:
        st.markdown("Test if the strategy has edge over random entry.")
        st.info("⚠️ Entry plan: 1 year history max. Pro unlocks 10 years.")
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
                        else: st.error("❌ No edge detected in this period")

    # ── PORTFOLIO ──
    with tab4:
        portfolio_tab()

    st.markdown("---")
    st.caption("⚠️ Educational tool only. Not financial advice.")

                            st.error("❌ Δεν υπάρχει edge")

    st.markdown("---")
    st.caption("⚠️ Educational tool only. Not financial advice.")
