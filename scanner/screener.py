"""
S&P 500 Stock Screener
-----------------------
Τρέχει την στρατηγική (momentum + technical) σε ολόκληρο τον S&P 500
(ή custom λίστα) και επιστρέφει τα top candidates της ημέρας.

Χρήση:
    pip install yfinance pandas numpy
    python screener.py                          # Top 20 από S&P 500
    python screener.py --top 30                 # Top 30
    python screener.py --universe nasdaq100     # NASDAQ 100 αντί S&P
    python screener.py --universe custom --tickers AAPL,MSFT,NVDA,GOOGL
    python screener.py --min-score 60           # Μόνο πολύ ισχυρά σήματα
    python screener.py --export results.csv     # Export σε CSV
    python screener.py --parallel 10            # 10 παράλληλα downloads

Universe options:
    sp500       - S&P 500 (default)
    nasdaq100   - NASDAQ 100
    dow         - Dow Jones 30
    custom      - Custom list (χρειάζεται --tickers)
"""

import sys
import time
import argparse
import warnings
warnings.filterwarnings('ignore')

from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import yfinance as yf


# ============================================================
# UNIVERSE FETCHING
# ============================================================

def get_sp500_tickers():
    """Παίρνει την τρέχουσα λίστα του S&P 500 από Wikipedia."""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        tickers = tables[0]['Symbol'].tolist()
        # Yahoo Finance χρησιμοποιεί '-' αντί '.'  (π.χ. BRK.B -> BRK-B)
        tickers = [t.replace('.', '-') for t in tickers]
        return tickers
    except Exception as e:
        print(f"⚠️  Αποτυχία fetch S&P 500 από Wikipedia: {e}")
        print("   Χρήση hardcoded fallback (top 50)...")
        # Fallback: top 50 by market cap (κατά προσέγγιση)
        return ['AAPL','MSFT','NVDA','GOOGL','GOOG','AMZN','META','TSLA','BRK-B','LLY',
                'AVGO','JPM','WMT','V','XOM','UNH','MA','PG','JNJ','HD',
                'COST','ORCL','ABBV','BAC','KO','NFLX','CVX','CRM','AMD','TMO',
                'PEP','ADBE','LIN','MCD','CSCO','ACN','ABT','MRK','WFC','DIS',
                'TXN','IBM','PM','INTU','GE','VZ','CAT','AMGN','ISRG','QCOM']


def get_nasdaq100_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        tables = pd.read_html(url)
        # Το σωστό table συνήθως έχει στήλη 'Ticker' ή 'Symbol'
        for tbl in tables:
            for col in ['Ticker', 'Symbol']:
                if col in tbl.columns:
                    return [t.replace('.', '-') for t in tbl[col].tolist()]
        raise ValueError("Δεν βρέθηκε column Ticker/Symbol")
    except Exception as e:
        print(f"⚠️  Αποτυχία fetch NASDAQ 100: {e}")
        return ['AAPL','MSFT','NVDA','GOOGL','GOOG','AMZN','META','TSLA','AVGO','COST',
                'NFLX','TMUS','ADBE','PEP','CSCO','AMD','LIN','INTU','QCOM','TXN']


def get_dow_tickers():
    return ['AAPL','AMGN','AXP','BA','CAT','CRM','CSCO','CVX','DIS','GS',
            'HD','HON','IBM','JNJ','JPM','KO','MCD','MMM','MRK','MSFT',
            'NKE','PG','SHW','TRV','UNH','V','VZ','WMT','NVDA','AMZN']


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
    return macd_line, signal_line


def bollinger(series, period=20, std=2):
    ma = series.rolling(period).mean()
    sd = series.rolling(period).std()
    return ma + sd*std, ma, ma - sd*std


def adx(df, period=14):
    high, low, close = df['High'], df['Low'], df['Close']
    plus_dm = high.diff().clip(lower=0)
    minus_dm = (-low.diff()).clip(lower=0)
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


# ============================================================
# ANALYSIS PER TICKER (returns single dict για ranking)
# ============================================================

