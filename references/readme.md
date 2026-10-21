# Long-Term Toolkit: Read Me

*Claude reads this to the user when they type `readme`. Present it as written, in order, without cutting commands or adding commentary. End with the closing question.*

---

**Welcome.** This toolkit helps you invest for the long term in two ways: **`scan`** finds quality companies at sensible entry points, and **`learn`** teaches you how to understand what the scan shows you.

## Set up (2 minutes)
1. **Turn on code execution and file creation** in Claude's settings. The scan uses a small script for the math.
2. **Connect your data (optional but better):** a brokerage connector such as Robinhood for prices and fundamentals, and Bigdata for news and sector context. It is used for reading only, and nothing is ever ordered. Without connectors, Claude uses web search, and you can upload a price CSV (date, open, high, low, close).
3. **Test it:** type `scan AAPL MSFT NVDA`.

## What `scan` does
Type `scan` and Claude:
1. Checks which **sectors** are leading and what **news** matters.
2. Screens for strong **balance sheets**: low debt, solid interest coverage, positive free cash flow, healthy liquidity, little dilution.
3. Reads each stock's **regime** on the 3-month chart using the 50 SMA: bullish, bearish, or in transition.
4. Looks for the setup that fits the regime: in uptrends, **pullbacks** that cross the SMA 50; in downtrends, it **waits for a confirmed bottom**.
5. Adds **RSI** for context on how stretched a move is.
6. Delivers a short ranked table with a thesis, main risk, and invalidation level for each name.

## What `learn` does
Type `learn` and Claude asks about your level, goal, and time, then builds a **personal curriculum** from 13 short lessons: how markets work, risk and compounding, reading financial statements, valuation, charts and regimes, investor psychology, and building a routine. You get one lesson at a time, each ending with a check question, plus quizzes, a glossary, and a capstone project.

## Starter prompts
**Scan**
- `scan`: broad scan of large and mid cap US stocks
- `scan semiconductors`: one sector
- `scan AAPL MSFT NVDA`: your own tickers
- `scan with SMA 20`: shorter average, more results
- `loosen debt to 1.5` or `only dividend payers`: change the screen
- `is NVDA in an uptrend on the quarterly chart?`: check one stock
- `why was this flagged?`: explain any result

**Learn**
- `learn`: build my curriculum
- `learn balance sheets`: one topic, no plan
- `start` or `next`: next lesson
- `quiz me` · `glossary` · `adjust plan`

**Technical questions**
- `how do I trade a pullback to a moving average?`: Claude answers, then points you to further resources

## Good to know
- **Setups are rare by design.** A quarterly 50 SMA is roughly a 12.5-year average, so expect a short list, and sometimes an empty one. Claude will say so honestly.
- **It moves slowly.** Run `scan` about once a quarter; results change little in between.
- **Educational only.** This is research and teaching, not financial advice. It never places trades or tells you what to buy.
- Newer companies with less than about 13 years of history are flagged as lower confidence.

**More from the creator:** the ORB 15-Minute Claude Skill and *The Master Blueprint to Profitable Trading* are available at https://lifeoscoach.wixsite.com/eldryn-steele-tradin

**Closing question:** Want to run a quick test scan or build your curriculum first?
