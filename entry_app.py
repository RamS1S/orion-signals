"""
Orion Signals — Entry Dashboard
---------------------------------
Βασικό περιβάλλον για Entry users.
Ίδια λογική με το αρχικό app.py + Orion UI.
"""

import time
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
# CSS — Orion Dark Theme
# ============================================================
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=Inter:wght@300;400;500&display=swap');

    #MainMenu, footer, .stDeployButton { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }

    .stApp {
        background: #080810;
        font-family: 'Inter', sans-serif;
        color: #E2E8F0;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #0D0D1A !important;
        border-right: 1px solid rgba(124,58,237,0.15) !important;
    }

    [data-testid="stSidebar"] * { color: #E2E8F0 !important; }

    /* Header */
    .orion-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 0 1.5rem;
        border-bottom: 1px solid rgba(124,58,237,0.2);
        margin-bottom: 1.5rem;
    }

    .orion-logo {
        font-family: 'Syne', sans-serif;
        font-size: 1.5rem;
        font-weight: 800;
        color: #fff;
    }

    .orion-logo span { color: #7C3AED; }

    .plan-badge {
        background: rgba(255,255,255,0.08);
        color: rgba(255,255,255,0.6);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(124,58,237,0.15) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }

    [data-testid="metric-container"] label {
        color: rgba(255,255,255,0.5) !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
    }

    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-family: 'Syne', sans-serif !important;
        font-size: 1.4rem !important;
    }

    /* Verdict banner */
    .verdict-banner {
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        font-family: 'Syne', sans-serif;
        font-size: 1.3rem;
        font-weight: 700;
    }

    .verdict-strong-buy {
        background: rgba(0,200,83,0.1);
        border: 1px solid rgba(0,200,83,0.3);
        color: #00C853;
    }

    .verdict-buy {
        background: rgba(0,200,83,0.06);
        border: 1px solid rgba(0,200,83,0.2);
        color: #69F0AE;
    }

    .verdict-neutral {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        color: rgba(255,255,255,0.6);
    }

    .verdict-sell {
        background: rgba(255,61,87,0.08);
        border: 1px solid rgba(255,61,87,0.2);
        color: #FF3D57;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 1px solid rgba(124,58,237,0.2) !important;
        gap: 0 !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: rgba(255,255,255,0.4) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.9rem !important;
        padding: 0.75rem 1.5rem !important;
        border: none !important;
    }

    .stTabs [aria-selected="true"] {
        color: #7C3AED !important;
        border-bottom: 2px solid #7C3AED !important;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(124,58,237,0.3) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }

    /* Button */
    .stButton > button {
        background: linear-gradient(135deg, #7C3AED, #5B21B6) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        transition: all 0.2s !important;
        box-shadow: 0 4px 15px rgba(124,58,237,0.3) !important;
    }

    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(124,58,237,0.5) !important;
    }

    /* Dataframe */
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(124,58,237,0.2) !important;
        border-radius: 12px !important;
    }

    /* Signal pills */
    .signal-bull {
        color: #00C853;
        font-size: 0.85rem;
        padding: 0.2rem 0;
    }

    .signal-bear {
        color: #FF3D57;
        font-size: 0.85rem;
        padding: 0.2rem 0;
    }

    .signal-neutral {
        color: rgba(255,255,255,0.4);
        font-size: 0.85rem;
        padding: 0.2rem 0;
    }
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# INDICATORS
# ============================================================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line, macd_line - signal_line

def bollinger(series, period=20, std=2):
    ma = series.rolling(period).mean()
    sd = series.rolling(period).std()
    return ma + sd*std, ma, ma - sd*std