def analyze_ticker(ticker: str) -> dict:
    """Επιστρέφει score summary για ένα ticker. None αν αποτύχει."""
    try:
        df = yf.download(ticker, period="1y", progress=False, auto_adjust=True,
                         threads=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if df.empty or len(df) < 252:
            return None

        close = df['Close']
        volume = df['Volume']
        current = close.iloc[-1]

        # Skip penny stocks / illiquid
        avg_volume = volume.tail(20).mean()
        if current < 5 or avg_volume < 100_000:
            return None

        # === MOMENTUM ===
        ret_1w  = (current / close.iloc[-6]  - 1) * 100 if len(close) > 6  else 0
        ret_1m  = (current / close.iloc[-22] - 1) * 100 if len(close) > 22 else 0
        ret_3m  = (current / close.iloc[-64] - 1) * 100 if len(close) > 64 else 0
        ret_6m  = (current / close.iloc[-127]- 1) * 100 if len(close) > 127 else 0
        ret_12m = (current / close.iloc[-253]- 1) * 100 if len(close) > 253 else 0

        mom_score = (
            np.clip(ret_1w * 5, -100, 100) * 0.1 +
            np.clip(ret_1m * 5, -100, 100) * 0.2 +
            np.clip(ret_3m * 5, -100, 100) * 0.3 +
            np.clip(ret_6m * 5, -100, 100) * 0.2 +
            np.clip(ret_12m * 5, -100, 100) * 0.2
        )

        # === TECHNICAL ===
        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]
        ma200 = close.rolling(200).mean().iloc[-1]

        rsi_val = rsi(close).iloc[-1]
        macd_line, signal_line = macd(close)
        macd_bullish = macd_line.iloc[-1] > signal_line.iloc[-1]
        macd_fresh_cross = (macd_line.iloc[-2] <= signal_line.iloc[-2]) and macd_bullish

        bb_upper, _, bb_lower = bollinger(close)
        bb_pos = ((current - bb_lower.iloc[-1]) /
                  (bb_upper.iloc[-1] - bb_lower.iloc[-1])) * 100

        adx_val = adx(df).iloc[-1]
        vol_ratio = volume.iloc[-1] / volume.tail(20).mean()

        # Scoring
        bull = bear = 0
        if current > ma20:  bull += 1
        else:                bear += 1
        if current > ma50:  bull += 1
        else:                bear += 1
        if current > ma200: bull += 1
        else:                bear += 1
        if ma50 > ma200:    bull += 1
        else:                bear += 1

        if 50 < rsi_val <= 70:       bull += 1
        elif rsi_val < 30:           bull += 1
        elif rsi_val > 70:           bear += 1
        else:                         bear += 1

        if macd_fresh_cross: bull += 2
        elif macd_bullish:   bull += 1
        else:                 bear += 1

        if vol_ratio > 1.5: bull += 1
        elif vol_ratio < 0.5: bear += 1

        if bb_pos > 100:    bear += 1
        elif bb_pos < 0:    bull += 1

        tech_score = ((bull - bear) / max(bull + bear, 1)) * 100

        # === COMBINED & VERDICT ===
        combined = (mom_score + tech_score) / 2
        agreement = (mom_score > 0 and tech_score > 0) or (mom_score < 0 and tech_score < 0)

        if combined > 50 and agreement:
            verdict = "STRONG_BUY"
        elif combined > 20 and agreement:
            verdict = "BUY"
        elif combined < -50 and agreement:
            verdict = "STRONG_SELL"
        elif combined < -20 and agreement:
            verdict = "SELL"
        elif not agreement and abs(combined) > 10:
            verdict = "MIXED"
        else:
            verdict = "NEUTRAL"

        # 52w
        high_52w = close.tail(252).max()
        pct_from_high = (current - high_52w) / high_52w * 100

        return {
            'ticker': ticker,
            'price': current,
            'mom_score': mom_score,
            'tech_score': tech_score,
            'combined': combined,
            'verdict': verdict,
            'agreement': agreement,
            'ret_1m': ret_1m,
            'ret_3m': ret_3m,
            'ret_12m': ret_12m,
            'rsi': rsi_val,
            'adx': adx_val,
            'vol_ratio': vol_ratio,
            'pct_from_52w_high': pct_from_high,
            'macd_fresh_cross': macd_fresh_cross,
            'above_ma200': current > ma200,
        }

    except Exception:
        return None


# ============================================================
# PARALLEL SCREENING
# ============================================================

def screen_universe(tickers: list, parallel: int = 8, verbose: bool = True):
    results = []
    failed = []
    start = time.time()

    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {executor.submit(analyze_ticker, t): t for t in tickers}
        done = 0
        for future in as_completed(futures):
            ticker = futures[future]
            done += 1
            try:
                result = future.result()
                if result:
                    results.append(result)
                else:
                    failed.append(ticker)
            except Exception:
                failed.append(ticker)

            if verbose and done % 25 == 0:
                elapsed = time.time() - start
                rate = done / elapsed
                eta = (len(tickers) - done) / rate if rate > 0 else 0
                print(f"  Progress: {done}/{len(tickers)} "
                      f"({done/len(tickers)*100:.0f}%) "
                      f"- ETA {eta:.0f}s")

    if verbose:
        print(f"\n  ✅ Analyzed {len(results)} tickers σε {time.time()-start:.1f}s")
        if failed:
            print(f"  ⚠️  Failed: {len(failed)} ({', '.join(failed[:10])}{'...' if len(failed) > 10 else ''})")

    return results


