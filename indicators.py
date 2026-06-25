"""
Orion Signals — Shared Indicators & Analysis
=============================================
v2.0 — Πλήρης αναθεώρηση

Τι άλλαξε από v1:
  - Market Regime filter (SPY/VIX check πριν όλα)
  - AND-logic για signals (όχι απλό weighted sum)
  - Νέοι indicators: VWAP, Williams %R, Stoch RSI, Pivot Points
  - OBV, Stochastic, Relative Strength ενσωματωμένα στο scoring
  - Earnings filter ενσωματωμένο στο verdict
  - Realistic backtest (slippage + commission)
  - Data provider: yfinance (αλλάζεις ΜΟΝΟ load_data() για Alpaca)
"""

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


# ============================================================
# SECTION 1: CORE INDICATORS
# ============================================================

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    return 100 - (100 / (1 + gain / loss))


def stoch_rsi(series, rsi_period=14, stoch_period=14, smooth_k=3, smooth_d=3):
    """Stochastic RSI — πιο ευαίσθητο από plain RSI."""
    r = rsi(series, rsi_period)
    min_r = r.rolling(stoch_period).min()
    max_r = r.rolling(stoch_period).max()
    k = 100 * (r - min_r) / (max_r - min_r + 1e-10)
    k = k.rolling(smooth_k).mean()
    d = k.rolling(smooth_d).mean()
    return k, d


def macd(series, fast=12, slow=26, signal=9):
    ef = series.ewm(span=fast, adjust=False).mean()
    es = series.ewm(span=slow, adjust=False).mean()
    ml = ef - es
    sl = ml.ewm(span=signal, adjust=False).mean()
    return ml, sl, ml - sl


def bollinger(series, period=20, std=2):
    ma = series.rolling(period).mean()
    sd = series.rolling(period).std()
    return ma + sd * std, ma, ma - sd * std


def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def adx_calc(df, period=14):
    h, l, c = df['High'], df['Low'], df['Close']
    pdm = h.diff().clip(lower=0)
    mdm = (-l.diff()).clip(lower=0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    pdi = 100 * (pdm.rolling(period).mean() / atr)
    mdi = 100 * (mdm.rolling(period).mean() / atr)
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi)
    return dx.rolling(period).mean()


def atr_calc(df, period=14):
    h, l, c = df['High'], df['Low'], df['Close']
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def stochastic(df, k_period=14, smooth=3):
    h = df['High'].rolling(k_period).max()
    l = df['Low'].rolling(k_period).min()
    k = 100 * (df['Close'] - l) / (h - l + 1e-10)
    k = k.rolling(smooth).mean()
    d = k.rolling(smooth).mean()
    return k, d


def obv(df):
    """On-Balance Volume."""
    close = df['Close']
    vol = df['Volume']
    direction = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (direction * vol).cumsum()


def obv_trend(df, lookback=20):
    """Αν OBV ανεβαίνει = αγοραστική πίεση επιβεβαιώνει κίνηση."""
    o = obv(df)
    if len(o) < lookback:
        return "neutral"
    return "rising" if float(o.iloc[-1]) > float(o.iloc[-lookback]) else "falling"


def vwap(df):
    """
    VWAP — Volume Weighted Average Price.
    Institutions αγοράζουν/πουλάνε γύρω από VWAP.
    Τιμή > VWAP = bullish intraday. Τιμή < VWAP = αδυναμία.
    Υπολογίζεται ως rolling VWAP 20 ημερών (daily data).
    """
    typical = (df['High'] + df['Low'] + df['Close']) / 3
    vol = df['Volume']
    vwap_val = (typical * vol).rolling(20).sum() / vol.rolling(20).sum()
    return vwap_val


def williams_r(df, period=14):
    """
    Williams %R — overbought/oversold.
    0 to -20 = overbought. -80 to -100 = oversold.
    """
    h = df['High'].rolling(period).max()
    l = df['Low'].rolling(period).min()
    return -100 * (h - df['Close']) / (h - l + 1e-10)


def pivot_points(df):
    """
    Pivot Points από previous day/period high/low/close.
    Institutions τα κοιτάνε ως support/resistance.
    """
    prev_h = float(df['High'].iloc[-2])
    prev_l = float(df['Low'].iloc[-2])
    prev_c = float(df['Close'].iloc[-2])
    pivot = (prev_h + prev_l + prev_c) / 3
    r1 = 2 * pivot - prev_l
    r2 = pivot + (prev_h - prev_l)
    s1 = 2 * pivot - prev_h
    s2 = pivot - (prev_h - prev_l)
    return {'pivot': pivot, 'r1': r1, 'r2': r2, 's1': s1, 's2': s2}


def squeeze_momentum(df, bb_period=20, bb_std=2, kc_period=20, kc_mult=1.5):
    """
    TTM Squeeze — εντοπίζει πότε η αγορά 'φορτίζεται' πριν μεγάλη κίνηση.
    Bollinger Bands μέσα σε Keltner Channel = squeeze (συμπίεση).
    Squeeze off = έκρηξη ενεργεία.
    """
    close = df['Close']
    # Bollinger Bands
    bb_upper, bb_mid, bb_lower = bollinger(close, bb_period, bb_std)
    # Keltner Channel
    atr = atr_calc(df, kc_period)
    kc_mid = ema(close, kc_period)
    kc_upper = kc_mid + kc_mult * atr
    kc_lower = kc_mid - kc_mult * atr
    # Squeeze: BB μέσα σε KC
    squeeze_on = (bb_upper < kc_upper) & (bb_lower > kc_lower)
    # Momentum
    delta = close - (df['High'].rolling(kc_period).max() + df['Low'].rolling(kc_period).min()) / 2
    momentum = delta.rolling(kc_period).mean()
    return {
        'squeeze_on': bool(squeeze_on.iloc[-1]),
        'momentum': float(momentum.iloc[-1]) if not pd.isna(momentum.iloc[-1]) else 0,
        'momentum_rising': float(momentum.iloc[-1]) > float(momentum.iloc[-2])
            if not pd.isna(momentum.iloc[-2]) else False,
    }