def adx_calc(df, period=14):
    high, low, close = df['High'], df['Low'], df['Close']
    plus_dm = high.diff().clip(lower=0)
    minus_dm = (-low.diff()).clip(lower=0)
    tr = pd.concat([high-low, (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    return dx.rolling(period).mean()


# ============================================================
# DATA & ANALYSIS
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
        tables = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
        return [t.replace('.', '-') for t in tables[0]['Symbol'].tolist()]
    except:
        return ['AAPL','MSFT','NVDA','GOOGL','AMZN','META','TSLA','JPM','V','UNH']

@st.cache_data(ttl=3600)
def get_nasdaq100():
    try:
        tables = pd.read_html("https://en.wikipedia.org/wiki/Nasdaq-100")
        for tbl in tables:
            for col in ['Ticker', 'Symbol']:
                if col in tbl.columns:
                    return [t.replace('.', '-') for t in tbl[col].tolist()]
    except: pass
    return ['AAPL','MSFT','NVDA','GOOGL','AMZN','META','TSLA','AVGO','COST','NFLX']

def get_dow():
    return ['AAPL','AMGN','AXP','BA','CAT','CRM','CSCO','CVX','DIS','GS',
            'HD','HON','IBM','JNJ','JPM','KO','MCD','MMM','MRK','MSFT',
            'NKE','PG','SHW','TRV','UNH','V','VZ','WMT','NVDA','AMZN']

def full_analysis(df):
    close = df['Close']
    volume = df['Volume']
    current = close.iloc[-1]

    timeframes = {'1w': 5, '1m': 21, '3m': 63, '6m': 126, '12m': 252}
    returns = {}
    for name, days in timeframes.items():
        if len(close) > days:
            returns[name] = ((current - close.iloc[-days-1]) / close.iloc[-days-1]) * 100

    weights = {'1w': 0.1, '1m': 0.2, '3m': 0.3, '6m': 0.2, '12m': 0.2}
    mom_score = sum(np.clip(returns.get(tf, 0) * 5, -100, 100) * w
                    for tf, w in weights.items() if tf in returns)

    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]
    ma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None
    rsi_val = rsi(close).iloc[-1]
    macd_line, signal_line, _ = macd(close)
    macd_bullish = macd_line.iloc[-1] > signal_line.iloc[-1]
    macd_cross = (macd_line.iloc[-2] <= signal_line.iloc[-2]) and macd_bullish
    bb_upper, bb_mid, bb_lower = bollinger(close)
    bb_pos = ((current - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])) * 100
    adx_val = adx_calc(df).iloc[-1]
    vol_ratio = volume.iloc[-1] / volume.tail(20).mean()

    signals = []
    bull = bear = 0

    def add(text, direction, weight=1):
        nonlocal bull, bear
        signals.append((text, direction))
        if direction == 'bullish': bull += weight
        elif direction == 'bearish': bear += weight

    add(f"Price ${current:.2f} vs MA20 ${ma20:.2f}", "bullish" if current > ma20 else "bearish")
    add(f"Price vs MA50 ${ma50:.2f}", "bullish" if current > ma50 else "bearish")
    if ma200:
        add(f"Price vs MA200 ${ma200:.2f}", "bullish" if current > ma200 else "bearish")
        add("Golden Cross" if ma50 > ma200 else "Death Cross", "bullish" if ma50 > ma200 else "bearish")

    if rsi_val > 70: add(f"RSI {rsi_val:.1f} (overbought)", "bearish")
    elif rsi_val < 30: add(f"RSI {rsi_val:.1f} (oversold)", "bullish")
    elif rsi_val > 50: add(f"RSI {rsi_val:.1f} (bullish momentum)", "bullish")
    else: add(f"RSI {rsi_val:.1f} (bearish momentum)", "bearish")

    if macd_cross: add("MACD fresh bullish crossover 🔔", "bullish", weight=2)
    elif macd_bullish: add("MACD above signal line", "bullish")
    else: add("MACD below signal line", "bearish")

    add(f"ADX {adx_val:.1f} ({'strong trend' if adx_val > 25 else 'weak trend'})", "neutral")

    if vol_ratio > 1.5: add(f"Volume {vol_ratio:.1f}x avg (high interest)", "bullish")
    elif vol_ratio < 0.5: add(f"Volume {vol_ratio:.1f}x avg (low interest)", "bearish")

    if bb_pos > 100: add("Price above upper Bollinger", "bearish")
    elif bb_pos < 0: add("Price below lower Bollinger", "bullish")

    tech_score = ((bull - bear) / max(bull + bear, 1)) * 100
    combined = (mom_score + tech_score) / 2
    agreement = (mom_score > 0 and tech_score > 0) or (mom_score < 0 and tech_score < 0)

    if combined > 50 and agreement: verdict = "STRONG BUY"
    elif combined > 20 and agreement: verdict = "BUY"
    elif combined < -50 and agreement: verdict = "STRONG SELL"
    elif combined < -20 and agreement: verdict = "SELL"
    elif not agreement and abs(combined) > 10: verdict = "MIXED SIGNALS"
    else: verdict = "NEUTRAL"

    high_52w = close.tail(252).max()
    low_52w = close.tail(252).min()

    return {
        'current': current, 'returns': returns,
        'mom_score': mom_score, 'tech_score': tech_score,
        'combined': combined, 'verdict': verdict, 'agreement': agreement,
        'ma20': ma20, 'ma50': ma50, 'ma200': ma200,
        'rsi': rsi_val, 'adx': adx_val, 'bb_pos': bb_pos, 'vol_ratio': vol_ratio,
        'macd_cross': macd_cross, 'signals': signals,
        'bb_upper': bb_upper, 'bb_mid': bb_mid, 'bb_lower': bb_lower,
        'macd_line': macd_line, 'signal_line': signal_line,
        'pct_from_high': (current - high_52w) / high_52w * 100,
        'pct_from_low': (current - low_52w) / low_52w * 100,
    }


def create_chart(df, a):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2],
                        subplot_titles=("Price + MAs + Bollinger", "RSI", "MACD"))

    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                  low=df['Low'], close=df['Close'],
                                  name='Price', showlegend=False,
                                  increasing_line_color='#00C853',
                                  decreasing_line_color='#FF3D57'), row=1, col=1)

    ma20 = df['Close'].rolling(20).mean()
    ma50 = df['Close'].rolling(50).mean()
    ma200 = df['Close'].rolling(200).mean()

    fig.add_trace(go.Scatter(x=df.index, y=ma20, name='MA20', line=dict(color='#F59E0B', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=ma50, name='MA50', line=dict(color='#3B82F6', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=ma200, name='MA200', line=dict(color='#EF4444', width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=a['bb_upper'], name='BB Upper',
                              line=dict(color='rgba(124,58,237,0.5)', width=1, dash='dot'), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=a['bb_lower'], name='BB Lower',
                              line=dict(color='rgba(124,58,237,0.5)', width=1, dash='dot'),
                              fill='tonexty', fillcolor='rgba(124,58,237,0.03)', showlegend=False), row=1, col=1)

    rsi_series = rsi(df['Close'])
    fig.add_trace(go.Scatter(x=df.index, y=rsi_series, name='RSI', line=dict(color='#7C3AED')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="rgba(255,61,87,0.5)", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="rgba(0,200,83,0.5)", row=2, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=a['macd_line'], name='MACD', line=dict(color='#3B82F6')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=a['signal_line'], name='Signal', line=dict(color='#F59E0B')), row=3, col=1)
    hist = a['macd_line'] - a['signal_line']
    fig.add_trace(go.Bar(x=df.index, y=hist, name='Histogram',
                          marker_color=['#00C853' if v > 0 else '#FF3D57' for v in hist],
                          showlegend=False), row=3, col=1)

    fig.update_layout(
        height=700,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        margin=dict(t=40, b=20),
        font=dict(color='#E2E8F0'),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
    )
    fig.update_xaxes(gridcolor='rgba(255,255,255,0.05)', showgrid=True)
    fig.update_yaxes(gridcolor='rgba(255,255,255,0.05)', showgrid=True)
    return fig


def screen_ticker(ticker):
    try:
        df = yf.download(ticker, period="1y", progress=False, auto_adjust=True, threads=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 252: return None
        close = df['Close']
        volume = df['Volume']
        current = close.iloc[-1]
        if current < 5 or volume.tail(20).mean() < 100_000: return None
        a = full_analysis(df)
        return {
            'ticker': ticker, 'price': current,
            'verdict': a['verdict'], 'combined': a['combined'],
            'mom_score': a['mom_score'], 'tech_score': a['tech_score'],
            'rsi': a['rsi'], 'ret_1m': a['returns'].get('1m', 0),
            'ret_3m': a['returns'].get('3m', 0), 'ret_12m': a['returns'].get('12m', 0),
            'macd_cross': a['macd_cross'], 'above_ma200': current > a['ma200'] if a['ma200'] else False,
        }
    except: return None


def compute_signals_bt(df):
    close = df['Close']
    volume = df['Volume']
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()
    rsi_val = rsi(close)
    macd_line, signal_line, _ = macd(close)
    bb_upper, _, bb_lower = bollinger(close)
    bb_pos = ((close - bb_lower) / (bb_upper - bb_lower)) * 100
    vol_ratio = volume / volume.rolling(20).mean()
    ret_1w = (close / close.shift(5) - 1) * 100
    ret_1m = (close / close.shift(21) - 1) * 100
    ret_3m = (close / close.shift(63) - 1) * 100
    ret_6m = (close / close.shift(126) - 1) * 100
    ret_12m = (close / close.shift(252) - 1) * 100
    mom_score = (np.clip(ret_1w*5,-100,100)*0.1 + np.clip(ret_1m*5,-100,100)*0.2 +
                 np.clip(ret_3m*5,-100,100)*0.3 + np.clip(ret_6m*5,-100,100)*0.2 +
                 np.clip(ret_12m*5,-100,100)*0.2)
    bull = ((close > ma20).astype(int) + (close > ma50).astype(int) +
            (close > ma200).astype(int) + (ma50 > ma200).astype(int) +
            ((rsi_val > 50) & (rsi_val <= 70)).astype(int) + (rsi_val < 30).astype(int) +
            (macd_line > signal_line).astype(int) + (vol_ratio > 1.5).astype(int) + (bb_pos < 0).astype(int))
    bear = ((close <= ma20).astype(int) + (close <= ma50).astype(int) +
            (close <= ma200).astype(int) + (ma50 <= ma200).astype(int) +
            (rsi_val > 70).astype(int) + ((rsi_val <= 50) & (rsi_val >= 30)).astype(int) +
            (macd_line <= signal_line).astype(int) + (vol_ratio < 0.5).astype(int) + (bb_pos > 100).astype(int))
    tech_score = ((bull - bear) / (bull + bear).replace(0, 1)) * 100
    combined = (mom_score + tech_score) / 2
    agreement = ((mom_score > 0) & (tech_score > 0)) | ((mom_score < 0) & (tech_score < 0))
    signal = pd.Series('NEUTRAL', index=close.index)
    signal[(combined > 50) & agreement] = 'STRONG_BUY'
    signal[(combined > 20) & (combined <= 50) & agreement] = 'BUY'
    return pd.DataFrame({'close': close, 'combined': combined, 'signal': signal})


def run_backtest(df, target_pct=10, horizon=60):
    sig_df = compute_signals_bt(df)
    is_signal = sig_df['signal'].isin(['BUY', 'STRONG_BUY'])
    fresh = is_signal & ~is_signal.shift(1).fillna(False)
    signal_dates = sig_df.index[fresh]
    trades = []
    close = sig_df['close']
    for sig_date in signal_dates:
        idx = sig_df.index.get_loc(sig_date)
        if idx + 1 >= len(close): continue
        entry = close.iloc[idx + 1]
        end_idx = min(idx + 1 + horizon, len(close) - 1)
        future = close.iloc[idx+1:end_idx+1]
        max_gain = ((future.max() - entry) / entry) * 100
        final = ((future.iloc[-1] - entry) / entry) * 100
        trades.append({'date': sig_date, 'max_gain': max_gain, 'final_ret': final, 'hit_target': max_gain >= target_pct})
    if not trades: return None
    df_t = pd.DataFrame(trades)
    baseline_rets, baseline_hits = [], 0
    for i in range(len(close) - horizon - 1):
        entry = close.iloc[i+1]
        future = close.iloc[i+1:i+1+horizon]
        ret = (future.iloc[-1] - entry) / entry * 100
        max_g = (future.max() - entry) / entry * 100
        baseline_rets.append(ret)
        if max_g >= target_pct: baseline_hits += 1
    return {
        'n_trades': len(trades),
        'win_rate': df_t['hit_target'].mean() * 100,
        'avg_return': df_t['final_ret'].mean(),
        'baseline_win_rate': baseline_hits / len(baseline_rets) * 100 if baseline_rets else 0,
        'baseline_avg': np.mean(baseline_rets) if baseline_rets else 0,
    }


# ============================================================
# MAIN DASHBOARD
# ============================================================
def show_entry_dashboard(user):
    inject_css()

    # Header
    st.markdown(f"""
    <div class="orion-header">
        <div class="orion-logo">🎯 Orion <span>Signals</span></div>
        <span class="plan-badge">Entry Plan</span>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown(f"**👤 {user['name']}**")
        st.markdown(f"*{user['email']}*")
        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

    # Tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Single Stock", "🎯 Screener", "📊 Backtest"])

    # ── TAB 1: SINGLE STOCK ──
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

                st.markdown("#### Returns")
                rcols = st.columns(len(a['returns']))
                for col, (tf, ret) in zip(rcols, a['returns'].items()):
                    col.metric(tf, f"{ret:+.2f}%")

                st.plotly_chart(create_chart(df, a), use_container_width=True)

                st.markdown("#### Signals")
                s1, s2 = st.columns(2)
                for i, (text, direction) in enumerate(a['signals']):
                    icon = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}[direction]
                    target = s1 if i % 2 == 0 else s2
                    target.write(f"{icon} {text}")

    # ── TAB 2: SCREENER ──
    with tab2:
        st.markdown("Σαρώνει universe μετοχών και βρίσκει τις πιο bullish.")
        col1, col2, col3 = st.columns(3)
        universe = col1.selectbox("Universe", ["dow", "nasdaq100", "sp500"],
                                   format_func=lambda x: {"dow": "Dow 30 (γρήγορο)",
                                                           "nasdaq100": "NASDAQ 100",
                                                           "sp500": "S&P 500 (αργό)"}[x])
        top_n = col2.number_input("Top N", min_value=5, max_value=20, value=10)
        min_score = col3.number_input("Min Score", min_value=-100, max_value=100, value=20)

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
                    st.download_button("📥 Download CSV", csv, "signals.csv", "text/csv")

    # ── TAB 3: BACKTEST ──
    with tab3:
        st.markdown("Δοκίμασε αν η στρατηγική έχει edge πάνω από random entry.")
        st.info("⚠️ Entry plan: έως 1 χρόνο ιστορικό. Αναβάθμισε σε Pro για 10 χρόνια.")

        col1, col2, col3 = st.columns(3)
        bt_ticker = col1.text_input("Ticker", value="AAPL", key="bt").upper()
        bt_target = col2.number_input("Target %", min_value=1, max_value=50, value=10)
        bt_horizon = col3.number_input("Horizon (days)", min_value=5, max_value=252, value=60)

        if st.button("📊 Run Backtest", use_container_width=True):
            with st.spinner(f"Backtesting {bt_ticker}..."):
                df = load_data(bt_ticker, period="1y")  # Entry: 1 χρόνο μόνο
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
                        c4.metric("Baseline Win Rate", f"{result['baseline_win_rate']:.1f}%")

                        edge_wr = result['win_rate'] - result['baseline_win_rate']
                        edge_ret = result['avg_return'] - result['baseline_avg']

                        if edge_wr > 5 and edge_ret > 1:
                            st.success("✅ Η στρατηγική έχει θετικό edge")
                        elif edge_wr > 0:
                            st.warning("🟡 Οριακό edge")
                        else:
                            st.error("❌ Δεν υπάρχει edge")

    st.markdown("---")
    st.caption("⚠️ Educational tool only. Not financial advice.")
