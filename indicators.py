"""
Orion Signals — Shared Indicators & Analysis
Κοινές functions για όλα τα dashboards.
"""
import warnings
warnings.filterwarnings('ignore')
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ============================================================
# INDICATORS
# ============================================================
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

def atr_calc(df, period=14):
    h,l,c = df['High'],df['Low'],df['Close']
    tr = pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    return tr.rolling(period).mean()


# ============================================================
# DATA
# ============================================================
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
        return ['AAPL','MSFT','NVDA','GOOGL','AMZN','META','TSLA','JPM','V','UNH',
                'HD','PG','JNJ','MA','COST','ABBV','MRK','LLY','CVX','PEP']

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


# ============================================================
# ANALYSIS
# ============================================================
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

    return {
        'current':current,'returns':returns,'mom_score':mom_score,'tech_score':tech,
        'combined':combined,'verdict':verdict,'agreement':agree,
        'ma20':ma20,'ma50':ma50,'ma200':ma200,'rsi':rsi_v,'adx':adx_v,
        'bb_pos':bb_pos,'vol_ratio':vol_r,'macd_cross':mc,'signals':sigs,
        'bb_upper':bbu,'bb_mid':bbm,'bb_lower':bbl,'macd_line':ml,'signal_line':sl,
        'pct_from_high':(current-h52)/h52*100,'pct_from_low':(current-l52)/l52*100
    }


def screen_ticker(ticker):
    try:
        df = yf.download(ticker,period="1y",progress=False,auto_adjust=True,threads=False)
        if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        if df.empty or len(df)<252: return None
        close=df['Close']; volume=df['Volume']
        current=float(close.iloc[-1])
        if current<5 or float(volume.tail(20).mean())<100_000: return None
        a=full_analysis(df)
        return {
            'ticker':ticker,'price':current,'verdict':a['verdict'],'combined':a['combined'],
            'mom_score':a['mom_score'],'tech_score':a['tech_score'],'rsi':a['rsi'],
            'ret_1m':a['returns'].get('1m',0),'ret_3m':a['returns'].get('3m',0),
            'ret_12m':a['returns'].get('12m',0),'macd_cross':a['macd_cross'],
            'above_ma200':current>a['ma200'] if a['ma200'] else False
        }
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
    return {
        'n_trades':len(trades),'win_rate':dt['hit'].mean()*100,
        'avg_return':dt['fr'].mean(),
        'baseline_win_rate':bl_h/len(bl_r)*100 if bl_r else 0,
        'baseline_avg':np.mean(bl_r) if bl_r else 0
    }


# ============================================================
# CHART
# ============================================================
def create_chart(df, a):
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
    fig.add_trace(go.Scatter(x=df.index,y=a['bb_upper'],name='BB',
                              line=dict(color='rgba(124,58,237,0.5)',width=1,dash='dot'),showlegend=False),row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=a['bb_lower'],name='BB',
                              line=dict(color='rgba(124,58,237,0.5)',width=1,dash='dot'),
                              fill='tonexty',fillcolor='rgba(124,58,237,0.03)',showlegend=False),row=1,col=1)
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


# ============================================================
# CSS
# ============================================================
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=Inter:wght@300;400;500&display=swap');
    #MainMenu,footer,.stDeployButton{display:none!important}
    [data-testid="stToolbar"]{display:none!important}
    .stApp{background:#080810;font-family:'Inter',sans-serif;color:#E2E8F0}
    [data-testid="stSidebar"]{background:#0D0D1A!important;border-right:1px solid rgba(124,58,237,0.15)!important}
    [data-testid="stSidebar"] *{color:#E2E8F0!important}
    .orion-header{display:flex;align-items:center;justify-content:space-between;
        padding:1rem 0 1.5rem;border-bottom:1px solid rgba(124,58,237,0.2);margin-bottom:1.5rem}
    .orion-logo{font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;color:#fff}
    .orion-logo span{color:#7C3AED}
    [data-testid="metric-container"]{background:rgba(255,255,255,0.03)!important;
        border:1px solid rgba(124,58,237,0.15)!important;border-radius:12px!important;padding:1rem!important}
    [data-testid="metric-container"] label{color:rgba(255,255,255,0.5)!important;
        font-size:0.75rem!important;text-transform:uppercase!important;letter-spacing:0.08em!important}
    [data-testid="metric-container"] [data-testid="stMetricValue"]{color:#fff!important;
        font-family:'Syne',sans-serif!important;font-size:1.4rem!important}
    .verdict-banner{padding:1rem 1.5rem;border-radius:12px;margin:1rem 0;
        font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:700}
    .verdict-strong-buy{background:rgba(0,200,83,0.1);border:1px solid rgba(0,200,83,0.3);color:#00C853}
    .verdict-buy{background:rgba(0,200,83,0.06);border:1px solid rgba(0,200,83,0.2);color:#69F0AE}
    .verdict-neutral{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:rgba(255,255,255,0.6)}
    .verdict-sell{background:rgba(255,61,87,0.08);border:1px solid rgba(255,61,87,0.2);color:#FF3D57}
    .stTabs [data-baseweb="tab-list"]{background:transparent!important;
        border-bottom:1px solid rgba(124,58,237,0.2)!important;gap:0!important}
    .stTabs [data-baseweb="tab"]{background:transparent!important;
        color:rgba(255,255,255,0.4)!important;font-size:0.9rem!important;
        padding:0.75rem 1.5rem!important;border:none!important}
    .stTabs [aria-selected="true"]{color:#7C3AED!important;border-bottom:2px solid #7C3AED!important}
    .stTextInput>div>div>input,.stSelectbox>div>div,.stNumberInput>div>div>input{
        background:rgba(255,255,255,0.05)!important;border:1px solid rgba(124,58,237,0.3)!important;
        border-radius:8px!important;color:#fff!important}
    .stButton>button{background:linear-gradient(135deg,#7C3AED,#5B21B6)!important;
        color:white!important;border:none!important;border-radius:8px!important;
        font-family:'Syne',sans-serif!important;font-weight:700!important;
        transition:all 0.2s!important;box-shadow:0 4px 15px rgba(124,58,237,0.3)!important}
    .stButton>button:hover{transform:translateY(-1px)!important;
        box-shadow:0 6px 20px rgba(124,58,237,0.5)!important}
    .upgrade-banner{background:rgba(124,58,237,0.08);border:1px solid rgba(124,58,237,0.25);
        border-radius:12px;padding:1rem 1.5rem;margin:1rem 0;font-size:0.85rem;color:rgba(255,255,255,0.6)}
    .upgrade-banner strong{color:#A78BFA}
    .pnl-pos{color:#00C853;font-weight:700}
    .pnl-neg{color:#FF3D57;font-weight:700}
    </style>
    """, unsafe_allow_html=True)