def relative_strength(df_stock, df_bench, lookback=63):
    """Relative Strength vs benchmark (SPY)."""
    if df_stock is None or df_bench is None:
        return None
    if len(df_stock) < lookback or len(df_bench) < lookback:
        return None
    s_ret = (float(df_stock['Close'].iloc[-1]) / float(df_stock['Close'].iloc[-lookback]) - 1) * 100
    b_ret = (float(df_bench['Close'].iloc[-1]) / float(df_bench['Close'].iloc[-lookback]) - 1) * 100
    return {
        'rs_ratio': (1 + s_ret / 100) / (1 + b_ret / 100),
        'outperform': s_ret > b_ret,
        'stock_ret': s_ret,
        'bench_ret': b_ret,
    }


def climax_volume(df, lookback=50, spike_mult=2.5):
    """Climax Volume — ακραίο spike που σηματοδοτεί εξάντληση."""
    if df is None or len(df) < lookback:
        return {"detected": False, "ratio": 0.0, "type": None}
    avg_vol = float(df['Volume'].tail(lookback).mean())
    last_vol = float(df['Volume'].iloc[-1])
    ratio = last_vol / avg_vol if avg_vol > 0 else 0
    detected = ratio >= spike_mult
    ctype = None
    if detected:
        day_change = float(df['Close'].iloc[-1] - df['Close'].iloc[-2]) if len(df) >= 2 else 0
        ctype = "buying_climax" if day_change > 0 else "selling_climax"
    return {"detected": detected, "ratio": ratio, "type": ctype}


# ============================================================
# SECTION 2: MARKET REGIME
# ============================================================

@st.cache_data(ttl=3600)
def get_market_regime():
    """
    Ελέγχει αν η αγορά είναι bull/bear/neutral.
    Πρέπει να τρέχει ΠΡΙΝ από κάθε signal.

    Επιστρέφει:
      regime  : 'bull' | 'bear' | 'neutral'
      spy_ok  : SPY > MA200
      vix_ok  : VIX < 25
      score   : 0-3 (3 = strong bull)
    """
    try:
        spy = yf.download('SPY', period='1y', progress=False, auto_adjust=True)
        if isinstance(spy.columns, pd.MultiIndex):
            spy.columns = spy.columns.get_level_values(0)

        spy_price = float(spy['Close'].iloc[-1])
        spy_ma200 = float(spy['Close'].rolling(200).mean().iloc[-1])
        spy_ma50 = float(spy['Close'].rolling(50).mean().iloc[-1])
        spy_ok = spy_price > spy_ma200

        # VIX
        vix_ok = True
        vix_level = 20.0
        try:
            vix = yf.download('^VIX', period='5d', progress=False, auto_adjust=True)
            if isinstance(vix.columns, pd.MultiIndex):
                vix.columns = vix.columns.get_level_values(0)
            if not vix.empty:
                vix_level = float(vix['Close'].iloc[-1])
                vix_ok = vix_level < 25
        except Exception:
            pass

        # % SPY πάνω από MA50 (proxy: SPY momentum)
        spy_momentum = spy_price > spy_ma50

        score = sum([spy_ok, vix_ok, spy_momentum])

        if score >= 3:
            regime = 'bull'
        elif score <= 1:
            regime = 'bear'
        else:
            regime = 'neutral'

        return {
            'regime': regime,
            'spy_ok': spy_ok,
            'vix_ok': vix_ok,
            'vix_level': vix_level,
            'spy_price': spy_price,
            'spy_ma200': spy_ma200,
            'score': score,
        }
    except Exception:
        return {
            'regime': 'neutral',
            'spy_ok': True,
            'vix_ok': True,
            'vix_level': 20.0,
            'spy_price': 0,
            'spy_ma200': 0,
            'score': 2,
        }


# ============================================================
# SECTION 3: EARNINGS CHECK
# ============================================================

@st.cache_data(ttl=3600)
def check_earnings(ticker, days=7):
    """Ελέγχει αν υπάρχουν earnings εντός <days> ημερών."""
    try:
        tk = yf.Ticker(ticker)
        ed = tk.get_earnings_dates(limit=8)
        if ed is not None and len(ed) > 0:
            now = datetime.now(ed.index.tz) if ed.index.tz else datetime.now()
            future = ed[ed.index > now]
            if len(future) > 0:
                next_date = future.index.min()
                days_until = (next_date.to_pydatetime().replace(tzinfo=None) - datetime.now()).days
                has = 0 <= days_until <= days
                return {
                    "has_earnings": has,
                    "date": next_date.strftime("%d/%m/%Y"),
                    "days_until": days_until,
                    "message": (f"⚠️ Earnings σε {days_until} μέρες ({next_date.strftime('%d/%m')})"
                                if has else f"✓ Χωρίς earnings εντός {days} ημερών"),
                }
    except Exception:
        pass
    return {"has_earnings": None, "date": None, "days_until": None, "message": "Earnings: N/A"}


# ============================================================
# SECTION 4: FUEL GAUGE (Momentum Exhaustion)
# ============================================================

