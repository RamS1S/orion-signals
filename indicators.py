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

def stochastic(df, k_period=5, smooth=3):
    """Stochastic %K and %D (fast stochastic, default 5,3,3)."""
    h = df['High'].rolling(k_period).max()
    l = df['Low'].rolling(k_period).min()
    k = 100 * (df['Close'] - l) / (h - l)
    k = k.rolling(smooth).mean()
    d = k.rolling(smooth).mean()
    return k, d


# ============================================================
# FUEL GAUGE — Momentum Exhaustion Detector
# ============================================================
# Provider-agnostic: δέχεται μόνο ένα OHLCV DataFrame.
# Δεν ξέρει αν ήρθε από yfinance, Polygon, Alpaca κλπ.
# Επιστρέφει 0-100% "καύσιμο" + αναλυτικά σήματα.
# 100% = υγιής κίνηση με δύναμη. 0% = εξαντλημένη, πιθανή αντιστροφή.

def fuel_gauge(df, lookback=20):
    """
    Υπολογίζει πόσο 'καύσιμο' έχει μείνει στην τρέχουσα κίνηση.

    5 σήματα εξάντλησης (όλα από OHLCV):
      1. RSI Divergence      — τιμή ↑ αλλά RSI ↓
      2. MACD Divergence     — τιμή ↑ αλλά MACD histogram ↓
      3. Volume Exhaustion   — άνοδος με λιγότερο όγκο
      4. Overextension       — τιμή πολύ μακριά από MA20
      5. Overbought          — RSI > 70 + Stochastic > 80

    Επιστρέφει dict:
      fuel        : 0-100 (100 = γεμάτο, υγιές)
      status      : healthy | slowing | exhausted
      signals     : λίστα (text, triggered) για κάθε σήμα
    """
    if df is None or len(df) < 60:
        return None

    close  = df['Close']
    volume = df['Volume']
    current = float(close.iloc[-1])

    # Indicators
    rsi_s = rsi(close)
    ml, sl, hist = macd(close)
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    k, d = stochastic(df)

    rsi_now   = float(rsi_s.iloc[-1])
    stoch_now = float(k.iloc[-1]) if not pd.isna(k.iloc[-1]) else 50.0

    # ── Penalty system: ξεκινάμε 100, αφαιρούμε ──
    fuel = 100.0
    signals = []

    def sig(text, triggered, penalty):
        nonlocal fuel
        signals.append((text, triggered))
        if triggered:
            fuel -= penalty

    half = lookback // 2

    # Smoothed peaks (αποφεύγουμε θόρυβο μονής μέρας)
    close_sm = close.rolling(3).mean()
    rsi_sm   = rsi_s.rolling(3).mean()
    hist_sm  = hist.rolling(3).mean()

    recent_price = float(close_sm.tail(half).max())
    prev_price   = float(close_sm.iloc[-lookback:-half].max())
    # "Κοντά στο high" = η τιμή κρατιέται ψηλά (δεν χρειάζεται ΝΕΟ high)
    near_highs = recent_price >= prev_price * 0.985

    # 1. RSI DIVERGENCE — τιμή κρατάει ψηλά, RSI σαφώς χαμηλότερο
    recent_rsi = float(rsi_sm.tail(half).max())
    prev_rsi   = float(rsi_sm.iloc[-lookback:-half].max())
    rsi_div = near_highs and (recent_rsi < prev_rsi - 4)
    sig("RSI divergence — price holds, momentum fading", rsi_div, 25)

    # 2. MACD DIVERGENCE — τιμή ψηλά, histogram σαφώς χαμηλότερο
    recent_hist = float(hist_sm.tail(half).max())
    prev_hist   = float(hist_sm.iloc[-lookback:-half].max())
    macd_div = near_highs and (recent_hist < prev_hist * 0.7)
    sig("MACD divergence — weakening thrust", macd_div, 20)

    # 3. VOLUME EXHAUSTION — κίνηση κρατιέται με σαφώς λιγότερο όγκο
    vol_recent = float(volume.tail(half).mean())
    vol_prev   = float(volume.iloc[-lookback:-half].mean())
    vol_exhaust = near_highs and (vol_recent < vol_prev * 0.7)
    sig("Volume exhaustion — fewer buyers behind move", vol_exhaust, 20)

    # 4. OVEREXTENSION — κλιμακωτή ποινή όσο απομακρύνεται από MA20
    ma20_now = float(ma20.iloc[-1])
    ext_pct = (current - ma20_now) / ma20_now * 100
    # 0 penalty κάτω από 8%, μέχρι 25 penalty στο 20%+
    ext_penalty = max(0.0, min(25.0, (ext_pct - 8) * 2.0))
    sig(f"Overextended — {ext_pct:+.1f}% from MA20", ext_penalty > 0, 0)
    fuel -= ext_penalty

    # 5. OVERBOUGHT — κλιμακωτή ποινή (RSI + Stochastic)
    # RSI: ξεκινάει στο 68. Πάνω από 80 = ακραίο, βαραίνει πολύ.
    rsi_pen   = max(0.0, min(25.0, (rsi_now - 68) * 1.4))
    stoch_pen = max(0.0, min(10.0, (stoch_now - 75) * 0.7))
    ob_penalty = rsi_pen + stoch_pen
    sig(f"Overbought — RSI {rsi_now:.0f}, Stoch {stoch_now:.0f}", ob_penalty > 4, 0)
    fuel -= ob_penalty

    fuel = max(0.0, min(100.0, fuel))

    if fuel >= 65:
        status = "healthy"
    elif fuel >= 35:
        status = "slowing"
    else:
        status = "exhausted"

    return {
        "fuel":       round(fuel),
        "status":     status,
        "signals":    signals,
        "rsi":        rsi_now,
        "stoch":      stoch_now,
        "ext_pct":    ext_pct,
    }


