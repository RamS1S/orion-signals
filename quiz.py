"""
Orion Signals — Quiz Module
-----------------------------
90 ερωτήσεις (30 ανά κατηγορία)
Εμφανίζει 30 τυχαίες (10 ανά κατηγορία)
Μετά το Sign Up και πριν το Disclaimer
"""

import random
import streamlit as st

# ============================================================
# QUESTIONS DATABASE
# ============================================================

STOCKS_QUESTIONS = [
    {
        "q": "What does RSI stand for?",
        "options": ["Relative Strength Index", "Real Stock Indicator", "Rate of Stock Increase", "Risk Signal Index"],
        "answer": "Relative Strength Index",
        "explanation": "RSI measures the speed and magnitude of recent price changes to evaluate overbought or oversold conditions."
    },
    {
        "q": "An RSI value above 70 typically indicates:",
        "options": ["Oversold conditions", "Overbought conditions", "Strong uptrend", "Weak volume"],
        "answer": "Overbought conditions",
        "explanation": "RSI > 70 suggests a stock may be overbought and could be due for a pullback."
    },
    {
        "q": "What does MACD stand for?",
        "options": ["Moving Average Convergence Divergence", "Market Acceleration and Change Direction", "Mean Average Cost Distribution", "Momentum and Chart Direction"],
        "answer": "Moving Average Convergence Divergence",
        "explanation": "MACD is a trend-following momentum indicator showing the relationship between two moving averages."
    },
    {
        "q": "A Golden Cross occurs when:",
        "options": ["The 50-day MA crosses above the 200-day MA", "The 200-day MA crosses above the 50-day MA", "RSI crosses above 50", "Volume doubles overnight"],
        "answer": "The 50-day MA crosses above the 200-day MA",
        "explanation": "A Golden Cross is considered a bullish signal indicating potential long-term upward momentum."
    },
    {
        "q": "What does a high volume spike on a bullish day typically signal?",
        "options": ["Weak buying interest", "Strong buying conviction behind the move", "Upcoming earnings", "Insider selling"],
        "answer": "Strong buying conviction behind the move",
        "explanation": "High volume confirms the strength of a price move — without volume, moves are less reliable."
    },
    {
        "q": "What is a Stop Loss?",
        "options": ["A price target where you take profits", "A pre-set price level to exit a losing trade", "A type of market order", "A dividend payment"],
        "answer": "A pre-set price level to exit a losing trade",
        "explanation": "Stop Loss limits your downside by automatically exiting a position if price falls to a set level."
    },
    {
        "q": "What is a support level?",
        "options": ["A price where selling pressure typically increases", "A price where buying interest typically holds the stock up", "The highest price in a year", "A broker fee"],
        "answer": "A price where buying interest typically holds the stock up",
        "explanation": "Support is a price floor where demand is strong enough to prevent further decline."
    },
    {
        "q": "What does 'buying the dip' mean?",
        "options": ["Buying stocks that are falling", "Buying stocks at a temporary price decline within an uptrend", "Selling at a loss", "Buying penny stocks"],
        "answer": "Buying stocks at a temporary price decline within an uptrend",
        "explanation": "Buying the dip means purchasing shares during a short-term pullback in an otherwise rising market."
    },
    {
        "q": "What is market capitalization?",
        "options": ["The total revenue of a company", "Share price × total number of shares outstanding", "The book value of a company", "Annual dividends paid"],
        "answer": "Share price × total number of shares outstanding",
        "explanation": "Market cap is the total market value of a company's outstanding shares."
    },
    {
        "q": "What is an earnings report?",
        "options": ["A monthly trading statement", "A quarterly report of a company's financial performance", "A stock broker's fee summary", "A dividend announcement"],
        "answer": "A quarterly report of a company's financial performance",
        "explanation": "Earnings reports reveal a company's revenue, profit, and guidance — major price movers."
    },
    {
        "q": "What does ADX measure?",
        "options": ["The direction of a trend", "The strength of a trend regardless of direction", "Average daily trading volume", "Advance-Decline ratio"],
        "answer": "The strength of a trend regardless of direction",
        "explanation": "ADX above 25 indicates a strong trend. It does NOT tell you if it's up or down."
    },
    {
        "q": "What are Bollinger Bands?",
        "options": ["Support and resistance lines", "Bands placed 2 standard deviations around a moving average", "Volume indicators", "Moving average crossovers"],
        "answer": "Bands placed 2 standard deviations around a moving average",
        "explanation": "When price touches the upper band it may be overbought; lower band may indicate oversold."
    },
    {
        "q": "What is a Death Cross?",
        "options": ["RSI dropping below 30", "The 50-day MA crosses below the 200-day MA", "A stock reaching a 52-week low", "Volume dropping to zero"],
        "answer": "The 50-day MA crosses below the 200-day MA",
        "explanation": "A Death Cross is a bearish signal suggesting potential long-term downward momentum."
    },
    {
        "q": "What does EMA stand for?",
        "options": ["Equal Moving Average", "Exponential Moving Average", "Extended Market Analysis", "Earnings Momentum Average"],
        "answer": "Exponential Moving Average",
        "explanation": "EMA gives more weight to recent prices, making it more responsive than a simple moving average."
    },
    {
        "q": "What is a resistance level?",
        "options": ["A price floor where buying increases", "A price ceiling where selling pressure typically increases", "The average price over 200 days", "A broker limit"],
        "answer": "A price ceiling where selling pressure typically increases",
        "explanation": "Resistance is a price level where selling is strong enough to prevent further price increases."
    },
    {
        "q": "What does 'going long' mean?",
        "options": ["Holding a stock for many years", "Buying a stock expecting the price to rise", "Short selling a stock", "Buying bonds"],
        "answer": "Buying a stock expecting the price to rise",
        "explanation": "Going long means you own the asset and profit if the price increases."
    },
    {
        "q": "What is a short squeeze?",
        "options": ["When a stock drops rapidly", "When short sellers are forced to buy to cover losses, driving price up", "A technical pattern", "A type of dividend"],
        "answer": "When short sellers are forced to buy to cover losses, driving price up",
        "explanation": "Short squeezes can cause rapid, dramatic price increases as shorts rush to cover their positions."
    },
    {
        "q": "What does P/E ratio stand for?",
        "options": ["Profit/Earnings", "Price/Earnings", "Performance/Efficiency", "Portfolio/Equity"],
        "answer": "Price/Earnings",
        "explanation": "P/E ratio compares a stock's price to its earnings per share — a key valuation metric."
    },
    {
        "q": "What is ATR used for in trading?",
        "options": ["Identifying trend direction", "Measuring market volatility and setting stop losses", "Calculating dividends", "Finding support levels"],
        "answer": "Measuring market volatility and setting stop losses",
        "explanation": "ATR (Average True Range) measures how much a stock moves on average — useful for position sizing."
    },
    {
        "q": "What is VWAP?",
        "options": ["Volume Weighted Average Price", "Volatility With Average Points", "Variable Width Ascending Pattern", "Volume and Wave Analysis Price"],
        "answer": "Volume Weighted Average Price",
        "explanation": "VWAP is used by institutional traders as a benchmark — price above VWAP is bullish intraday."
    },
    {
        "q": "What does 'RSI divergence' mean?",
        "options": ["RSI and price move in the same direction", "Price makes a new high but RSI makes a lower high — warning sign", "RSI crosses above 50", "RSI equals zero"],
        "answer": "Price makes a new high but RSI makes a lower high — warning sign",
        "explanation": "Divergence between price and RSI suggests momentum is weakening — potential reversal ahead."
    },
    {
        "q": "What is momentum in trading?",
        "options": ["The total value of a portfolio", "The rate of acceleration of a stock's price movement", "A type of order", "Daily trading volume"],
        "answer": "The rate of acceleration of a stock's price movement",
        "explanation": "High momentum stocks continue in their direction — momentum trading capitalizes on this tendency."
    },
    {
        "q": "What does 'overextended' mean in technical analysis?",
        "options": ["A stock with high volume", "A stock that has moved too far too fast and may reverse", "A stock near its 52-week low", "A stock with no volume"],
        "answer": "A stock that has moved too far too fast and may reverse",
        "explanation": "Overextended stocks often pull back or consolidate before continuing their trend."
    },
    {
        "q": "What is a 52-week high?",
        "options": ["The average price over a year", "The highest price a stock has traded at in the past 52 weeks", "The target price set by analysts", "The IPO price"],
        "answer": "The highest price a stock has traded at in the past 52 weeks",
        "explanation": "Breaking above a 52-week high is often a bullish signal — less overhead resistance."
    },
    {
        "q": "What does 'consolidation' mean?",
        "options": ["A stock merging with another", "A period of sideways price movement after a big move", "A stock hitting its all-time high", "Increasing dividends"],
        "answer": "A period of sideways price movement after a big move",
        "explanation": "Consolidation lets a stock 'rest' and build energy for its next move up or down."
    },
    {
        "q": "What is a breakout?",
        "options": ["A stock dropping below support", "A stock moving above a key resistance level on high volume", "A company going bankrupt", "A broker error"],
        "answer": "A stock moving above a key resistance level on high volume",
        "explanation": "Breakouts on high volume are more reliable signals of a new upward trend beginning."
    },
    {
        "q": "What does 'position sizing' mean?",
        "options": ["The number of traders in a stock", "How much capital you allocate to a single trade", "The size of a company", "The spread between bid and ask"],
        "answer": "How much capital you allocate to a single trade",
        "explanation": "Proper position sizing is key to risk management — never risk more than you can afford to lose."
    },
    {
        "q": "What is Risk/Reward ratio?",
        "options": ["Profit divided by total revenue", "Potential profit compared to potential loss on a trade", "The P/E ratio", "Beta of a stock"],
        "answer": "Potential profit compared to potential loss on a trade",
        "explanation": "A 1:2 R/R means risking $1 to potentially make $2. Always aim for at least 1:2."
    },
    {
        "q": "What does 'confirmation' mean before entering a trade?",
        "options": ["Broker approval", "Waiting for additional signals to validate your thesis before entering", "A guaranteed profit", "A stock split"],
        "answer": "Waiting for additional signals to validate your thesis before entering",
        "explanation": "Confirmation reduces false entries — e.g., waiting for price to move +1.5% before buying."
    },
    {
        "q": "What is a moving average crossover signal?",
        "options": ["Two moving averages intersecting — potential trend change", "A stock splitting", "Volume doubling", "RSI hitting 50"],
        "answer": "Two moving averages intersecting — potential trend change",
        "explanation": "When a faster MA crosses above a slower MA, it signals potential upward momentum ahead."
    },
]