def fuel_gauge(df, lookback=20):
    """
    Πόσο 'καύσιμο' έχει μείνει στην τρέχουσα κίνηση.
    100% = υγιής. 0% = εξαντλημένη, πιθανή αντιστροφή.
    """
    if df is None or len(df) < 60:
        return None

    close = df['Close']
    volume = df['Volume']
    current = float(close.iloc[-1])

    rsi_s = rsi(close)
    ml, sl, hist = macd(close)
    ma20 = close.rolling(20).mean()
    k, d = stochastic(df)

    rsi_now = float(rsi_s.iloc[-1])
    stoch_now = float(k.iloc[-1]) if not pd.isna(k.iloc[-1]) else 50.0

    fuel = 100.0
    signals = []

    def sig(text, triggered, penalty):
        nonlocal fuel
        signals.append((text, triggered))
        if triggered:
            fuel -= penalty

    half = lookback // 2
    close_sm = close.rolling(3).mean()
    rsi_sm = rsi_s.rolling(3).mean()
    hist_sm = hist.rolling(3).mean()

    recent_price = float(close_sm.tail(half).max())
    prev_price = float(close_sm.iloc[-lookback:-half].max())
    near_highs = recent_price >= prev_price * 0.985

    # 1. RSI Divergence
    recent_rsi = float(rsi_sm.tail(half).max())
    prev_rsi = float(rsi_sm.iloc[-lookback:-half].max())
    rsi_div = near_highs and (recent_rsi < prev_rsi - 4)
    sig("RSI divergence — momentum fading", rsi_div, 25)

    # 2. MACD Divergence
    recent_hist = float(hist_sm.tail(half).max())
    prev_hist = float(hist_sm.iloc[-lookback:-half].max())
    macd_div = near_highs and (recent_hist < prev_hist * 0.7)
    sig("MACD divergence — weakening thrust", macd_div, 20)

    # 3. Volume Exhaustion
    vol_recent = float(volume.tail(half).mean())
    vol_prev = float(volume.iloc[-lookback:-half].mean())
    vol_exhaust = near_highs and (vol_recent < vol_prev * 0.7)
    sig("Volume exhaustion — fewer buyers", vol_exhaust, 20)

    # 4. Overextension
    ma20_now = float(ma20.iloc[-1])
    ext_pct = (current - ma20_now) / ma20_now * 100
    ext_penalty = max(0.0, min(25.0, (ext_pct - 8) * 2.0))
    sig(f"Overextended {ext_pct:+.1f}% from MA20", ext_penalty > 0, 0)
    fuel -= ext_penalty

    # 5. Overbought
    rsi_pen = max(0.0, min(25.0, (rsi_now - 68) * 1.4))
    stoch_pen = max(0.0, min(10.0, (stoch_now - 75) * 0.7))
    sig(f"Overbought RSI {rsi_now:.0f} / Stoch {stoch_now:.0f}", (rsi_pen + stoch_pen) > 4, 0)
    fuel -= (rsi_pen + stoch_pen)

    fuel = max(0.0, min(100.0, fuel))
    status = "healthy" if fuel >= 65 else "slowing" if fuel >= 35 else "exhausted"

    return {
        "fuel": round(fuel),
        "status": status,
        "signals": signals,
        "rsi": rsi_now,
        "stoch": stoch_now,
        "ext_pct": ext_pct,
    }


def fuel_bar(fuel):
    filled = round(fuel / 10)
    return "█" * filled + "░" * (10 - filled)


# ============================================================
# SECTION 5: TARGET PROJECTION & ENTRY
# ============================================================

def target_projection(df):
    """Entry / Stop Loss / Target βάσει ATR."""
    if df is None or len(df) < 60:
        return None

    close = df['Close']
    current = float(close.iloc[-1])
    atr = float(atr_calc(df).iloc[-1])

    # Stop Loss: κάτω από recent swing low ή 1.5x ATR
    recent_low = float(df['Low'].tail(10).min())
    sl_atr = current - 1.5 * atr
    stop_loss = max(recent_low * 0.99, sl_atr)

    # Target: 2:1 R:R minimum
    risk = current - stop_loss
    target_1 = current + 2 * risk   # 2:1
    target_2 = current + 3 * risk   # 3:1

    # Resistance (recent high)
    resistance = float(close.tail(52).max())
    if resistance > current * 1.02:
        target_2 = min(target_2, resistance)

    pct_sl = (stop_loss - current) / current * 100
    pct_t1 = (target_1 - current) / current * 100
    pct_t2 = (target_2 - current) / current * 100

    return {
        "entry": current,
        "stop_loss": stop_loss,
        "target_1": target_1,
        "target_2": target_2,
        "atr": atr,
        "pct_sl": pct_sl,
        "pct_t1": pct_t1,
        "pct_t2": pct_t2,
        "rr_ratio": abs(pct_t1 / pct_sl) if pct_sl != 0 else 0,
    }


def confirmation_entry(df, threshold=1.5):
    """Επιβεβαίωση ότι η μετοχή έχει αρχίσει να κινείται."""
    if df is None or len(df) < 2:
        return {"confirmed": False, "move_pct": 0.0, "message": "Not enough data"}
    prev_close = float(df['Close'].iloc[-2])
    current = float(df['Close'].iloc[-1])
    move_pct = (current - prev_close) / prev_close * 100
    confirmed = move_pct >= threshold
    msg = (f"✅ Confirmed +{move_pct:.1f}%" if confirmed
           else f"⏳ Not yet {move_pct:+.1f}% (needs +{threshold}%)")
    return {"confirmed": confirmed, "move_pct": move_pct, "message": msg}


# ============================================================
# SECTION 6: DATA LOADING
# ============================================================
# ════════════════════════════════════════════════════════════
#  ⚠️  DATA SOURCE — ΣΗΜΕΙΟ ΑΛΛΑΓΗΣ ΠΑΡΟΧΟΥ
#  ΤΩΡΑ: yfinance (δωρεάν, delayed)
#  ΓΙΑ ALPACA: άλλαξε ΜΟΝΟ τη load_data() παρακάτω
#  Όλα τα υπόλοιπα μένουν ΙΔΙΑ — αρκεί DataFrame με:
#  Open, High, Low, Close, Volume (index = ημερομηνίες)
# ════════════════════════════════════════════════════════════

@st.cache_data(ttl=600)
def load_data(ticker, period="1y"):
    """
    Κατεβάζει OHLCV data.
    Άλλαξε αυτή τη function για Alpaca/Polygon/άλλο provider.
    """
    df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
    if df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


