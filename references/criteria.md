# Screening Criteria

Defaults for the balance sheet screen. The user can override any of them ("loosen debt to 1.5", "only dividend payers"). Apply sector adjustments instead of one rule for everything: a bank and a software company have very different balance sheets.

## Hard filters (must pass)

| Metric | Default threshold | Why |
|--------|-------------------|-----|
| Debt-to-equity | < 1.0 | Limits fragility in a downturn |
| Interest coverage (EBIT / interest) | > 5x | Debt is easily serviced |
| Free cash flow (TTM) | Positive | Business funds itself |
| Current ratio | > 1.5 | Can cover near-term obligations |
| Share count trend (3 yr) | Flat or shrinking, dilution < 5% | Avoids quiet value erosion |

## Quality tilt (used for ranking, not exclusion)

- Revenue growth positive over the last 3 years
- Gross or operating margin stable or expanding
- Return on invested capital above ~10%
- Net cash or low net debt / EBITDA (< 2x)
- Consistent profitability (no loss years in the last 5)

## Sector adjustments

- **Financials (banks, insurers):** Skip debt-to-equity, current ratio, and interest coverage. Use CET1 / capital ratios, return on equity, and loan quality if available.
- **Utilities, REITs, telecom:** Allow debt-to-equity up to ~2.0 and interest coverage down to ~3x. Check payout and coverage of dividends.
- **Early growth / unprofitable tech:** Standard filters will exclude most. Only include if the user asks, and swap FCF for cash runway (> 24 months) and gross margin trend.
- **Energy and materials:** Judge through the cycle. Prefer net debt / EBITDA < 2x and positive FCF at mid-cycle prices.

## Data hygiene

- Use trailing-twelve-month or latest annual figures consistently within one scan, and say which.
- Do not mix reporting currencies without noting it.
- If a company restated or has one-off items distorting a number, mention it in the Main risk column.