OPTIONS_QUESTIONS = [
    {
        "q": "What is a Call Option?",
        "options": ["The right to sell shares at a set price", "The right to buy shares at a set price", "An obligation to buy shares", "A type of dividend"],
        "answer": "The right to buy shares at a set price",
        "explanation": "A call option gives the buyer the right (not obligation) to buy shares at the strike price."
    },
    {
        "q": "What is a Put Option?",
        "options": ["The right to buy shares at a set price", "The right to sell shares at a set price", "An obligation to sell shares", "A broker commission"],
        "answer": "The right to sell shares at a set price",
        "explanation": "A put option profits when the stock price falls below the strike price."
    },
    {
        "q": "What is the Strike Price?",
        "options": ["The current market price", "The price at which an option can be exercised", "The highest price today", "The broker's fee"],
        "answer": "The price at which an option can be exercised",
        "explanation": "The strike price is the agreed price at which you can buy (call) or sell (put) the underlying asset."
    },
    {
        "q": "What is the Premium in options?",
        "options": ["The profit from an option", "The cost to buy an options contract", "The strike price", "The expiry date fee"],
        "answer": "The cost to buy an options contract",
        "explanation": "Premium is what you pay to buy an option — your maximum loss if you're a buyer."
    },
    {
        "q": "What does 'In The Money' (ITM) mean for a call option?",
        "options": ["The option has expired", "The stock price is above the strike price", "The option premium is high", "You've made a profit"],
        "answer": "The stock price is above the strike price",
        "explanation": "ITM calls have intrinsic value — the stock is already above where you can buy it."
    },
    {
        "q": "What is Theta in options?",
        "options": ["Sensitivity to price movement", "Time decay — the daily loss of option value as expiration approaches", "Sensitivity to volatility", "The strike price delta"],
        "answer": "Time decay — the daily loss of option value as expiration approaches",
        "explanation": "Theta works against option buyers — every day your option loses value even if price doesn't move."
    },
    {
        "q": "What is Delta in options?",
        "options": ["How much the option price changes per $1 move in the stock", "The time remaining on the option", "The implied volatility", "The option's daily decay"],
        "answer": "How much the option price changes per $1 move in the stock",
        "explanation": "Delta of 0.5 means if the stock rises $1, the option gains $0.50. Call deltas range from 0 to 1."
    },
    {
        "q": "What is Implied Volatility (IV)?",
        "options": ["Historical price movement", "The market's expectation of future price movement — affects option price", "The stock's beta", "The ATR of the stock"],
        "answer": "The market's expectation of future price movement — affects option price",
        "explanation": "High IV = expensive options. Low IV = cheap options. Buy options when IV is low."
    },
    {
        "q": "What is IV Crush?",
        "options": ["A stock falling sharply", "A rapid drop in implied volatility after an event like earnings", "Theta decay", "A broker margin call"],
        "answer": "A rapid drop in implied volatility after an event like earnings",
        "explanation": "After earnings, IV drops sharply — even if you're right on direction, your option may lose value."
    },
    {
        "q": "What is a Covered Call?",
        "options": ["Buying a call with no shares", "Selling a call option on shares you already own", "Buying a call and a put", "A broker-issued option"],
        "answer": "Selling a call option on shares you already own",
        "explanation": "Covered calls generate income from your existing shares by selling upside potential."
    },
    {
        "q": "What is Gamma in options?",
        "options": ["The rate of change of Delta", "Time decay per day", "The strike price sensitivity", "Daily volume of the option"],
        "answer": "The rate of change of Delta",
        "explanation": "Gamma is highest for at-the-money options near expiration — can make options very volatile."
    },
    {
        "q": "What is Vega in options?",
        "options": ["Sensitivity to time", "Sensitivity to changes in implied volatility", "Rate of Delta change", "Intrinsic value"],
        "answer": "Sensitivity to changes in implied volatility",
        "explanation": "High Vega means the option price changes significantly when IV moves up or down."
    },
    {
        "q": "What does 'Out of The Money' (OTM) mean for a put option?",
        "options": ["The stock is below the strike price", "The stock is above the strike price", "The option has expired worthless", "You've lost your premium"],
        "answer": "The stock is above the strike price",
        "explanation": "An OTM put has no intrinsic value — the stock hasn't fallen to the strike price yet."
    },
    {
        "q": "What is an Iron Condor?",
        "options": ["Buying a call and a put", "Selling an OTM call spread and OTM put spread simultaneously", "A leveraged ETF strategy", "A type of covered call"],
        "answer": "Selling an OTM call spread and OTM put spread simultaneously",
        "explanation": "Iron Condors profit from low volatility — you collect premium when the stock stays in a range."
    },
    {
        "q": "What is a Straddle?",
        "options": ["Buying both a call and put at the same strike and expiry", "Selling both call and put", "Buying a call and shorting the stock", "A covered call strategy"],
        "answer": "Buying both a call and put at the same strike and expiry",
        "explanation": "Straddles profit from big moves in either direction — useful around earnings."
    },
    {
        "q": "What is an option's Intrinsic Value?",
        "options": ["The time value of the option", "The amount the option is in the money", "The implied volatility premium", "The broker spread"],
        "answer": "The amount the option is in the money",
        "explanation": "Intrinsic value = how much you'd gain by exercising immediately. OTM options have zero intrinsic value."
    },
    {
        "q": "What is the maximum loss for an option buyer?",
        "options": ["Unlimited", "The strike price", "The premium paid", "The stock price"],
        "answer": "The premium paid",
        "explanation": "As an option buyer, the worst case is losing the premium — your defined maximum risk."
    },
    {
        "q": "Why do traders prefer options over stocks sometimes?",
        "options": ["Options always make more money", "Options provide leverage — control more shares with less capital", "Options have no time decay", "Options pay dividends"],
        "answer": "Options provide leverage — control more shares with less capital",
        "explanation": "One contract controls 100 shares. This amplifies both gains AND losses."
    },
    {
        "q": "What is a Debit Spread?",
        "options": ["Selling options to collect premium", "Buying one option and selling another to reduce cost", "A broker fee", "An OTM covered call"],
        "answer": "Buying one option and selling another to reduce cost",
        "explanation": "Debit spreads cost money upfront but limit both risk and reward — great for directional bets."
    },
    {
        "q": "What does 'rolling' an option mean?",
        "options": ["Exercising the option early", "Closing the current option and opening a new one with a different expiry/strike", "Selling the option at expiry", "Converting to stock"],
        "answer": "Closing the current option and opening a new one with a different expiry/strike",
        "explanation": "Rolling gives your trade more time or adjusts the strike if the market moved against you."
    },
    {
        "q": "What is the relationship between IV and option price?",
        "options": ["Higher IV = cheaper options", "Higher IV = more expensive options", "IV does not affect price", "IV only affects puts"],
        "answer": "Higher IV = more expensive options",
        "explanation": "High IV reflects uncertainty — options cost more when the market expects large moves."
    },
    {
        "q": "What is a Cash Secured Put?",
        "options": ["Buying a put with cash", "Selling a put while holding enough cash to buy the stock if assigned", "A covered call strategy", "A broker margin product"],
        "answer": "Selling a put while holding enough cash to buy the stock if assigned",
        "explanation": "If the stock drops below your strike, you buy it at that price — a common income strategy."
    },
    {
        "q": "What does 'assignment' mean in options?",
        "options": ["Being selected by a broker", "The option seller being obligated to buy/sell shares", "Receiving dividends", "Rolling to a new expiry"],
        "answer": "The option seller being obligated to buy/sell shares",
        "explanation": "When a buyer exercises their option, the seller is 'assigned' and must fulfill the contract."
    },
    {
        "q": "What is Open Interest in options?",
        "options": ["The number of trades today", "The total number of outstanding option contracts", "The profit on open positions", "The bid-ask spread"],
        "answer": "The total number of outstanding option contracts",
        "explanation": "High open interest means more liquidity — easier to enter and exit your position."
    },
    {
        "q": "What is IV Rank (IVR)?",
        "options": ["The raw implied volatility number", "How current IV compares to its historical range — percentage", "The daily IV change", "The Vega of an option"],
        "answer": "How current IV compares to its historical range — percentage",
        "explanation": "IVR of 80 means IV is at the 80th percentile of its range — options are expensive. Good for selling."
    },
    {
        "q": "What is the Put/Call Ratio?",
        "options": ["The ratio of profits to losses", "The number of puts vs calls traded — market sentiment indicator", "The premium difference between put and call", "The delta ratio"],
        "answer": "The number of puts vs calls traded — market sentiment indicator",
        "explanation": "High P/C ratio signals fear (bearish sentiment). Low ratio signals greed (bullish sentiment)."
    },
    {
        "q": "When is the best time to BUY options?",
        "options": ["When IV is very high", "When IV is low relative to its historical range", "Right before expiration", "After earnings"],
        "answer": "When IV is low relative to its historical range",
        "explanation": "Buying cheap options (low IV) gives you better value — you pay less for the same potential move."
    },
    {
        "q": "What happens to options on expiration day if OTM?",
        "options": ["They are rolled automatically", "They expire worthless — the buyer loses the premium", "They convert to stock", "They gain value"],
        "answer": "They expire worthless — the buyer loses the premium",
        "explanation": "OTM options at expiration have no value. Theta has eroded them completely by this point."
    },
    {
        "q": "What is a Strangle?",
        "options": ["Buying a call and put at different strikes", "Selling both a call and put at the same strike", "A bearish spread", "A type of covered call"],
        "answer": "Buying a call and put at different strikes",
        "explanation": "Strangles are cheaper than straddles but need a bigger move to profit."
    },
    {
        "q": "What is the 'Greeks' in options?",
        "options": ["Ancient trading strategies", "Delta, Gamma, Theta, Vega, Rho — measures of option sensitivity", "European-style options", "A trading platform"],
        "answer": "Delta, Gamma, Theta, Vega, Rho — measures of option sensitivity",
        "explanation": "The Greeks help traders understand how an option's price will change with various market conditions."
    },
]