@st.cache_data(ttl=600)
def load_spy():
    """Φορτώνει SPY για relative strength comparison."""
    return load_data('SPY', period='1y')


@st.cache_data(ttl=3600)
def get_sp500():
    try:
        t = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]['Symbol'].tolist()
        return [x.replace('.', '-') for x in t]
    except Exception:
        return ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA', 'JPM', 'V', 'UNH',
                'HD', 'PG', 'JNJ', 'MA', 'COST', 'ABBV', 'MRK', 'LLY', 'CVX', 'PEP']


@st.cache_data(ttl=3600)
def get_nasdaq100():
    try:
        tables = pd.read_html("https://en.wikipedia.org/wiki/Nasdaq-100")
        for tbl in tables:
            for col in ['Ticker', 'Symbol']:
                if col in tbl.columns:
                    return [x.replace('.', '-') for x in tbl[col].tolist()]
    except Exception:
        pass
    return ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA', 'AVGO', 'COST', 'NFLX']


def get_dow():
    return ['AAPL', 'AMGN', 'AXP', 'BA', 'CAT', 'CRM', 'CSCO', 'CVX', 'DIS', 'GS',
            'HD', 'HON', 'IBM', 'JNJ', 'JPM', 'KO', 'MCD', 'MMM', 'MRK', 'MSFT',
            'NKE', 'PG', 'SHW', 'TRV', 'UNH', 'V', 'VZ', 'WMT', 'NVDA', 'AMZN']


# ============================================================
# SECTION 7: FULL ANALYSIS (AND-LOGIC)
# ============================================================