# ============================================================
# RANKING & REPORT
# ============================================================

def print_results(results: list, top_n: int, min_score: float):
    if not results:
        print("\n  Δεν βρέθηκαν αποτελέσματα.")
        return

    df = pd.DataFrame(results)

    # Filter by min combined score
    df = df[df['combined'] >= min_score].copy()

    # Sort by combined score
    df = df.sort_values('combined', ascending=False).head(top_n)

    if df.empty:
        print(f"\n  Καμία μετοχή με combined score >= {min_score}")
        return

    print(f"\n{'='*95}")
    print(f"  🎯 TOP {len(df)} BULLISH CANDIDATES (min score: {min_score})")
    print(f"{'='*95}")
    print(f"  {'#':<3} {'Ticker':<7} {'Price':>8} {'Verdict':<12} "
          f"{'Combined':>9} {'Mom':>7} {'Tech':>7} "
          f"{'RSI':>5} {'1M%':>7} {'3M%':>7} {'12M%':>7}")
    print(f"  {'-'*92}")

    for i, row in enumerate(df.itertuples(), 1):
        macd_flag = " 🔔" if row.macd_fresh_cross else ""
        ma200_flag = " ✓" if row.above_ma200 else ""
        print(f"  {i:<3} {row.ticker:<7} ${row.price:>7.2f} "
              f"{row.verdict:<12} "
              f"{row.combined:>+8.1f}  "
              f"{row.mom_score:>+6.1f} {row.tech_score:>+6.1f} "
              f"{row.rsi:>5.1f} "
              f"{row.ret_1m:>+6.1f} {row.ret_3m:>+6.1f} {row.ret_12m:>+6.1f}"
              f"{macd_flag}{ma200_flag}")

    # Distribution summary
    full_df = pd.DataFrame(results)
    print(f"\n  📊 Universe distribution:")
    counts = full_df['verdict'].value_counts()
    for v in ['STRONG_BUY', 'BUY', 'NEUTRAL', 'MIXED', 'SELL', 'STRONG_SELL']:
        if v in counts.index:
            pct = counts[v] / len(full_df) * 100
            print(f"    {v:<13}: {counts[v]:>4} ({pct:.1f}%)")

    print(f"\n  Legend:")
    print(f"    🔔 = Fresh MACD bullish crossover (extra signal)")
    print(f"    ✓  = Price above 200-day MA (long-term uptrend)")


def main():
    parser = argparse.ArgumentParser(description="S&P 500 (or custom) screener")
    parser.add_argument('--universe', default='sp500',
                        choices=['sp500', 'nasdaq100', 'dow', 'custom'])
    parser.add_argument('--tickers', help='Comma-separated tickers (αν universe=custom)')
    parser.add_argument('--top', type=int, default=20, help='Top N να εμφανιστούν (default 20)')
    parser.add_argument('--min-score', type=float, default=20,
                        help='Min combined score για inclusion (default 20)')
    parser.add_argument('--parallel', type=int, default=8,
                        help='Παράλληλα downloads (default 8)')
    parser.add_argument('--export', help='Export full results σε CSV')
    args = parser.parse_args()

    # Universe selection
    print(f"\n  🔍 Loading universe: {args.universe}")
    if args.universe == 'sp500':
        tickers = get_sp500_tickers()
    elif args.universe == 'nasdaq100':
        tickers = get_nasdaq100_tickers()
    elif args.universe == 'dow':
        tickers = get_dow_tickers()
    elif args.universe == 'custom':
        if not args.tickers:
            print("  ❌ Με --universe custom χρειάζεται και --tickers AAPL,MSFT,...")
            sys.exit(1)
        tickers = [t.strip().upper() for t in args.tickers.split(',')]
    else:
        sys.exit(1)

    print(f"  📋 {len(tickers)} tickers στο universe")
    print(f"  🚀 Starting screen (parallel={args.parallel})...\n")

    results = screen_universe(tickers, parallel=args.parallel)

    print_results(results, top_n=args.top, min_score=args.min_score)

    if args.export and results:
        df = pd.DataFrame(results).sort_values('combined', ascending=False)
        df.to_csv(args.export, index=False)
        print(f"\n  💾 Exported {len(df)} rows σε {args.export}")

    print(f"\n⚠️  Disclaimer: Educational tool. Όχι financial advice.")
    print(f"   Πάντα κάνε δικιά σου ανάλυση (fundamentals, news, sector) πριν αγοράσεις.\n")


if __name__ == "__main__":
    main()
