"""
Stock Momentum & Technical Analysis Tool
-----------------------------------------
Δίνεις ένα ticker (π.χ. AAPL, MSFT, TSLA) και βγάζει:
- Momentum score (πολλαπλά χρονικά πλαίσια)
- Technical indicators (RSI, MACD, MA, Bollinger Bands, ADX, Volume)
- Τελική κρίση: συμφωνεί η τεχνική ανάλυση με το momentum;

Εγκατάσταση:
    pip install yfinance pandas numpy pandas-ta

Χρήση:
    python stock_analyzer.py AAPL
    python stock_analyzer.py MSFT TSLA NVDA   # πολλαπλά
"""

import sys
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import yfinance as yf


# ============================================================
# DATA FETCHING
# ============================================================

def fetch_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Κατεβάζει ιστορικά OHLCV δεδομένα."""
    df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
    if df.empty:
        raise ValueError(f"Δεν βρέθηκαν δεδομένα για {ticker}")
    # Flatten columns αν είναι MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


# ============================================================
# MOMENTUM ANALYSIS
# ============================================================

def momentum_analysis(df: pd.DataFrame) -> dict:
    """Υπολογίζει momentum σε πολλαπλά χρονικά πλαίσια."""
    close = df['Close']
    current = close.iloc[-1]

    timeframes = {
        '1_week':   5,
        '1_month':  21,
        '3_month':  63,
        '6_month':  126,
        '12_month': 252,
    }

    returns = {}
    for name, days in timeframes.items():
        if len(close) > days:
            past = close.iloc[-days-1]
            returns[name] = ((current - past) / past) * 100

    # 12-1 momentum (classic academic factor: 12 month return εξαιρώντας τον τελευταίο μήνα)
    if len(close) > 252:
        ret_12m = ((close.iloc[-22] - close.iloc[-252]) / close.iloc[-252]) * 100
        returns['12_1_momentum'] = ret_12m

    # Momentum score (-100 to +100)
    score = 0
    weights = {'1_week': 0.1, '1_month': 0.2, '3_month': 0.3,
               '6_month': 0.2, '12_month': 0.2}
    for tf, weight in weights.items():
        if tf in returns:
            # Καθένα κανονικοποιείται: +20% return -> +100 score
            score += np.clip(returns[tf] * 5, -100, 100) * weight

    return {'returns': returns, 'score': score}


# ============================================================
# TECHNICAL INDICATORS
# ============================================================

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(series: pd.Series, period: int = 20, std: float = 2):
    ma = series.rolling(period).mean()
    sd = series.rolling(period).std()
    upper = ma + (sd * std)
    lower = ma - (sd * std)
    return upper, ma, lower


def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average Directional Index - μετράει την ισχύ της τάσης."""
    high, low, close = df['High'], df['Low'], df['Close']
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    return dx.rolling(period).mean()


def technical_analysis(df: pd.DataFrame) -> dict:
    """Συγκεντρωτική τεχνική ανάλυση."""
    close = df['Close']
    volume = df['Volume']
    current = close.iloc[-1]

    # Moving Averages
    ma_20 = close.rolling(20).mean().iloc[-1]
    ma_50 = close.rolling(50).mean().iloc[-1]
    ma_200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None

    # RSI
    rsi_val = rsi(close).iloc[-1]

    # MACD
    macd_line, signal_line, hist = macd(close)
    macd_bullish = macd_line.iloc[-1] > signal_line.iloc[-1]
    macd_crossover = (macd_line.iloc[-2] <= signal_line.iloc[-2]) and macd_bullish

    # Bollinger Bands
    bb_upper, bb_mid, bb_lower = bollinger_bands(close)
    bb_position = ((current - bb_lower.iloc[-1]) /
                   (bb_upper.iloc[-1] - bb_lower.iloc[-1])) * 100

    # ADX
    adx_val = adx(df).iloc[-1]

    # Volume trend
    vol_avg_20 = volume.rolling(20).mean().iloc[-1]
    vol_current = volume.iloc[-1]
    vol_ratio = vol_current / vol_avg_20

    # 52-week high/low proximity
    high_52w = close.tail(252).max() if len(close) >= 252 else close.max()
    low_52w = close.tail(252).min() if len(close) >= 252 else close.min()
    pct_from_high = ((current - high_52w) / high_52w) * 100
    pct_from_low = ((current - low_52w) / low_52w) * 100

    # === Bullish/Bearish signals scoring ===
    signals = []
    bull_count = 0
    bear_count = 0

    # Price vs MAs
    if current > ma_20:
        signals.append(("Price > MA20", "bullish"));  bull_count += 1
    else:
        signals.append(("Price < MA20", "bearish"));  bear_count += 1

    if current > ma_50:
        signals.append(("Price > MA50", "bullish"));  bull_count += 1
    else:
        signals.append(("Price < MA50", "bearish"));  bear_count += 1

    if ma_200 is not None:
        if current > ma_200:
            signals.append(("Price > MA200 (long-term uptrend)", "bullish")); bull_count += 1
        else:
            signals.append(("Price < MA200 (long-term downtrend)", "bearish")); bear_count += 1

    # Golden/Death cross
    if ma_200 is not None:
        if ma_50 > ma_200:
            signals.append(("MA50 > MA200 (Golden Cross territory)", "bullish")); bull_count += 1
        else:
            signals.append(("MA50 < MA200 (Death Cross territory)", "bearish")); bear_count += 1

    # RSI
    if rsi_val > 70:
        signals.append((f"RSI={rsi_val:.1f} (overbought)", "bearish")); bear_count += 1
    elif rsi_val < 30:
        signals.append((f"RSI={rsi_val:.1f} (oversold - potential bounce)", "bullish")); bull_count += 1
    elif 50 < rsi_val <= 70:
        signals.append((f"RSI={rsi_val:.1f} (bullish momentum)", "bullish")); bull_count += 1
    else:
        signals.append((f"RSI={rsi_val:.1f} (bearish momentum)", "bearish")); bear_count += 1

    # MACD
    if macd_crossover:
        signals.append(("MACD bullish crossover (fresh)", "bullish")); bull_count += 2
    elif macd_bullish:
        signals.append(("MACD above signal line", "bullish")); bull_count += 1
    else:
        signals.append(("MACD below signal line", "bearish")); bear_count += 1

    # ADX (trend strength)
    if adx_val > 25:
        signals.append((f"ADX={adx_val:.1f} (strong trend)", "neutral"))
    else:
        signals.append((f"ADX={adx_val:.1f} (weak/no trend)", "neutral"))

    # Volume
    if vol_ratio > 1.5:
        signals.append((f"Volume {vol_ratio:.1f}x average (high interest)", "bullish")); bull_count += 1
    elif vol_ratio < 0.5:
        signals.append((f"Volume {vol_ratio:.1f}x average (low interest)", "bearish")); bear_count += 1

    # Bollinger position
    if bb_position > 100:
        signals.append(("Price above upper Bollinger (extended)", "bearish")); bear_count += 1
    elif bb_position < 0:
        signals.append(("Price below lower Bollinger (oversold)", "bullish")); bull_count += 1

    technical_score = ((bull_count - bear_count) / max(bull_count + bear_count, 1)) * 100

    return {
        'current_price': current,
        'ma_20': ma_20, 'ma_50': ma_50, 'ma_200': ma_200,
        'rsi': rsi_val,
        'macd_bullish': macd_bullish,
        'macd_crossover': macd_crossover,
        'bb_position': bb_position,
        'adx': adx_val,
        'volume_ratio': vol_ratio,
        'pct_from_52w_high': pct_from_high,
        'pct_from_52w_low': pct_from_low,
        'signals': signals,
        'bull_count': bull_count,
        'bear_count': bear_count,
        'score': technical_score,
    }