def fuel_bar(fuel):
    """Επιστρέφει visual bar string για το fuel level."""
    filled = round(fuel / 10)
    return "█" * filled + "░" * (10 - filled)


# ============================================================
# CONFIRMATION ENTRY (+1.5%)
# ============================================================
def confirmation_entry(df, threshold=1.5):
    """
    Ελέγχει αν η μετοχή έχει 'επιβεβαιώσει' την κίνηση.
    Logic: έχει ανέβει >= threshold% από το προηγούμενο close
    (δηλαδή ξεκίνησε όντως να κινείται — όχι πρόωρη είσοδος).

    Επιστρέφει dict:
      confirmed : True/False
      move_pct  : πόσο έχει κινηθεί
      message   : κείμενο για UI
    """
    if df is None or len(df) < 2:
        return {"confirmed": False, "move_pct": 0.0, "message": "Not enough data"}

    prev_close = float(df['Close'].iloc[-2])
    current    = float(df['Close'].iloc[-1])
    move_pct = (current - prev_close) / prev_close * 100

    confirmed = move_pct >= threshold
    if confirmed:
        msg = f"✅ Confirmed — moved +{move_pct:.1f}% (≥ {threshold}%)"
    elif move_pct > 0:
        msg = f"⏳ Not yet — only +{move_pct:.1f}% (needs +{threshold}%)"
    else:
        msg = f"⏳ Not confirmed — {move_pct:+.1f}%"
    return {"confirmed": confirmed, "move_pct": move_pct, "message": msg}


