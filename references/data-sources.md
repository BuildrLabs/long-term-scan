# Data Sources and Tool Mapping

Load tool schemas with `tool_search` before first use. Do not guess parameter names. Use whichever of these is connected and fall back down the list.

## Prices (for the quarterly SMA regime check)
- **Robinhood** historical bars tool (equity historicals) with the longest span and a weekly or daily interval. Request an explicit date range going back 13+ years. Read-only: never call any order, exercise, or watchlist-modifying tool.
- Fallback: fetch a public historical price page with `web_fetch` or ask the user to upload a CSV (date, open, high, low, close).

## Fundamentals
- **Robinhood** equity fundamentals and company financials for ratios and multi-period statements.
- **Robinhood** SEC filing facts for debt, interest expense, operating income, cash flow, and share count when ratios are missing.
- **Bigdata** screener and company tearsheets for batch screening and quick cross-checks.

## Sector and news context
- **Bigdata** market tearsheet and search for sector performance, macro themes, and recent news.
- Fallback: `web_search` for "sector performance this quarter" and recent catalysts.

## Practical tips
- Batch candidates into as few calls as the tools allow. Screen on fundamentals first so you only pull long price histories for survivors.
- Save price bars to a temporary JSON file in the shape the script expects, then run the script once for all survivors.
- Always report the as-of date of every data source.