CRYPTO_QUESTIONS = [
    {
        "q": "What is a blockchain?",
        "options": ["A type of crypto wallet", "A decentralized, distributed ledger recording all transactions", "A crypto exchange", "A mining machine"],
        "answer": "A decentralized, distributed ledger recording all transactions",
        "explanation": "Blockchain is the underlying technology of crypto — transparent, immutable, and decentralized."
    },
    {
        "q": "What is a crypto wallet?",
        "options": ["An exchange account", "A software or hardware tool for storing and managing crypto", "A mining pool", "A blockchain node"],
        "answer": "A software or hardware tool for storing and managing crypto",
        "explanation": "Wallets store your private keys — the passwords to your crypto. Not your keys, not your coins."
    },
    {
        "q": "What does HODL mean in crypto?",
        "options": ["High Odds Daily Leverage", "Hold On for Dear Life — long-term holding strategy", "A type of trade order", "Hedge on Declining Lows"],
        "answer": "Hold On for Dear Life — long-term holding strategy",
        "explanation": "HODL originated from a typo and became a philosophy — holding crypto through volatility."
    },
    {
        "q": "What is DeFi?",
        "options": ["Default Finance", "Decentralized Finance — financial services without intermediaries", "Derivative Finance", "Digital Fiat"],
        "answer": "Decentralized Finance — financial services without intermediaries",
        "explanation": "DeFi uses smart contracts to offer lending, trading, and yield farming without banks."
    },
    {
        "q": "What is a Funding Rate in crypto futures?",
        "options": ["The fee to open a futures position", "Periodic payments between long and short traders to keep futures price near spot", "The exchange withdrawal fee", "The staking reward rate"],
        "answer": "Periodic payments between long and short traders to keep futures price near spot",
        "explanation": "High positive funding = longs paying shorts = market overheated. Often precedes corrections."
    },
    {
        "q": "What is liquidation in crypto trading?",
        "options": ["Selling all your crypto", "When a leveraged position is forcibly closed due to insufficient margin", "Converting crypto to fiat", "Unstaking tokens"],
        "answer": "When a leveraged position is forcibly closed due to insufficient margin",
        "explanation": "Liquidations can cascade — a big move triggers mass liquidations, accelerating the price move."
    },
    {
        "q": "What is market cap in crypto?",
        "options": ["The maximum supply of a coin", "Current price × circulating supply", "The 24h trading volume", "The all-time high price"],
        "answer": "Current price × circulating supply",
        "explanation": "Market cap determines the relative size of a cryptocurrency compared to others."
    },
    {
        "q": "What is an altcoin?",
        "options": ["A fake cryptocurrency", "Any cryptocurrency other than Bitcoin", "A stablecoin", "A mining reward coin"],
        "answer": "Any cryptocurrency other than Bitcoin",
        "explanation": "Altcoins include Ethereum, Solana, XRP and thousands of others. They often follow Bitcoin's trend."
    },
    {
        "q": "What does the Fear & Greed Index measure in crypto?",
        "options": ["The total crypto market cap", "Market sentiment from extreme fear to extreme greed (0-100)", "Bitcoin's hash rate", "Exchange trading volume"],
        "answer": "Market sentiment from extreme fear to extreme greed (0-100)",
        "explanation": "Extreme fear (0-25) = potential buy opportunity. Extreme greed (75-100) = potential sell signal."
    },
    {
        "q": "What is on-chain data?",
        "options": ["Trading data from exchanges", "Data recorded directly on the blockchain — wallet movements, transactions", "Price chart data", "Social media sentiment"],
        "answer": "Data recorded directly on the blockchain — wallet movements, transactions",
        "explanation": "On-chain data reveals whale movements, exchange flows, and holder behavior — powerful signals."
    },
    {
        "q": "What is Bitcoin Dominance?",
        "options": ["Bitcoin's hash rate vs other coins", "Bitcoin's market cap as a percentage of total crypto market cap", "Bitcoin's trading volume share", "The number of Bitcoin holders"],
        "answer": "Bitcoin's market cap as a percentage of total crypto market cap",
        "explanation": "Rising BTC dominance often means capital flowing from altcoins to Bitcoin — risk-off signal."
    },
    {
        "q": "What is a whale in crypto?",
        "options": ["A large mining operation", "An entity holding a very large amount of cryptocurrency", "A leverage trader", "A crypto exchange"],
        "answer": "An entity holding a very large amount of cryptocurrency",
        "explanation": "Whale movements — large transfers to exchanges — can signal incoming selling pressure."
    },
    {
        "q": "What does 'Exchange Inflow' mean?",
        "options": ["Money deposited in fiat", "Crypto being moved from wallets to exchanges — potential selling", "New users joining an exchange", "Exchange listing fees"],
        "answer": "Crypto being moved from wallets to exchanges — potential selling",
        "explanation": "Large exchange inflows often precede selling — people move coins to exchanges to sell them."
    },
    {
        "q": "What is a stablecoin?",
        "options": ["A slowly growing cryptocurrency", "A cryptocurrency pegged to a stable asset like USD", "A government-issued digital currency", "A low-volatility altcoin"],
        "answer": "A cryptocurrency pegged to a stable asset like USD",
        "explanation": "Stablecoins like USDT and USDC maintain a 1:1 peg with the dollar — used for safety."
    },
    {
        "q": "What is the halving in Bitcoin?",
        "options": ["Bitcoin price dropping 50%", "The mining reward being cut in half approximately every 4 years", "A fork of the Bitcoin blockchain", "A market correction"],
        "answer": "The mining reward being cut in half approximately every 4 years",
        "explanation": "Halvings reduce Bitcoin supply issuance — historically bullish events for Bitcoin price."
    },
    {
        "q": "What does DYOR mean in crypto?",
        "options": ["Daily Yield on Returns", "Do Your Own Research", "Decentralized Yield on Risk", "Deploy Your Own Rewards"],
        "answer": "Do Your Own Research",
        "explanation": "DYOR is a reminder to verify information yourself before making any investment decisions."
    },
    {
        "q": "What is a rug pull?",
        "options": ["A market crash", "When developers abandon a project and run off with investor funds", "A liquidation event", "A short squeeze"],
        "answer": "When developers abandon a project and run off with investor funds",
        "explanation": "Rug pulls are common in DeFi — always research the team behind any crypto project."
    },
    {
        "q": "What is Open Interest in crypto futures?",
        "options": ["The number of new accounts", "The total value of outstanding futures contracts", "The daily trading volume", "The funding rate"],
        "answer": "The total value of outstanding futures contracts",
        "explanation": "Rising OI with rising price = strong uptrend. Falling OI = positions being closed."
    },
    {
        "q": "What is a bull run in crypto?",
        "options": ["A temporary price spike", "A sustained period of rising prices across the crypto market", "A single coin's price increase", "A futures contract type"],
        "answer": "A sustained period of rising prices across the crypto market",
        "explanation": "Bull runs are characterized by broad market gains, high retail interest, and extreme greed."
    },
    {
        "q": "What is a bear market in crypto?",
        "options": ["A market with low volume", "A prolonged period of falling prices — typically 20%+ decline", "A single coin correction", "A stablecoin depegging"],
        "answer": "A prolonged period of falling prices — typically 20%+ decline",
        "explanation": "Bear markets test conviction — many retail traders sell at the bottom out of fear."
    },
    {
        "q": "What is the SOPR indicator?",
        "options": ["Speed of Price Recovery", "Spent Output Profit Ratio — whether coins are being sold at profit or loss", "Sum of Position Returns", "Stochastic Oscillator Price Ratio"],
        "answer": "Spent Output Profit Ratio — whether coins are being sold at profit or loss",
        "explanation": "SOPR > 1 means holders are selling at profit. SOPR < 1 means they're selling at a loss — capitulation."
    },
    {
        "q": "What is a crypto liquidation heatmap?",
        "options": ["A chart of mining activity", "A visual showing price levels where large leveraged positions will be liquidated", "A whale tracker", "An exchange fee chart"],
        "answer": "A visual showing price levels where large leveraged positions will be liquidated",
        "explanation": "Price often moves toward liquidation clusters — market makers hunt stop losses and liquidations."
    },
    {
        "q": "What is staking in crypto?",
        "options": ["Mining Bitcoin", "Locking up crypto to support a network and earn rewards", "Day trading crypto", "Converting crypto to NFTs"],
        "answer": "Locking up crypto to support a network and earn rewards",
        "explanation": "Staking is like earning interest — you lock coins and receive rewards for supporting the network."
    },
    {
        "q": "What is a smart contract?",
        "options": ["A legal crypto agreement", "Self-executing code on a blockchain that runs when conditions are met", "A trading bot", "An exchange API"],
        "answer": "Self-executing code on a blockchain that runs when conditions are met",
        "explanation": "Smart contracts power DeFi, NFTs, and DAOs — no intermediary needed to enforce the terms."
    },
    {
        "q": "What does FUD mean in crypto?",
        "options": ["Future Upside Direction", "Fear, Uncertainty and Doubt — often used to manipulate markets", "Fundamental Upward Data", "Futures Under Development"],
        "answer": "Fear, Uncertainty and Doubt — often used to manipulate markets",
        "explanation": "FUD is often spread to push prices down so whales can accumulate at lower prices."
    },
    {
        "q": "What is the NVT Ratio?",
        "options": ["Net Volume Trading", "Network Value to Transactions — Bitcoin's version of P/E ratio", "New Volatility Threshold", "Net Value Transfer"],
        "answer": "Network Value to Transactions — Bitcoin's version of P/E ratio",
        "explanation": "High NVT suggests Bitcoin is overvalued relative to actual on-chain economic activity."
    },
    {
        "q": "What is a crypto exchange's order book?",
        "options": ["A record of completed trades", "A list of all pending buy and sell orders at various prices", "The exchange's revenue report", "A list of listed tokens"],
        "answer": "A list of all pending buy and sell orders at various prices",
        "explanation": "Order books show supply and demand at every price level — thin order books = more volatile."
    },
    {
        "q": "What is paper trading?",
        "options": ["Trading physical currency", "Simulated trading without real money to practice strategies", "Trading penny stocks", "Printing financial reports"],
        "answer": "Simulated trading without real money to practice strategies",
        "explanation": "Paper trading lets you test strategies risk-free — essential before risking real capital."
    },
    {
        "q": "What is a market order vs limit order?",
        "options": ["They are the same thing", "Market = execute immediately at any price; Limit = execute only at your specified price", "Limit executes faster", "Market orders cost more"],
        "answer": "Market = execute immediately at any price; Limit = execute only at your specified price",
        "explanation": "Use limit orders in volatile markets — market orders can fill at very different prices (slippage)."
    },
    {
        "q": "What is slippage in crypto trading?",
        "options": ["A broker error", "The difference between expected price and actual execution price", "A type of stablecoin depegging", "A withdrawal fee"],
        "answer": "The difference between expected price and actual execution price",
        "explanation": "High slippage occurs in low liquidity markets — your large order moves the price against you."
    },
]


