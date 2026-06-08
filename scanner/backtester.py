"""
Backtester for Stock Analyzer Signals
--------------------------------------
Παίρνει ένα ή πολλά tickers, τρέχει την στρατηγική (momentum + technical)
σε όλο το ιστορικό και μετράει:
  - Πόσες φορές εμφανίστηκε σήμα (BUY / STRONG BUY)
  - Win rate: % φορών που η μετοχή ανέβηκε ≥ target (default 10%)
    μέσα σε holding period (default 60 ημέρες)
  - Average gain / loss
  - Expectancy ανά trade
  - Max drawdown σε equity curve (αν αγόραζες κάθε σήμα)

Χρήση:
    pip install yfinance pandas numpy
    python backtester.py AAPL
    python backtester.py AAPL MSFT NVDA GOOGL META
    python backtester.py AAPL --target 10 --horizon 60 --years 10

Σημαντικό για αξιόπιστο backtest:
  - Χρησιμοποιεί ΜΟΝΟ δεδομένα μέχρι την ημέρα του σήματος (no look-ahead)
  - Αγορά γίνεται στο close της επόμενης ημέρας (realistic execution)
  - Δεν υπολογίζει transaction costs/slippage (πρόσθεσέ τα αν θες ακρίβεια)
  - ΠΡΟΣΟΧΗ: survivorship bias - δοκιμάζεις σε μετοχές που υπάρχουν σήμερα
"""

import sys
import argparse
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import yfinance as yf


# ============================================================
# INDICATORS (ίδια λογική με τον analyzer, vectorized)
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
# COMPUTE SIGNALS VECTORIZED (για όλη την ιστορία)
# ============================================================

