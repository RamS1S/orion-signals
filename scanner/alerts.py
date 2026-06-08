"""
Daily Alert System
-------------------
Τρέχει την στρατηγική σε ένα universe μετοχών και στέλνει email
όταν εμφανιστεί STRONG_BUY με fresh MACD crossover (ή άλλα κριτήρια).

Χαρακτηριστικά:
  - Email alerts μέσω Gmail (ή άλλου SMTP)
  - State tracking: δεν στέλνει το ίδιο alert 2 φορές
  - Configurable criteria (verdict, MACD cross, ADX, RSI)
  - Λογ σε CSV για ιστορικό
  - Telegram support (optional)

Setup:
  1. pip install yfinance pandas numpy python-dotenv requests
  2. Φτιάξε αρχείο .env στον ίδιο φάκελο με:
        EMAIL_FROM=your.email@gmail.com
        EMAIL_PASSWORD=your_app_password
        EMAIL_TO=destination@gmail.com
        # Optional Telegram:
        TELEGRAM_BOT_TOKEN=...
        TELEGRAM_CHAT_ID=...
  3. Για Gmail χρειάζεσαι App Password (όχι το κανονικό password):
     https://myaccount.google.com/apppasswords

Χρήση:
    python alerts.py                         # Default: Dow 30
    python alerts.py --universe sp500        # S&P 500
    python alerts.py --test                  # Test email χωρίς να τρέξει screening
    python alerts.py --dry-run               # Τρέξε χωρίς να στείλεις email
"""

import os
import sys
import json
import smtplib
import argparse
import warnings
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import yfinance as yf

# Optional: load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Optional: Telegram
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ============================================================
# CONFIGURATION
# ============================================================

STATE_FILE = Path("alerts_state.json")
LOG_FILE = Path("alerts_log.csv")

EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


# ============================================================
# INDICATORS (ίδια λογική)
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
# UNIVERSE
# ============================================================

def get_universe(name: str) -> list:
    if name == "sp500":
        try:
            tables = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
            return [t.replace('.', '-') for t in tables[0]['Symbol'].tolist()]
        except Exception:
            print("⚠️  Fallback σε hardcoded top 50")
            name = "top50"
    if name == "nasdaq100":
        try:
            tables = pd.read_html("https://en.wikipedia.org/wiki/Nasdaq-100")
            for tbl in tables:
                for col in ['Ticker', 'Symbol']:
                    if col in tbl.columns:
                        return [t.replace('.', '-') for t in tbl[col].tolist()]
        except Exception:
            pass
    if name == "dow":
        return ['AAPL','AMGN','AXP','BA','CAT','CRM','CSCO','CVX','DIS','GS',
                'HD','HON','IBM','JNJ','JPM','KO','MCD','MMM','MRK','MSFT',
                'NKE','PG','SHW','TRV','UNH','V','VZ','WMT','NVDA','AMZN']
    # fallback top50
    return ['AAPL','MSFT','NVDA','GOOGL','GOOG','AMZN','META','TSLA','BRK-B','LLY',
            'AVGO','JPM','WMT','V','XOM','UNH','MA','PG','JNJ','HD',
            'COST','ORCL','ABBV','BAC','KO','NFLX','CVX','CRM','AMD','TMO',
            'PEP','ADBE','LIN','MCD','CSCO','ACN','ABT','MRK','WFC','DIS',
            'TXN','IBM','PM','INTU','GE','VZ','CAT','AMGN','ISRG','QCOM']


# ============================================================
# ANALYSIS PER TICKER
# ============================================================

