"""Bayesian variance estimator for the variance trading game.

Players use this to update their estimate of the true variance
as community cards are revealed one by one.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import List


@dataclass
class VarianceEstimate:
 """Current estimate of true variance with uncertainty bounds."""
 mean: float = 0.0
 std: float = 0.0
 lower_95: float = 0.0
 upper_95: float = 0.0
 n_observed: int = 0


class BayesianVarianceEstimator:
 """Updates variance estimate as cards are revealed.

 Uses conjugate prior (inverse-gamma) for variance estimation.
 Tightens confidence interval as more cards are observed.
 """

 def __init__(self, prior_mean: float = 100.0, prior_strength: float = 2.0):
 self.prior_mean = prior_mean
 self.prior_strength = prior_strength
 self.observed: List[float] = []

 def update(self, card_value: float):
 """Add a newly revealed card value and update estimate."""
 self.observed.append(card_value)

 def estimate(self) -> VarianceEstimate:
 """Return current posterior variance estimate."""
 n = len(self.observed)
 if n < 2:
 return VarianceEstimate(
 mean=self.prior_mean,
 std=self.prior_mean * 0.5,
 lower_95=self.prior_mean * 0.1,
 upper_95=self.prior_mean * 2.0,
 n_observed=n,
 )

 sample_var = float(np.var(self.observed, ddof=1))
 posterior_mean = (self.prior_strength * self.prior_mean + n * sample_var) / (self.prior_strength + n)
 posterior_std = posterior_mean / np.sqrt(self.prior_strength + n)

 return VarianceEstimate(
 mean=posterior_mean,
 std=posterior_std,
 lower_95=max(0, posterior_mean - 1.96 * posterior_std),
 upper_95=posterior_mean + 1.96 * posterior_std,
 n_observed=n,
 )

 def suggested_spread(self) -> tuple[float, float]:
 """Return (bid, ask) based on current uncertainty."""
 est = self.estimate()
 half_spread = 1.96 * est.std
 return (max(0, est.mean - half_spread), est.mean + half_spread)

 def reset(self):
 """Reset for a new game."""
 self.observed = []