def compute_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Υπολογίζει momentum + technical score για κάθε ημέρα.
    Χρησιμοποιεί ΜΟΝΟ ιστορικά δεδομένα (no look-ahead).
    Επιστρέφει DataFrame με στήλες: mom_score, tech_score, signal
    """
    close = df['Close']
    volume = df['Volume']

    # Indicators
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()
    rsi_val = rsi(close)
    macd_line, signal_line = macd(close)
    bb_upper, _, bb_lower = bollinger(close)
    bb_pos = ((close - bb_lower) / (bb_upper - bb_lower)) * 100
    adx_val = adx(df)
    vol_avg = volume.rolling(20).mean()
    vol_ratio = volume / vol_avg

    # === MOMENTUM SCORE (sum of normalized returns) ===
    ret_1w = (close / close.shift(5) - 1) * 100
    ret_1m = (close / close.shift(21) - 1) * 100
    ret_3m = (close / close.shift(63) - 1) * 100
    ret_6m = (close / close.shift(126) - 1) * 100
    ret_12m = (close / close.shift(252) - 1) * 100

    mom_score = (
        np.clip(ret_1w * 5, -100, 100) * 0.1 +
        np.clip(ret_1m * 5, -100, 100) * 0.2 +
        np.clip(ret_3m * 5, -100, 100) * 0.3 +
        np.clip(ret_6m * 5, -100, 100) * 0.2 +
        np.clip(ret_12m * 5, -100, 100) * 0.2
    )

    # === TECHNICAL SCORE ===
    bull = pd.Series(0, index=close.index)
    bear = pd.Series(0, index=close.index)

    # Price vs MAs
    bull += (close > ma20).astype(int)
    bear += (close <= ma20).astype(int)
    bull += (close > ma50).astype(int)
    bear += (close <= ma50).astype(int)
    bull += (close > ma200).astype(int)
    bear += (close <= ma200).astype(int)

    # Golden/Death cross territory
    bull += (ma50 > ma200).astype(int)
    bear += (ma50 <= ma200).astype(int)

    # RSI
    bull += ((rsi_val > 50) & (rsi_val <= 70)).astype(int)
    bull += (rsi_val < 30).astype(int)
    bear += (rsi_val > 70).astype(int)
    bear += ((rsi_val <= 50) & (rsi_val >= 30)).astype(int)

    # MACD
    macd_bullish = macd_line > signal_line
    macd_cross_fresh = macd_bullish & ~(macd_line.shift() > signal_line.shift())
    bull += macd_bullish.astype(int)
    bull += macd_cross_fresh.astype(int)  # extra βάρος
    bear += (~macd_bullish).astype(int)

    # Volume
    bull += (vol_ratio > 1.5).astype(int)
    bear += (vol_ratio < 0.5).astype(int)

    # Bollinger
    bear += (bb_pos > 100).astype(int)
    bull += (bb_pos < 0).astype(int)

    tech_score = ((bull - bear) / (bull + bear).replace(0, 1)) * 100

    # === VERDICT ===
    combined = (mom_score + tech_score) / 2
    agreement = ((mom_score > 0) & (tech_score > 0)) | ((mom_score < 0) & (tech_score < 0))

    signal = pd.Series('NEUTRAL', index=close.index)
    signal[(combined > 50) & agreement] = 'STRONG_BUY'
    signal[(combined > 20) & (combined <= 50) & agreement] = 'BUY'
    signal[(combined < -50) & agreement] = 'STRONG_SELL'
    signal[(combined < -20) & (combined >= -50) & agreement] = 'SELL'
    signal[~agreement & (combined.abs() > 10)] = 'MIXED'

    return pd.DataFrame({
        'close': close,
        'mom_score': mom_score,
        'tech_score': tech_score,
        'combined': combined,
        'signal': signal,
    })


# ============================================================
# BACKTEST: για κάθε σήμα, δες τι έγινε στις επόμενες N μέρες
# ============================================================

def backtest_signals(signals_df: pd.DataFrame, target_pct: float = 10,
                      horizon: int = 60, signal_types=('BUY', 'STRONG_BUY')) -> dict:
    """
    Για κάθε ημέρα που υπήρχε bullish σήμα:
    - Υποθέτουμε αγορά στο close της ΕΠΟΜΕΝΗΣ ημέρας (no look-ahead)
    - Παρακολουθούμε για `horizon` ημέρες
    - Καταγράφουμε αν χτύπησε ο στόχος +target_pct% (winner)
      ή τι απόδοση είχε στο τέλος του horizon
    """
    close = signals_df['close']
    signal = signals_df['signal']

    trades = []

    # Βρες δείκτες όπου εμφανίστηκε σήμα (αλλά όχι την προηγούμενη ημέρα -
    # μετράμε μόνο "fresh" σήματα για να αποφύγουμε διπλομέτρηση)
    is_signal = signal.isin(signal_types)
    fresh_signal = is_signal & ~is_signal.shift(1).fillna(False)

    signal_dates = signals_df.index[fresh_signal]

    for sig_date in signal_dates:
        sig_idx = signals_df.index.get_loc(sig_date)

        # Αγορά στην ΕΠΟΜΕΝΗ ημέρα (no look-ahead)
        if sig_idx + 1 >= len(close):
            continue
        entry_idx = sig_idx + 1
        entry_price = close.iloc[entry_idx]

        # Παρακολούθηση επόμενων `horizon` ημερών
        end_idx = min(entry_idx + horizon, len(close) - 1)
        future_prices = close.iloc[entry_idx:end_idx + 1]

        max_price = future_prices.max()
        min_price = future_prices.min()
        final_price = future_prices.iloc[-1]

        max_gain_pct = ((max_price - entry_price) / entry_price) * 100
        max_loss_pct = ((min_price - entry_price) / entry_price) * 100
        final_return_pct = ((final_price - entry_price) / entry_price) * 100

        hit_target = max_gain_pct >= target_pct

        trades.append({
            'signal_date': sig_date,
            'signal_type': signal.loc[sig_date],
            'entry_price': entry_price,
            'max_gain_pct': max_gain_pct,
            'max_loss_pct': max_loss_pct,
            'final_return_pct': final_return_pct,
            'hit_target': hit_target,
        })

    return trades


# ============================================================
# STATISTICS
# ============================================================

def compute_stats(trades: list, target_pct: float) -> dict:
    if not trades:
        return None

    df = pd.DataFrame(trades)
    n = len(df)
    wins = df[df['hit_target']]
    losses = df[~df['hit_target']]

    win_rate = len(wins) / n * 100
    avg_final = df['final_return_pct'].mean()
    median_final = df['final_return_pct'].median()
    avg_win_final = wins['final_return_pct'].mean() if len(wins) > 0 else 0
    avg_loss_final = losses['final_return_pct'].mean() if len(losses) > 0 else 0
    avg_max_gain = df['max_gain_pct'].mean()
    avg_max_loss = df['max_loss_pct'].mean()

    # Expectancy: μέση απόδοση ανά trade
    expectancy = avg_final

    # Profit factor
    total_gains = df[df['final_return_pct'] > 0]['final_return_pct'].sum()
    total_losses = abs(df[df['final_return_pct'] < 0]['final_return_pct'].sum())
    profit_factor = total_gains / total_losses if total_losses > 0 else float('inf')

    return {
        'n_trades': n,
        'win_rate': win_rate,
        'avg_final_return': avg_final,
        'median_final_return': median_final,
        'avg_winner_return': avg_win_final,
        'avg_loser_return': avg_loss_final,
        'avg_max_gain': avg_max_gain,
        'avg_max_loss': avg_max_loss,
        'expectancy': expectancy,
        'profit_factor': profit_factor,
    }


def baseline_stats(df: pd.DataFrame, target_pct: float, horizon: int) -> dict:
    """
    Baseline: τι θα έπαιρνες αν αγόραζες ΤΥΧΑΙΑ ημέρα (buy & hold horizon).
    Έτσι βλέπεις αν το σήμα έχει πραγματικό edge πάνω από το random.
    """
    close = df['Close']
    future_returns = []
    hit_target_count = 0

    for i in range(len(close) - horizon - 1):
        entry = close.iloc[i + 1]
        window = close.iloc[i + 1:i + 1 + horizon]
        max_price = window.max()
        final = window.iloc[-1]
        max_gain = (max_price - entry) / entry * 100
        final_ret = (final - entry) / entry * 100
        future_returns.append(final_ret)
        if max_gain >= target_pct:
            hit_target_count += 1

    n = len(future_returns)
    if n == 0:
        return None

    return {
        'baseline_win_rate': hit_target_count / n * 100,
        'baseline_avg_return': np.mean(future_returns),
        'baseline_median_return': np.median(future_returns),
    }


# ============================================================
# REPORT
# ============================================================

def run_backtest(ticker: str, target_pct: float, horizon: int, years: int):
    ticker = ticker.upper()
    print(f"\n{'='*70}")
    print(f"  BACKTEST: {ticker}")
    print(f"  Target: +{target_pct}% within {horizon} trading days")
    print(f"  History: last {years} years")
    print(f"{'='*70}")

    try:
        df = yf.download(ticker, period=f"{years}y", progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 300:
            print(f"  ⚠️  Ανεπαρκή δεδομένα για {ticker}")
            return None
    except Exception as e:
        print(f"  Σφάλμα: {e}")
        return None

    signals_df = compute_signals(df)
    trades = backtest_signals(signals_df, target_pct=target_pct, horizon=horizon,
                                signal_types=('BUY', 'STRONG_BUY'))

    if not trades:
        print("  Δεν εμφανίστηκαν bullish σήματα στο διάστημα.")
        return None

    stats = compute_stats(trades, target_pct)
    baseline = baseline_stats(df, target_pct, horizon)

    print(f"\n  📊 RESULTS")
    print(f"  Total bullish signals:    {stats['n_trades']}")
    print(f"  Win rate (hit +{target_pct}%):    {stats['win_rate']:.1f}%")
    print(f"  Avg final return:         {stats['avg_final_return']:+.2f}%")
    print(f"  Median final return:      {stats['median_final_return']:+.2f}%")
    print(f"  Avg max gain reached:     {stats['avg_max_gain']:+.2f}%")
    print(f"  Avg max drawdown:         {stats['avg_max_loss']:+.2f}%")
    print(f"  Expectancy per trade:     {stats['expectancy']:+.2f}%")
    print(f"  Profit factor:            {stats['profit_factor']:.2f}")

    if baseline:
        print(f"\n  🎲 BASELINE (random entry, same horizon)")
        print(f"  Baseline win rate:        {baseline['baseline_win_rate']:.1f}%")
        print(f"  Baseline avg return:      {baseline['baseline_avg_return']:+.2f}%")

        edge_wr = stats['win_rate'] - baseline['baseline_win_rate']
        edge_ret = stats['avg_final_return'] - baseline['baseline_avg_return']
        print(f"\n  📈 EDGE vs random:")
        print(f"  Win rate edge:            {edge_wr:+.1f} pp")
        print(f"  Return edge:              {edge_ret:+.2f} pp")

        if edge_wr > 5 and edge_ret > 1:
            print(f"  ✅ Σήμα έχει θετικό edge")
        elif edge_wr > 0 and edge_ret > 0:
            print(f"  🟡 Σήμα έχει οριακό edge (μάλλον θόρυβος)")
        else:
            print(f"  ❌ Σήμα ΔΕΝ έχει edge πάνω από το random")

    return {'ticker': ticker, 'stats': stats, 'baseline': baseline}


def main():
    parser = argparse.ArgumentParser(description="Backtest stock signals")
    parser.add_argument('tickers', nargs='+', help='Tickers (π.χ. AAPL MSFT)')
    parser.add_argument('--target', type=float, default=10,
                        help='Target gain %% (default 10)')
    parser.add_argument('--horizon', type=int, default=60,
                        help='Holding period in trading days (default 60)')
    parser.add_argument('--years', type=int, default=10,
                        help='Years of history (default 10)')
    args = parser.parse_args()

    all_results = []
    for ticker in args.tickers:
        result = run_backtest(ticker, args.target, args.horizon, args.years)
        if result:
            all_results.append(result)

    # Aggregate αν έχουμε πολλαπλά tickers
    if len(all_results) > 1:
        print(f"\n{'='*70}")
        print(f"  📋 AGGREGATE ACROSS {len(all_results)} TICKERS")
        print(f"{'='*70}")
        total_trades = sum(r['stats']['n_trades'] for r in all_results)
        wr_weighted = sum(r['stats']['win_rate'] * r['stats']['n_trades']
                          for r in all_results) / total_trades
        ret_weighted = sum(r['stats']['avg_final_return'] * r['stats']['n_trades']
                            for r in all_results) / total_trades
        print(f"  Total signals across all tickers: {total_trades}")
        print(f"  Weighted win rate: {wr_weighted:.1f}%")
        print(f"  Weighted avg return: {ret_weighted:+.2f}%")

    print(f"\n⚠️  Disclaimer: Educational tool. Συμπεριλάβει survivorship bias")
    print(f"   (μετοχές που υπάρχουν σήμερα). Δεν περιλαμβάνει transaction costs.")
    print(f"   Past performance != future results.\n")


if __name__ == "__main__":
    main()