# ============================================================
# FINAL VERDICT
# ============================================================

def verdict(mom_score: float, tech_score: float) -> tuple:
    """Συνδυάζει momentum + technical για τελική κρίση."""
    combined = (mom_score + tech_score) / 2
    agreement = (mom_score > 0 and tech_score > 0) or (mom_score < 0 and tech_score < 0)

    if combined > 50 and agreement:
        rating = "STRONG BUY"
    elif combined > 20 and agreement:
        rating = "BUY"
    elif combined < -50 and agreement:
        rating = "STRONG SELL"
    elif combined < -20 and agreement:
        rating = "SELL / AVOID"
    elif not agreement:
        rating = "MIXED SIGNALS (caution)"
    else:
        rating = "NEUTRAL"

    return rating, combined, agreement


# ============================================================
# REPORTING
# ============================================================

def analyze(ticker: str):
    ticker = ticker.upper()
    print(f"\n{'='*60}")
    print(f"  ANALYSIS: {ticker}")
    print(f"{'='*60}")

    try:
        df = fetch_data(ticker)
    except Exception as e:
        print(f"Σφάλμα: {e}")
        return

    mom = momentum_analysis(df)
    tech = technical_analysis(df)

    # --- MOMENTUM ---
    print(f"\n📈 MOMENTUM")
    print(f"  Current price: ${tech['current_price']:.2f}")
    print(f"  Distance from 52w high: {tech['pct_from_52w_high']:+.1f}%")
    print(f"  Distance from 52w low:  {tech['pct_from_52w_low']:+.1f}%")
    print(f"\n  Returns:")
    for tf, ret in mom['returns'].items():
        emoji = "🟢" if ret > 0 else "🔴"
        print(f"    {emoji} {tf:>15s}: {ret:+6.2f}%")
    print(f"\n  Momentum Score: {mom['score']:+.1f} / 100")

    # --- TECHNICAL ---
    print(f"\n📊 TECHNICAL INDICATORS")
    print(f"  MA20:  ${tech['ma_20']:.2f}")
    print(f"  MA50:  ${tech['ma_50']:.2f}")
    if tech['ma_200']:
        print(f"  MA200: ${tech['ma_200']:.2f}")
    print(f"  RSI:   {tech['rsi']:.1f}")
    print(f"  ADX:   {tech['adx']:.1f}")
    print(f"  Bollinger position: {tech['bb_position']:.0f}%  (0=lower band, 100=upper band)")
    print(f"  Volume vs 20d avg:  {tech['volume_ratio']:.2f}x")

    print(f"\n  Signals:")
    for sig, direction in tech['signals']:
        icon = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}[direction]
        print(f"    {icon} {sig}")

    print(f"\n  Technical Score: {tech['score']:+.1f} / 100")
    print(f"  ({tech['bull_count']} bullish vs {tech['bear_count']} bearish signals)")

    # --- VERDICT ---
    rating, combined, agreement = verdict(mom['score'], tech['score'])
    print(f"\n{'─'*60}")
    print(f"  🎯 VERDICT: {rating}")
    print(f"  Combined score: {combined:+.1f} / 100")
    print(f"  Momentum & Technical agreement: {'✅ YES' if agreement else '⚠️  NO'}")
    print(f"{'─'*60}")
    print(f"\n⚠️  Educational tool only. Not financial advice.")
    print(f"   Technical analysis has limited predictive power.\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python stock_analyzer.py TICKER [TICKER2 ...]")
        print("Example: python stock_analyzer.py AAPL MSFT NVDA")
        sys.exit(1)

    for ticker in sys.argv[1:]:
        analyze(ticker)


if __name__ == "__main__":
    main()