def analyze_ticker(ticker: str) -> dict:
    try:
        df = yf.download(ticker, period="1y", progress=False, auto_adjust=True, threads=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 252:
            return None

        close = df['Close']
        volume = df['Volume']
        current = close.iloc[-1]
        if current < 5 or volume.tail(20).mean() < 100_000:
            return None

        # Momentum
        ret_1w = (current / close.iloc[-6]   - 1) * 100 if len(close) > 6   else 0
        ret_1m = (current / close.iloc[-22]  - 1) * 100 if len(close) > 22  else 0
        ret_3m = (current / close.iloc[-64]  - 1) * 100 if len(close) > 64  else 0
        ret_6m = (current / close.iloc[-127] - 1) * 100 if len(close) > 127 else 0
        ret_12m = (current / close.iloc[-253]- 1) * 100 if len(close) > 253 else 0

        mom_score = (np.clip(ret_1w*5,-100,100)*0.1 + np.clip(ret_1m*5,-100,100)*0.2 +
                     np.clip(ret_3m*5,-100,100)*0.3 + np.clip(ret_6m*5,-100,100)*0.2 +
                     np.clip(ret_12m*5,-100,100)*0.2)

        # Technical
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

        bull = bear = 0
        if current > ma20:   bull += 1
        else:                 bear += 1
        if current > ma50:   bull += 1
        else:                 bear += 1
        if current > ma200:  bull += 1
        else:                 bear += 1
        if ma50 > ma200:     bull += 1
        else:                 bear += 1

        if 50 < rsi_val <= 70:    bull += 1
        elif rsi_val < 30:        bull += 1
        elif rsi_val > 70:        bear += 1
        else:                      bear += 1

        if macd_fresh_cross:      bull += 2
        elif macd_bullish:        bull += 1
        else:                      bear += 1

        if vol_ratio > 1.5:       bull += 1
        elif vol_ratio < 0.5:     bear += 1
        if bb_pos > 100:          bear += 1
        elif bb_pos < 0:          bull += 1

        tech_score = ((bull - bear) / max(bull + bear, 1)) * 100
        combined = (mom_score + tech_score) / 2
        agreement = (mom_score > 0 and tech_score > 0)

        if combined > 50 and agreement:
            verdict = "STRONG_BUY"
        elif combined > 20 and agreement:
            verdict = "BUY"
        else:
            verdict = "NEUTRAL"

        return {
            'ticker': ticker, 'price': current,
            'verdict': verdict, 'combined': combined,
            'mom_score': mom_score, 'tech_score': tech_score,
            'rsi': rsi_val, 'adx': adx_val, 'vol_ratio': vol_ratio,
            'ret_1m': ret_1m, 'ret_3m': ret_3m, 'ret_12m': ret_12m,
            'macd_fresh_cross': bool(macd_fresh_cross),
            'above_ma200': bool(current > ma200),
        }
    except Exception:
        return None


# ============================================================
# ALERT CRITERIA
# ============================================================

def matches_alert_criteria(result: dict, criteria: dict) -> bool:
    """
    Επιστρέφει True αν η μετοχή πληροί τα alert criteria.
    Default: STRONG_BUY + fresh MACD crossover + πάνω από MA200.
    """
    if criteria.get('require_strong_buy', True):
        if result['verdict'] != 'STRONG_BUY':
            return False
    elif criteria.get('require_buy_or_better', False):
        if result['verdict'] not in ('BUY', 'STRONG_BUY'):
            return False

    if criteria.get('require_macd_cross', True):
        if not result['macd_fresh_cross']:
            return False

    if criteria.get('require_above_ma200', True):
        if not result['above_ma200']:
            return False

    if 'min_combined' in criteria:
        if result['combined'] < criteria['min_combined']:
            return False

    if 'min_adx' in criteria:
        if result['adx'] < criteria['min_adx']:
            return False

    if 'max_rsi' in criteria:
        if result['rsi'] > criteria['max_rsi']:
            return False

    return True


# ============================================================
# STATE MANAGEMENT (αποφυγή διπλών alerts)
# ============================================================

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def should_alert(ticker: str, state: dict, cooldown_days: int = 14) -> bool:
    """
    Επιστρέφει True αν δεν έχουμε στείλει alert για το ticker τις τελευταίες
    cooldown_days μέρες. Έτσι δεν spammάρουμε το ίδιο σήμα.
    """
    last = state.get(ticker)
    if not last:
        return True
    try:
        last_date = datetime.fromisoformat(last).date()
        days_since = (date.today() - last_date).days
        return days_since >= cooldown_days
    except Exception:
        return True


# ============================================================
# LOGGING
# ============================================================

def log_alert(result: dict):
    """Αποθηκεύει το alert σε CSV για ιστορικό."""
    entry = {
        'date': date.today().isoformat(),
        'ticker': result['ticker'],
        'price': result['price'],
        'verdict': result['verdict'],
        'combined': result['combined'],
        'rsi': result['rsi'],
        'macd_cross': result['macd_fresh_cross'],
    }
    df_entry = pd.DataFrame([entry])
    if LOG_FILE.exists():
        df_entry.to_csv(LOG_FILE, mode='a', header=False, index=False)
    else:
        df_entry.to_csv(LOG_FILE, index=False)


# ============================================================
# EMAIL
# ============================================================

def format_email_html(alerts: list, universe_name: str, total_scanned: int) -> str:
    """HTML email με όμορφο πίνακα."""
    rows_html = ""
    for r in alerts:
        rows_html += f"""
        <tr>
            <td style="padding:8px; border:1px solid #ddd;"><b>{r['ticker']}</b></td>
            <td style="padding:8px; border:1px solid #ddd;">${r['price']:.2f}</td>
            <td style="padding:8px; border:1px solid #ddd; color:#16a34a;"><b>{r['verdict']}</b></td>
            <td style="padding:8px; border:1px solid #ddd;">{r['combined']:+.1f}</td>
            <td style="padding:8px; border:1px solid #ddd;">{r['rsi']:.1f}</td>
            <td style="padding:8px; border:1px solid #ddd;">{r['ret_1m']:+.1f}%</td>
            <td style="padding:8px; border:1px solid #ddd;">{r['ret_3m']:+.1f}%</td>
            <td style="padding:8px; border:1px solid #ddd;">🔔</td>
        </tr>
        """

    return f"""
    <html><body style="font-family:Arial,sans-serif; color:#333;">
        <h2 style="color:#16a34a;">📈 Stock Alert — {date.today().isoformat()}</h2>
        <p>Σαρώθηκαν <b>{total_scanned}</b> μετοχές από <b>{universe_name}</b>.
           Βρέθηκαν <b>{len(alerts)}</b> νέα σήματα που πληρούν τα κριτήρια:</p>
        <ul>
            <li>Verdict: STRONG_BUY</li>
            <li>Fresh MACD bullish crossover</li>
            <li>Πάνω από MA200 (long-term uptrend)</li>
        </ul>
        <table style="border-collapse:collapse; width:100%; margin-top:15px;">
            <thead>
                <tr style="background:#f3f4f6;">
                    <th style="padding:8px; border:1px solid #ddd;">Ticker</th>
                    <th style="padding:8px; border:1px solid #ddd;">Price</th>
                    <th style="padding:8px; border:1px solid #ddd;">Verdict</th>
                    <th style="padding:8px; border:1px solid #ddd;">Score</th>
                    <th style="padding:8px; border:1px solid #ddd;">RSI</th>
                    <th style="padding:8px; border:1px solid #ddd;">1M</th>
                    <th style="padding:8px; border:1px solid #ddd;">3M</th>
                    <th style="padding:8px; border:1px solid #ddd;">MACD</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        <p style="margin-top:25px; color:#666; font-size:12px;">
            ⚠️ Educational tool only. Όχι financial advice.<br>
            Πριν αγοράσεις, έλεγξε fundamentals, news, sector exposure και κάνε position sizing.
        </p>
    </body></html>
    """


def send_email(subject: str, html_body: str, dry_run: bool = False) -> bool:
    if dry_run:
        print(f"\n[DRY RUN] Θα στελνόταν email:\n  Subject: {subject}\n")
        return True

    if not all([EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO]):
        print("❌ Email credentials λείπουν. Έλεγξε το .env αρχείο.")
        return False

    msg = MIMEMultipart('alternative')
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"✅ Email στάλθηκε στο {EMAIL_TO}")
        return True
    except Exception as e:
        print(f"❌ Αποτυχία αποστολής email: {e}")
        return False


