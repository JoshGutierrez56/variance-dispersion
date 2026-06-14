# variance-dispersion — Session 2 placeholder
# Full implementation coming before September 30, 2026
__version__ = "0.1.0"

from .estimator import VarianceEstimate, BayesianVarianceEstimator
from .game import GameConfig, GameState, Quote, VarianceGame

__all__ = [
    "VarianceEstimate",
    "BayesianVarianceEstimator",
    "GameConfig",
    "GameState",
    "Quote",
    "VarianceGame",
]