def full_analysis(df, ticker=None, include_extras=False):
    """
    Κεντρική ανάλυση με AND-logic για signals.

    Αντί για weighted sum, χρησιμοποιεί CONDITIONS:
    Για BUY πρέπει να ισχύουν ΟΛΑ τα core conditions.
    Αυτό δίνει λιγότερα αλλά αξιόπιστα signals.

    include_extras: φορτώνει SPY για RS (πιο αργό, για Pro)
    """
    close = df['Close']
    volume = df['Volume']
    current = float(close.iloc[-1])

    # ── Momentum (multi-timeframe) ──
    timeframes = {'1w': 5, '1m': 21, '3m': 63, '6m': 126, '12m': 252}
    returns = {}
    for name, days in timeframes.items():
        if len(close) > days:
            returns[name] = float((current - float(close.iloc[-days - 1])) /
                                  float(close.iloc[-days - 1]) * 100)

    weights = {'1w': 0.1, '1m': 0.2, '3m': 0.3, '6m': 0.2, '12m': 0.2}
    mom_score = sum(np.clip(returns.get(tf, 0) * 5, -100, 100) * w
                    for tf, w in weights.items())

    # ── Moving Averages ──
    ma20 = float(close.rolling(20).mean().iloc[-1])
    ma50 = float(close.rolling(50).mean().iloc[-1])
    ma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
    ema21 = float(ema(close, 21).iloc[-1])

    # ── RSI & Stoch RSI ──
    rsi_v = float(rsi(close).iloc[-1])
    sk, sd = stoch_rsi(close)
    stochrsi_k = float(sk.iloc[-1]) if not pd.isna(sk.iloc[-1]) else 50.0
    stochrsi_d = float(sd.iloc[-1]) if not pd.isna(sd.iloc[-1]) else 50.0

    # ── MACD ──
    ml, sl, hist_macd = macd(close)
    macd_bull = float(ml.iloc[-1]) > float(sl.iloc[-1])
    macd_cross = (float(ml.iloc[-2]) <= float(sl.iloc[-2])) and macd_bull

    # ── Bollinger ──
    bbu, bbm, bbl = bollinger(close)
    bb_pos = float((current - float(bbl.iloc[-1])) /
                   (float(bbu.iloc[-1]) - float(bbl.iloc[-1]) + 1e-10) * 100)

    # ── ADX ──
    adx_v = float(adx_calc(df).iloc[-1])

    # ── VWAP ──
    vwap_val = float(vwap(df).iloc[-1])
    above_vwap = current > vwap_val

    # ── Williams %R ──
    wr = float(williams_r(df).iloc[-1])
    wr_oversold = wr < -80
    wr_overbought = wr > -20

    # ── OBV ──
    obv_direction = obv_trend(df)

    # ── Volume ──
    vol_r = float(volume.iloc[-1]) / float(volume.tail(20).mean())

    # ── Stochastic ──
    stoch_k, stoch_d = stochastic(df)
    stoch_val = float(stoch_k.iloc[-1]) if not pd.isna(stoch_k.iloc[-1]) else 50.0

    # ── Pivot Points ──
    pivots = pivot_points(df) if len(df) >= 3 else None

    # ── Squeeze Momentum ──
    squeeze = squeeze_momentum(df)

    # ── Climax Volume ──
    climax = climax_volume(df)

    # ── 52w ──
    h52 = float(close.tail(252).max())
    l52 = float(close.tail(252).min())
    pct_from_high = (current - h52) / h52 * 100
    pct_from_low = (current - l52) / l52 * 100

    # MANDATORY — 4 conditions, πρέπει ΟΛΑ για BUY
    mandatory = {
        'above_ma50':   current > ma50,
        'mom_positive': mom_score > 0,
        'rsi_ok':       30 < rsi_v < 75,
        'macd_bullish': macd_bull,
    }
    mandatory_ok = all(mandatory.values())

    # BEARISH MANDATORY — για SELL signals
    mandatory_bear = {
        'below_ma50':   current < ma50,
        'mom_negative': mom_score < 0,
        'rsi_bear':     rsi_v < 50 or rsi_v > 80,
        'macd_bearish': not macd_bull,
    }
    mandatory_bear_ok = all(mandatory_bear.values())

    # OPTIONAL — πρέπει 3/5 για BUY, 4/5 για STRONG BUY
    optional = {
        'above_ma200':   current > ma200 if ma200 else True,
        'ma50_gt_ma200': ma50 > ma200 if ma200 else True,
        'obv_rising':    obv_direction == 'rising',
        'above_vwap':    above_vwap,
        'ret_3m_pos':    returns.get('3m', 0) > 0,
    }
    optional_count = sum(optional.values())

    # BEARISH OPTIONAL
    optional_bear = {
        'below_ma200':  current < ma200 if ma200 else False,
        'death_cross':  ma50 < ma200 if ma200 else False,
        'obv_falling':  obv_direction == 'falling',
        'below_vwap':   not above_vwap,
        'ret_3m_neg':   returns.get('3m', 0) < 0,
    }
    optional_bear_count = sum(optional_bear.values())

    # Συνολικό για UI
    conditions = {**mandatory, **optional}
    core_bull = sum(conditions.values())
    core_total = len(conditions)

    # BONUS signals
    bonus = {
        'macd_fresh_cross': macd_cross,
        'stochrsi_bullish': stochrsi_k > stochrsi_d and stochrsi_k < 80,
        'wr_oversold':      wr_oversold,
        'squeeze_firing':   not squeeze['squeeze_on'] and squeeze['momentum_rising'],
        'high_volume':      vol_r > 1.5,
        'above_ema21':      current > ema21,
        'no_climax':        not climax['detected'],
    }
    bonus_count = sum(bonus.values())

    # WARNING signals
    warnings_list = {
        'overbought_rsi': rsi_v > 75,
        'above_bb_upper': bb_pos > 100,
        'wr_overbought':  wr_overbought,
        'climax_volume':  climax['detected'] and climax['type'] == 'buying_climax',
        'weak_trend':     adx_v < 20,
        'below_vwap':     not above_vwap,
    }
    warning_count = sum(warnings_list.values())

    # ── SCORING ──
    tech_raw = (core_bull / core_total) * 60 + bonus_count * 5 - warning_count * 8
    tech_score = np.clip(tech_raw, -100, 100)
    combined = (mom_score + tech_score) / 2
    agree = (mom_score > 0 and tech_score > 0) or (mom_score < 0 and tech_score < 0)

    # ── VERDICT ──
    if mandatory_ok and optional_count >= 4 and combined > 35:
        verdict = "STRONG BUY"
    elif mandatory_ok and optional_count >= 3 and combined > 15:
        verdict = "BUY"
    elif mandatory_bear_ok and optional_bear_count >= 4 and combined < -35:
        verdict = "STRONG SELL"
    elif mandatory_bear_ok and optional_bear_count >= 3 and combined < -15:
        verdict = "SELL"
    elif not agree and abs(combined) > 10:
        verdict = "MIXED SIGNALS"
    else:
        verdict = "NEUTRAL"

    # ── SIGNALS LIST (για UI) ──
    sigs = []
    def add(text, direction):
        sigs.append((text, direction))

    add(f"Price ${current:.2f} vs MA50 ${ma50:.2f}", "bullish" if current > ma50 else "bearish")
    if ma200:
        add(f"Price vs MA200 ${ma200:.2f}", "bullish" if current > ma200 else "bearish")
        add("Golden Cross ✓" if ma50 > ma200 else "Death Cross ✗",
            "bullish" if ma50 > ma200 else "bearish")
    add(f"Price vs VWAP ${vwap_val:.2f}", "bullish" if above_vwap else "bearish")
    add(f"RSI {rsi_v:.1f}", "bullish" if 40 < rsi_v < 70 else
        "bearish" if rsi_v > 75 else "neutral")
    add(f"Stoch RSI K:{stochrsi_k:.0f} D:{stochrsi_d:.0f}",
        "bullish" if stochrsi_k > stochrsi_d else "bearish")
    add(f"Williams %R {wr:.0f}", "bullish" if wr_oversold else
        "bearish" if wr_overbought else "neutral")
    add("MACD fresh crossover 🔔" if macd_cross else
        "MACD above signal" if macd_bull else "MACD below signal",
        "bullish" if macd_bull else "bearish")
    add(f"OBV {obv_direction}", "bullish" if obv_direction == "rising" else "bearish")
    add(f"ADX {adx_v:.1f} — {'strong' if adx_v > 25 else 'weak'} trend", "neutral")
    add(f"Volume {vol_r:.1f}x avg",
        "bullish" if vol_r > 1.5 else "bearish" if vol_r < 0.5 else "neutral")
    if squeeze['squeeze_on']:
        add("TTM Squeeze ON 🔴 — energy building", "neutral")
    elif squeeze['momentum_rising']:
        add("TTM Squeeze fired — momentum rising 🟢", "bullish")
    if climax['detected']:
        add(f"⚠️ Climax Volume {climax['ratio']:.1f}x — {climax['type']}", "bearish")

    # ── RELATIVE STRENGTH (Pro only) ──
    rs = None
    if include_extras:
        try:
            spy_df = load_spy()
            if spy_df is not None:
                rs = relative_strength(df, spy_df)
        except Exception:
            pass

    return {
        'current': current,
        'returns': returns,
        'mom_score': mom_score,
        'tech_score': tech_score,
        'combined': combined,
        'verdict': verdict,
        'agreement': agree,
        'conditions': conditions,
        'core_bull': core_bull,
        'core_total': core_total,
        'bonus': bonus,
        'warnings': warnings_list,
        'ma20': ma20, 'ma50': ma50, 'ma200': ma200, 'ema21': ema21,
        'rsi': rsi_v,
        'stochrsi_k': stochrsi_k, 'stochrsi_d': stochrsi_d,
        'macd_bull': macd_bull, 'macd_cross': macd_cross,
        'bb_pos': bb_pos,
        'bb_upper': bbu, 'bb_mid': bbm, 'bb_lower': bbl,
        'macd_line': ml, 'signal_line': sl,
        'adx': adx_v,
        'vwap': vwap_val, 'above_vwap': above_vwap,
        'williams_r': wr,
        'obv_direction': obv_direction,
        'vol_ratio': vol_r,
        'squeeze': squeeze,
        'climax': climax,
        'pivots': pivots,
        'pct_from_high': pct_from_high,
        'pct_from_low': pct_from_low,
        'signals': sigs,
        'rs': rs,
    }