# ============================================================
# TELEGRAM (optional)
# ============================================================

def send_telegram(message: str, dry_run: bool = False) -> bool:
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID and HAS_REQUESTS):
        return False
    if dry_run:
        print(f"[DRY RUN] Telegram message:\n{message[:200]}...")
        return True
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }, timeout=10)
        if resp.status_code == 200:
            print(f"✅ Telegram message sent")
            return True
        else:
            print(f"❌ Telegram error: {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Telegram exception: {e}")
        return False


def format_telegram(alerts: list) -> str:
    lines = [f"📈 <b>Stock Alert — {date.today().isoformat()}</b>\n"]
    for r in alerts:
        lines.append(
            f"🟢 <b>{r['ticker']}</b> ${r['price']:.2f}\n"
            f"   {r['verdict']} | Score: {r['combined']:+.1f}\n"
            f"   RSI: {r['rsi']:.1f} | 1M: {r['ret_1m']:+.1f}% | 3M: {r['ret_3m']:+.1f}%\n"
            f"   🔔 Fresh MACD crossover\n"
        )
    lines.append("\n⚠️ Educational only. Not financial advice.")
    return "\n".join(lines)


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_alerts(universe: str = "dow", criteria: dict = None,
                cooldown_days: int = 14, parallel: int = 10,
                dry_run: bool = False):

    if criteria is None:
        criteria = {
            'require_strong_buy': True,
            'require_macd_cross': True,
            'require_above_ma200': True,
            'min_combined': 50,
            'min_adx': 20,
            'max_rsi': 70,
        }

    print(f"\n{'='*60}")
    print(f"  🚨 DAILY ALERT RUN — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")

    tickers = get_universe(universe)
    print(f"  Universe: {universe} ({len(tickers)} tickers)")
    print(f"  Criteria: {criteria}\n")

    # Parallel scan
    results = []
    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {executor.submit(analyze_ticker, t): t for t in tickers}
        done = 0
        for future in as_completed(futures):
            done += 1
            r = future.result()
            if r:
                results.append(r)
            if done % 25 == 0:
                print(f"  Progress: {done}/{len(tickers)}")

    print(f"\n  ✅ Analyzed {len(results)} tickers")

    # Filter by criteria
    matching = [r for r in results if matches_alert_criteria(r, criteria)]
    print(f"  📋 Matching alerts: {len(matching)}")

    # Filter by cooldown (αποφυγή spam)
    state = load_state()
    new_alerts = [r for r in matching if should_alert(r['ticker'], state, cooldown_days)]
    suppressed = len(matching) - len(new_alerts)

    print(f"  🔕 Suppressed (already alerted in last {cooldown_days}d): {suppressed}")
    print(f"  🔔 New alerts to send: {len(new_alerts)}")

    if not new_alerts:
        print("\n  Δεν υπάρχουν νέα alerts σήμερα.")
        return

    # Print to console
    print(f"\n  {'─'*55}")
    for r in new_alerts:
        print(f"  🟢 {r['ticker']:<7} ${r['price']:>7.2f}  "
              f"score={r['combined']:+6.1f}  RSI={r['rsi']:>5.1f}  "
              f"1M={r['ret_1m']:+5.1f}%  3M={r['ret_3m']:+5.1f}%")
    print(f"  {'─'*55}")

    # Send email
    subject = f"📈 {len(new_alerts)} New Stock Alert(s) — {date.today().isoformat()}"
    html = format_email_html(new_alerts, universe, len(results))
    email_ok = send_email(subject, html, dry_run=dry_run)

    # Send Telegram
    if TELEGRAM_BOT_TOKEN:
        tg_msg = format_telegram(new_alerts)
        send_telegram(tg_msg, dry_run=dry_run)

    # Update state + log
    if not dry_run and email_ok:
        for r in new_alerts:
            state[r['ticker']] = date.today().isoformat()
            log_alert(r)
        save_state(state)
        print(f"\n  💾 State updated, alerts logged σε {LOG_FILE}")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--universe', default='dow',
                        choices=['dow', 'nasdaq100', 'sp500', 'top50'])
    parser.add_argument('--cooldown', type=int, default=14,
                        help='Days πριν στείλει ξανά alert για ίδιο ticker (default 14)')
    parser.add_argument('--min-score', type=float, default=50,
                        help='Min combined score (default 50)')
    parser.add_argument('--max-rsi', type=float, default=70,
                        help='Max RSI για αποφυγή overbought (default 70)')
    parser.add_argument('--allow-buy', action='store_true',
                        help='Δέξου και BUY (όχι μόνο STRONG_BUY)')
    parser.add_argument('--no-macd-cross', action='store_true',
                        help='Δεν απαιτείται fresh MACD crossover')
    parser.add_argument('--parallel', type=int, default=10)
    parser.add_argument('--dry-run', action='store_true',
                        help='Τρέξε χωρίς να στείλεις email/Telegram')
    parser.add_argument('--test', action='store_true',
                        help='Στείλε test email και exit')
    args = parser.parse_args()

    if args.test:
        print("📧 Στέλνω test email...")
        html = "<html><body><h2>✅ Test Email</h2><p>Αν το βλέπεις αυτό, το setup δουλεύει.</p></body></html>"
        send_email("Test Alert System", html, dry_run=False)
        if TELEGRAM_BOT_TOKEN:
            send_telegram("✅ Test από alert system", dry_run=False)
        sys.exit(0)

    criteria = {
        'require_strong_buy': not args.allow_buy,
        'require_buy_or_better': args.allow_buy,
        'require_macd_cross': not args.no_macd_cross,
        'require_above_ma200': True,
        'min_combined': args.min_score,
        'min_adx': 20,
        'max_rsi': args.max_rsi,
    }

    run_alerts(
        universe=args.universe,
        criteria=criteria,
        cooldown_days=args.cooldown,
        parallel=args.parallel,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