# ============================================================
# QUIZ ENGINE
# ============================================================

def get_random_questions(n_per_category: int = 10) -> list:
    """Επιλέγει n τυχαίες ερωτήσεις από κάθε κατηγορία."""
    stocks = random.sample(STOCKS_QUESTIONS, min(n_per_category, len(STOCKS_QUESTIONS)))
    options = random.sample(OPTIONS_QUESTIONS, min(n_per_category, len(OPTIONS_QUESTIONS)))
    crypto = random.sample(CRYPTO_QUESTIONS, min(n_per_category, len(CRYPTO_QUESTIONS)))

    questions = []
    for q in stocks:  questions.append({**q, "category": "📈 Stocks"})
    for q in options: questions.append({**q, "category": "⚡ Options"})
    for q in crypto:  questions.append({**q, "category": "₿ Crypto"})

    random.shuffle(questions)
    return questions


def get_level(score: int, total: int) -> dict:
    """Επιστρέφει το επίπεδο βάσει score."""
    pct = score / total * 100
    if pct >= 80:
        return {
            "level": "Advanced",
            "emoji": "🏆",
            "color": "#00C853",
            "message": "Impressive knowledge! You're ready to use the full platform.",
            "plan": "Pro"
        }
    elif pct >= 50:
        return {
            "level": "Intermediate",
            "emoji": "⭐",
            "color": "#F59E0B",
            "message": "Good foundation! You'll get comfortable quickly.",
            "plan": "Entry"
        }
    else:
        return {
            "level": "Beginner",
            "emoji": "🌱",
            "color": "#7C3AED",
            "message": "Everyone starts somewhere! The platform will help you learn as you go.",
            "plan": "Entry"
        }