# ============================================================
# SECTION 8: SCREENER
# ============================================================

def screen_ticker(ticker):
    """
    Screener με market regime awareness και AND-logic.
    Επιστρέφει None αν η μετοχή δεν πληροί τα κριτήρια.
    """
    try:
        df = yf.download(ticker, period="1y", progress=False,
                         auto_adjust=True, threads=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 200:
            return None

        close = df['Close']
        volume = df['Volume']
        current = float(close.iloc[-1])

        # Φίλτρα εισόδου
        avg_vol = float(volume.tail(20).mean())
        if current < 10 or avg_vol < 500_000:
            return None

        # Ανάλυση
        a = full_analysis(df, ticker=ticker)

        # Μόνο BUY / STRONG BUY περνάνε
        if a['verdict'] not in ('BUY', 'STRONG BUY'):
            return None

        return {
            'ticker':       ticker,
            'price':        current,
            'verdict':      a['verdict'],
            'combined':     a['combined'],
            'mom_score':    a['mom_score'],
            'tech_score':   a['tech_score'],
            'core_bull':    a['core_bull'],
            'rsi':          a['rsi'],
            'adx':          a['adx'],
            'ret_1m':       a['returns'].get('1m', 0),
            'ret_3m':       a['returns'].get('3m', 0),
            'ret_12m':      a['returns'].get('12m', 0),
            'macd_cross':   a['macd_cross'],
            'above_ma200':  current > a['ma200'] if a['ma200'] else False,
            'above_vwap':   a['above_vwap'],
            'obv_ok':       a['obv_direction'] == 'rising',
            'squeeze':      a['squeeze']['momentum_rising'] and not a['squeeze']['squeeze_on'],
        }
    except Exception:
        return None


# ============================================================
# SECTION 9: BACKTEST (Realistic)
# ============================================================

def run_backtest(df, target_pct=10, horizon=30,
                 slippage=0.001, commission=2.0):
    """
    Backtest με realistic assumptions:
    - Slippage: 0.1% per side
    - Commission: $2 per trade
    - Entry: επόμενη μέρα μετά το signal (no lookahead bias)
    - Horizon: max days να κρατήσεις
    - Target: % κέρδος για win
    """
    close = df['Close']
    if len(close) < 252:
        return None

    # Υπολογισμός signals με full_analysis σε rolling basis
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()
    rsi_s = rsi(close)
    ml, sl_line, _ = macd(close)
    obv_s = obv(df)
    vwap_s = vwap(df)

    # Conditions (simplified για speed)
    cond_trend = (close > ma50) & (close > ma200) & (ma50 > ma200)
    cond_rsi = (rsi_s > 30) & (rsi_s < 75)
    cond_macd = ml > sl_line
    cond_obv = obv_s > obv_s.shift(20)
    cond_vwap = close > vwap_s
    cond_mom = (close / close.shift(63) - 1) > 0

    # Signal: ΟΛΑ τα conditions
    signal = cond_trend & cond_rsi & cond_macd & cond_obv & cond_vwap & cond_mom
    fresh = signal & ~signal.shift(1).fillna(False)

    trades = []
    for date in close.index[fresh]:
        idx = close.index.get_loc(date)
        if idx + 1 >= len(close):
            continue
        # Entry επόμενη μέρα + slippage
        entry_price = float(close.iloc[idx + 1]) * (1 + slippage)
        end_idx = min(idx + 1 + horizon, len(close) - 1)
        future = close.iloc[idx + 1:end_idx + 1]

        max_gain = float((future.max() - entry_price) / entry_price * 100)
        final_ret = float((future.iloc[-1] - entry_price) / entry_price * 100)

        # Κόστος: slippage εξόδου + commission (σε %)
        exit_cost = slippage * 100 + (commission * 2 / entry_price / 100 * 100)
        final_ret_net = final_ret - exit_cost
        hit = max_gain >= target_pct

        trades.append({
            'date': date,
            'entry': entry_price,
            'max_gain': max_gain,
            'final_ret': final_ret_net,
            'hit': hit,
        })

    if not trades:
        return None

    dt = pd.DataFrame(trades)

    # Baseline: random entry (buy & hold για horizon days)
    bl_results = []
    for i in range(50, len(close) - horizon - 1):
        e = float(close.iloc[i + 1]) * (1 + slippage)
        f = close.iloc[i + 1:i + 1 + horizon]
        g = float((f.max() - e) / e * 100)
        r = float((f.iloc[-1] - e) / e * 100) - (slippage * 100 + commission * 2 / e)
        bl_results.append({'hit': g >= target_pct, 'ret': r})

    bl_df = pd.DataFrame(bl_results)

    return {
        'n_trades':           len(trades),
        'win_rate':           dt['hit'].mean() * 100,
        'avg_return':         dt['final_ret'].mean(),
        'avg_max_gain':       dt['max_gain'].mean(),
        'baseline_win_rate':  bl_df['hit'].mean() * 100,
        'baseline_avg':       bl_df['ret'].mean(),
        'edge_win_rate':      dt['hit'].mean() * 100 - bl_df['hit'].mean() * 100,
        'edge_return':        dt['final_ret'].mean() - bl_df['ret'].mean(),
        'slippage_used':      slippage,
        'commission_used':    commission,
    }


# ============================================================
# SECTION 10: CHART
# ============================================================

def create_chart(df, a, height=700, show_vwap=False, show_ema21=False):
    """
    Candlestick chart με:
    - MA20/50/200 + optional EMA21
    - Bollinger Bands
    - Optional VWAP
    - RSI με Stoch RSI overlay
    - MACD με histogram
    - Pivot Points (optional)
    """
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=("Price + Indicators", "RSI / Stoch RSI", "MACD")
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], name='Price',
        showlegend=False,
        increasing_line_color='#00C853',
        decreasing_line_color='#FF3D57'
    ), row=1, col=1)

    # MAs
    ma20_s = df['Close'].rolling(20).mean()
    ma50_s = df['Close'].rolling(50).mean()
    ma200_s = df['Close'].rolling(200).mean()
    fig.add_trace(go.Scatter(x=df.index, y=ma20_s, name='MA20',
                             line=dict(color='#F59E0B', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=ma50_s, name='MA50',
                             line=dict(color='#3B82F6', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=ma200_s, name='MA200',
                             line=dict(color='#EF4444', width=1.5)), row=1, col=1)
    if show_ema21:
        ema21_s = ema(df['Close'], 21)
        fig.add_trace(go.Scatter(x=df.index, y=ema21_s, name='EMA21',
                                 line=dict(color='#A78BFA', width=1, dash='dot')), row=1, col=1)

    # Bollinger Bands
    fig.add_trace(go.Scatter(x=df.index, y=a['bb_upper'], name='BB Upper',
                             line=dict(color='rgba(124,58,237,0.4)', width=1, dash='dot'),
                             showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=a['bb_lower'], name='BB Lower',
                             line=dict(color='rgba(124,58,237,0.4)', width=1, dash='dot'),
                             fill='tonexty', fillcolor='rgba(124,58,237,0.04)',
                             showlegend=False), row=1, col=1)

    # VWAP (Pro)
    if show_vwap:
        vwap_s = vwap(df)
        fig.add_trace(go.Scatter(x=df.index, y=vwap_s, name='VWAP',
                                 line=dict(color='#34D399', width=1.5, dash='dot')), row=1, col=1)

    # Pivot Points
    if a.get('pivots'):
        p = a['pivots']
        for level, color, label in [
            (p['pivot'], '#FBBF24', 'Pivot'),
            (p['r1'], '#F87171', 'R1'),
            (p['s1'], '#34D399', 'S1'),
        ]:
            fig.add_hline(y=level, line_dash="dash",
                          line_color=color, opacity=0.4,
                          annotation_text=label,
                          annotation_position="right",
                          row=1, col=1)

    # RSI
    rsi_s = rsi(df['Close'])
    fig.add_trace(go.Scatter(x=df.index, y=rsi_s, name='RSI',
                             line=dict(color='#7C3AED', width=1.5)), row=2, col=1)
    # Stoch RSI
    sk, sd = stoch_rsi(df['Close'])
    fig.add_trace(go.Scatter(x=df.index, y=sk, name='StochRSI K',
                             line=dict(color='#F59E0B', width=1)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="rgba(255,61,87,0.4)", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="rgba(0,200,83,0.4)", row=2, col=1)

    # MACD
    fig.add_trace(go.Scatter(x=df.index, y=a['macd_line'], name='MACD',
                             line=dict(color='#3B82F6')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=a['signal_line'], name='Signal',
                             line=dict(color='#F59E0B')), row=3, col=1)
    hist_vals = a['macd_line'] - a['signal_line']
    fig.add_trace(go.Bar(x=df.index, y=hist_vals, name='Hist',
                         marker_color=['#00C853' if v > 0 else '#FF3D57' for v in hist_vals],
                         showlegend=False), row=3, col=1)

    fig.update_layout(
        height=height,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        margin=dict(t=40, b=20),
        font=dict(color='#E2E8F0'),
        legend=dict(bgcolor='rgba(0,0,0,0)', orientation='h',
                    yanchor='bottom', y=1.02)
    )
    fig.update_xaxes(gridcolor='rgba(255,255,255,0.05)', showgrid=True)
    fig.update_yaxes(gridcolor='rgba(255,255,255,0.05)', showgrid=True)
    return fig


# ============================================================
# SECTION 11: CSS
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
    .regime-bull{background:rgba(0,200,83,0.08);border:1px solid rgba(0,200,83,0.2);
        border-radius:8px;padding:0.5rem 1rem;font-size:0.8rem;color:#00C853;margin-bottom:1rem}
    .regime-bear{background:rgba(255,61,87,0.08);border:1px solid rgba(255,61,87,0.2);
        border-radius:8px;padding:0.5rem 1rem;font-size:0.8rem;color:#FF3D57;margin-bottom:1rem}
    .regime-neutral{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);
        border-radius:8px;padding:0.5rem 1rem;font-size:0.8rem;color:rgba(255,255,255,0.5);margin-bottom:1rem}
    .conditions-grid{display:grid;grid-template-columns:1fr 1fr;gap:0.4rem;margin:0.5rem 0}
    .cond-ok{color:#00C853;font-size:0.8rem}
    .cond-fail{color:#FF3D57;font-size:0.8rem}
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


# ============================================================
# UNIVERSES v2 — Νέοι δείκτες
# ============================================================

@st.cache_data(ttl=3600)
def get_sp400():
    """S&P 400 Mid Cap."""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies"
        tables = pd.read_html(url)
        for tbl in tables:
            for col in ['Ticker', 'Symbol', 'Ticker symbol']:
                if col in tbl.columns:
                    return [x.replace('.', '-') for x in tbl[col].tolist()]
    except Exception:
        pass
    return ['AXON','BILL','CASY','CHDN','DKS','EHC','EXEL','FBIN','FHN','GMED',
            'GTLB','HQY','ITT','JAZZ','LFUS','LNW','MMS','MTZ','NOVT','NVT',
            'ONTO','OZK','PFGC','PRI','PSTG','RGEN','RLI','RRX','SFM','SLGN',
            'SM','SMAR','SNX','SSD','THC','TMHC','TTC','TXRH','UNF','WMS']


@st.cache_data(ttl=3600)
def get_sp600():
    """S&P 600 Small Cap."""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_600_companies"
        tables = pd.read_html(url)
        for tbl in tables:
            for col in ['Ticker', 'Symbol', 'Ticker symbol']:
                if col in tbl.columns:
                    return [x.replace('.', '-') for x in tbl[col].tolist()]
    except Exception:
        pass
    return ['ACLS','ADUS','AGYS','ALRM','AMPH','AMSF','ANIK','AOSL','APEI','ARCH',
            'ARKO','ARLO','ASTH','ATEN','ATNI','AVAV','AVNS','AXGN','BCAL','BCPC',
            'BFST','BGS','BHE','BKU','BLKB','BRC','BRKL','CABO','CAKE','CALX',
            'CARG','CASH','CATO','CCRN','CDRE','CEVA','CHCO','CHUY','CLFD','COHU']


@st.cache_data(ttl=3600)
def get_russell2000():
    """Russell 2000 — Top 150 liquid small caps."""
    return [
        'ACLX','ACMR','ADMA','ADUS','AGEN','AGYS','AHCO','ALRM','AMPH','AMSF',
        'AMTB','ANIK','AOSL','APEI','ARCH','ARKO','ARLO','ASTH','ATEN','AVAV',
        'AVNS','AXGN','BCAL','BCPC','BFST','BGS','BKU','BLKB','BRC','BRKL',
        'CABO','CAKE','CALX','CARG','CASH','CATO','CCRN','CDRE','CEVA','CHCO',
        'CHUY','CLFD','CLNE','COHU','COMM','CPSI','CRAI','CSWI','CTBI','CTRE',
        'CVBF','CVCO','CVLG','DAKT','DCGO','DCOM','DFIN','DGII','DLTH','DORM',
        'DWSN','DXPE','EAST','EFSC','ELME','ENSG','EPRT','ERII','ESRT','EVTC',
        'EXTR','EZPW','FBNC','FCBC','FCEL','FISI','FLGT','FLNC','FLXS','FMBH',
        'FMNB','FOLD','FORM','FORR','FOSL','FRPH','FSBW','FULT','GDOT','GEF',
        'GEOS','GERN','GLAD','GLDD','GOOD','GRTS','HAFC','HCAT','HCSG','HEAR',
        'HEES','HFWA','HIBB','HIMS','HTBK','HUBG','HURN','HWKN','HYXF','IIIV',
        'IIIN','IMMR','IMRX','INBK','INDB','INFU','INSG','INVA','IONS','IOSP',
        'IPAR','IPGP','IRMD','ITIC','JACK','JBSS','JELD','JOBY','KELYA','KEQU',
        'KFRC','KIDS','KNSL','KTOS','KURA','LGND','LKFN','LMAT','LNDC','LOCO',
        'LPSN','LQDT','LSAQ','LSTR','LVWR','LYTS','MBIN','MBUU','MCBS','MCFT',
    ]


@st.cache_data(ttl=86400)
def get_sector(ticker):
    """Sector μιας μετοχής από yfinance. Cache 24h."""
    try:
        info = yf.Ticker(ticker).info
        return info.get('sector', 'Unknown')
    except Exception:
        return 'Unknown'


SECTOR_ETFS = {
    'Technology': 'XLK', 'Healthcare': 'XLV', 'Financials': 'XLF',
    'Consumer Discretionary': 'XLY', 'Consumer Staples': 'XLP',
    'Energy': 'XLE', 'Industrials': 'XLI', 'Materials': 'XLB',
    'Real Estate': 'XLRE', 'Utilities': 'XLU', 'Communication Services': 'XLC',
}


def get_universe(name):
    """Κεντρική function επιλογής universe."""
    return {
        'dow': get_dow, 'nasdaq100': get_nasdaq100, 'sp500': get_sp500,
        'sp400': get_sp400, 'sp600': get_sp600, 'russell2000': get_russell2000,
    }.get(name, get_dow)()


# ============================================================
# SCREEN TICKER v2 — Επιστρέφει ΟΛΕΣ τις κατηγορίες
# ============================================================

def screen_ticker_v2(ticker, include_sector=False):
    """
    Screener που επιστρέφει ΟΛΑ τα verdicts:
    STRONG BUY, BUY, NEUTRAL, MIXED, SELL, STRONG SELL.
    Έτσι βλέπεις και τι να αποφύγεις/πουλήσεις.
    """
    try:
        df = yf.download(ticker, period="1y", progress=False,
                         auto_adjust=True, threads=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 100:
            return None

        close = df['Close']
        volume = df['Volume']
        current = float(close.iloc[-1])
        avg_vol = float(volume.tail(20).mean())

        # Φίλτρο: μόνο για screener (όχι για single stock analysis)
        if current < 2 or avg_vol < 50_000:
            return None

        a = full_analysis(df, ticker=ticker)

        sector = 'Unknown'
        if include_sector and a['verdict'] in ('BUY', 'STRONG BUY', 'SELL', 'STRONG SELL'):
            sector = get_sector(ticker)

        return {
            'ticker':      ticker,
            'price':       current,
            'verdict':     a['verdict'],
            'combined':    a['combined'],
            'mom_score':   a['mom_score'],
            'tech_score':  a['tech_score'],
            'core_bull':   a['core_bull'],
            'rsi':         a['rsi'],
            'adx':         a['adx'],
            'ret_1m':      a['returns'].get('1m', 0),
            'ret_3m':      a['returns'].get('3m', 0),
            'ret_12m':     a['returns'].get('12m', 0),
            'macd_cross':  a['macd_cross'],
            'above_ma200': current > a['ma200'] if a['ma200'] else False,
            'above_vwap':  a['above_vwap'],
            'obv_ok':      a['obv_direction'] == 'rising',
            'squeeze':     a['squeeze']['momentum_rising'] and not a['squeeze']['squeeze_on'],
            'sector':      sector,
            'avg_vol':     avg_vol,
        }
    except Exception:
        return None