# ============================================================
# EARNINGS CHECK
# ============================================================
@st.cache_data(ttl=3600)
def check_earnings(ticker, days=7):
    """
    Ελέγχει αν υπάρχουν earnings στις επόμενες <days> μέρες.
    Defensive — το yfinance earnings API είναι ασταθές.

    Επιστρέφει dict:
      has_earnings : True/False/None (None = δεν βρέθηκε info)
      date         : ημερομηνία ή None
      days_until   : μέρες ή None
      message      : κείμενο για UI
    """
    from datetime import datetime, timedelta
    try:
        tk = yf.Ticker(ticker)
        cal = None
        # Δοκιμή 1: get_earnings_dates
        try:
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
                        "message": (f"⚠️ Earnings in {days_until} days ({next_date.strftime('%d/%m')})"
                                    if has else f"✓ No earnings within {days} days"),
                    }
        except Exception:
            pass
        return {"has_earnings": None, "date": None, "days_until": None,
                "message": "Earnings date unavailable"}
    except Exception:
        return {"has_earnings": None, "date": None, "days_until": None,
                "message": "Earnings date unavailable"}


# ============================================================
# TARGET PROJECTION
# ============================================================
def target_projection(df, analysis=None):
    """
    Εκτιμά ρεαλιστικό target ως ΕΥΡΟΣ (όχι ακριβές σημείο).
    Συνδυάζει 3 πηγές:
      1. ATR projection   — current + 3×ATR
      2. Resistance        — πρόσφατο high (52 ημερών)
      3. Statistical move  — τυπική θετική κίνηση βάσει volatility

    Επιστρέφει dict:
      low, high     : εύρος target τιμής
      pct_low, pct_high : % κίνηση
      note          : κείμενο
    Πάντα ως ESTIMATE — όχι πρόβλεψη-βεβαιότητα.
    """
    if df is None or len(df) < 60:
        return None

    close = df['Close']
    current = float(close.iloc[-1])
    atr = float(atr_calc(df).iloc[-1])

    # 1. ATR-based (3x ATR target)
    atr_target = current + 3 * atr

    # 2. Resistance (πρόσφατο high)
    recent_high = float(close.tail(52).max())
    # Αν ήδη κοντά/πάνω στο high, χρησιμοποίησε ATR
    resistance = recent_high if recent_high > current * 1.02 else atr_target

    # 3. Statistical (τυπική 20-ημερη θετική διακύμανση)
    daily_ret = close.pct_change().tail(60)
    upside_vol = float(daily_ret[daily_ret > 0].std()) if len(daily_ret[daily_ret > 0]) > 0 else 0.01
    stat_target = current * (1 + upside_vol * (20 ** 0.5) * 1.5)  # ~20 μέρες horizon

    # Συνδυασμός → εύρος
    targets = sorted([atr_target, resistance, stat_target])
    low  = targets[0]
    high = targets[-1]
    # Αν πολύ κοντά, δώσε λίγο εύρος
    if high - low < current * 0.02:
        high = low * 1.03

    pct_low  = (low - current) / current * 100
    pct_high = (high - current) / current * 100

    return {
        "low":      low,
        "high":     high,
        "pct_low":  pct_low,
        "pct_high": pct_high,
        "current":  current,
        "note":     "Estimate based on ATR + resistance + volatility. Not a guarantee.",
    }


# ============================================================
# DATA
# ============================================================
# ════════════════════════════════════════════════════════════
#  ⚠️  DATA SOURCE — ΣΗΜΕΙΟ ΑΛΛΑΓΗΣ ΠΑΡΟΧΟΥ
# ════════════════════════════════════════════════════════════
#  ΤΩΡΑ: Yahoo Finance (yfinance)
#  → 2 ενημερώσεις/μέρα (after-market + open), delayed data
#  → Δωρεάν, κατάλληλο για swing trading
#
#  ΓΙΑ LIVE / INTRADAY ΑΡΓΟΤΕΡΑ:
#  → Άλλαξε ΜΟΝΟ τη load_data() παρακάτω
#  → π.χ. Polygon.io / Alpaca / Finnhub / Tradier
#  → Όλα τα υπόλοιπα (fuel_gauge, picks, backtest, target)
#    μένουν ΙΔΙΑ — αρκεί να επιστρέφεις DataFrame με στήλες:
#    Open, High, Low, Close, Volume  (index = ημερομηνίες)
# ════════════════════════════════════════════════════════════
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