def show_quiz():
    """
    Εμφανίζει το quiz.
    Επιστρέφει True όταν ο χρήστης ολοκληρώσει.
    """

    st.markdown("""
    <style>
    .quiz-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .quiz-title {
        font-family: 'Syne', sans-serif;
        font-size: 1.6rem;
        font-weight: 800;
        color: #fff;
        margin-bottom: 0.3rem;
    }
    .quiz-subtitle {
        font-size: 0.82rem;
        color: rgba(255,255,255,0.4);
    }
    .question-card {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(124,58,237,0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .q-category {
        font-size: 0.7rem;
        color: rgba(167,139,250,0.7);
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .q-text {
        font-size: 0.95rem;
        color: #fff;
        font-weight: 500;
        line-height: 1.5;
        margin-bottom: 1rem;
    }
    .q-number {
        font-family: 'Syne', sans-serif;
        font-size: 0.75rem;
        color: rgba(255,255,255,0.25);
        margin-bottom: 0.3rem;
    }
    .progress-text {
        font-size: 0.78rem;
        color: rgba(255,255,255,0.35);
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .result-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(124,58,237,0.25);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    .result-emoji { font-size: 3rem; margin-bottom: 0.5rem; }
    .result-level {
        font-family: 'Syne', sans-serif;
        font-size: 1.8rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    .result-score {
        font-size: 1rem;
        color: rgba(255,255,255,0.5);
        margin-bottom: 1rem;
    }
    .result-message {
        font-size: 0.88rem;
        color: rgba(255,255,255,0.6);
        line-height: 1.6;
        margin-bottom: 1.5rem;
    }
    .category-breakdown {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-top: 1rem;
    }
    .stRadio > label {
        color: rgba(255,255,255,0.7) !important;
        font-size: 0.85rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Αρχικοποίηση quiz state
    if "quiz_questions" not in st.session_state:
        st.session_state.quiz_questions = get_random_questions(10)
        st.session_state.quiz_answers = {}
        st.session_state.quiz_submitted = False
        st.session_state.quiz_score = 0

    questions = st.session_state.quiz_questions
    total = len(questions)

    # ── RESULTS ──
    if st.session_state.quiz_submitted:
        score = st.session_state.quiz_score
        level_info = get_level(score, total)

        st.markdown(f"""
        <div class="result-card">
            <div class="result-emoji">{level_info['emoji']}</div>
            <div class="result-level" style="color:{level_info['color']}">{level_info['level']}</div>
            <div class="result-score">{score} / {total} correct ({score/total*100:.0f}%)</div>
            <div class="result-message">{level_info['message']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Category breakdown
        stocks_score = sum(1 for i, q in enumerate(questions)
                          if q["category"] == "📈 Stocks" and
                          st.session_state.quiz_answers.get(i) == q["answer"])
        options_score = sum(1 for i, q in enumerate(questions)
                           if q["category"] == "⚡ Options" and
                           st.session_state.quiz_answers.get(i) == q["answer"])
        crypto_score = sum(1 for i, q in enumerate(questions)
                          if q["category"] == "₿ Crypto" and
                          st.session_state.quiz_answers.get(i) == q["answer"])

        c1, c2, c3 = st.columns(3)
        c1.metric("📈 Stocks", f"{stocks_score}/10")
        c2.metric("⚡ Options", f"{options_score}/10")
        c3.metric("₿ Crypto", f"{crypto_score}/10")

        st.markdown(f"""
        <div style="background:rgba(124,58,237,0.1);border:1px solid rgba(124,58,237,0.25);
                    border-radius:10px;padding:1rem;margin:1rem 0;text-align:center;">
            <span style="color:#A78BFA;font-size:0.82rem;">
                💡 Recommended plan: <strong style="color:#fff">{level_info['plan']}</strong>
            </span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Continue to Terms & Disclaimer →", key="quiz_continue"):
            st.session_state.quiz_completed = True
            st.session_state.quiz_level = level_info["level"]
            st.session_state.quiz_recommended_plan = level_info["plan"]
            return True

        # Option to retake
        if st.button("Retake Quiz", key="quiz_retake"):
            for key in ["quiz_questions", "quiz_answers", "quiz_submitted", "quiz_score"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        return False

    # ── QUIZ ──
    st.markdown("""
    <div class="quiz-header">
        <div class="quiz-title">📚 Knowledge Check</div>
        <div class="quiz-subtitle">30 questions · Stocks, Options & Crypto · ~5 minutes</div>
    </div>
    """, unsafe_allow_html=True)

    answered = len(st.session_state.quiz_answers)
    st.markdown(f'<div class="progress-text">{answered} / {total} answered</div>',
                unsafe_allow_html=True)
    st.progress(answered / total)

    # Questions
    for i, q in enumerate(questions):
        with st.container():
            st.markdown(f"""
            <div class="question-card">
                <div class="q-number">Question {i+1} of {total}</div>
                <div class="q-category">{q['category']}</div>
                <div class="q-text">{q['q']}</div>
            </div>
            """, unsafe_allow_html=True)

            answer = st.radio(
                f"q_{i}",
                q["options"],
                key=f"quiz_q_{i}",
                label_visibility="collapsed",
                index=None,
            )

            if answer:
                st.session_state.quiz_answers[i] = answer

        st.markdown("<br>", unsafe_allow_html=True)

    # Submit
    all_answered = len(st.session_state.quiz_answers) == total

    if all_answered:
        if st.button("Submit Quiz →", key="quiz_submit"):
            score = sum(1 for i, q in enumerate(questions)
                       if st.session_state.quiz_answers.get(i) == q["answer"])
            st.session_state.quiz_score = score
            st.session_state.quiz_submitted = True
            st.rerun()
    else:
        remaining = total - len(st.session_state.quiz_answers)
        st.button(f"Answer {remaining} more question{'s' if remaining > 1 else ''} to submit",
                  disabled=True, key="quiz_submit_disabled")

    return False
