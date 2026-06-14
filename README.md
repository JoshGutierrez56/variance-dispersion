# variance-dispersion
> Options Club Session 2 — Variance Trading Game | September 30, 2026

## The Game
Players quote bid-ask spreads on the **variance** (sum of squared deviations) of a set of cards, not the sum itself. This introduces a new challenge: variance is non-linear, harder to estimate, and more sensitive to outliers than the mean.

Each round, community cards are revealed one by one. Players update their variance estimates using Bayesian updating and quote tighter spreads as uncertainty resolves. The player with the best-calibrated spreads (fewest adverse selections, tightest profitable quotes) wins.

## Connection to Real Markets
Variance trading is the foundation of the VIX, variance swaps, and volatility arbitrage. Market makers at Citadel Securities and Jane Street quote variance daily. This session builds intuition for why vol is mean-reverting, why variance buyers and sellers disagree, and how realized vs. implied variance creates profit opportunities.

## Coming Soon
- variance_simulator/ package
- Bayesian variance estimator
- Realized vs. implied variance P&L
- Volatility surface visualization

## The Three Sessions
| Session | Date | Game |
|---------|------|------|
| 1 — Vanilla Market Making | Sept 16 | mm-simulator |
| 2 — Variance Trading | Sept 30 | variance-dispersion (this repo) |
| 3 — Options Payoff | Oct 14 | greeks-payoffs |
