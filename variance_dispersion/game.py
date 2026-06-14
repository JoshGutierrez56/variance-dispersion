"""Game engine for Session 2 — Variance Trading.

Players quote bid-ask spreads on the variance (sum of squared deviations)
of a set of cards, not the mean. Each round one community card is revealed
(time-to-reveal = time-to-expiration). As uncertainty resolves, true variance
becomes more certain and quotes should tighten.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .estimator import BayesianVarianceEstimator, VarianceEstimate


@dataclass
class GameConfig:
    """Configuration for one variance trading game."""
    n_players: int = 4
    n_hidden_per_player: int = 2
    n_community: int = 6
    card_min: int = 2
    card_max: int = 14
    prior_mean: float = 100.0
    prior_strength: float = 2.0
    seed: Optional[int] = 42

    @property
    def total_hidden(self) -> int:
        return self.n_players * self.n_hidden_per_player

    @property
    def total_cards(self) -> int:
        return self.total_hidden + self.n_community


@dataclass
class Quote:
    """A player's quote on variance for a given round."""
    player_id: int
    bid: float
    ask: float
    mid: float
    spread: float
    round_num: int = 0
    revealed_sum: float = 0.0
    true_variance: Optional[float] = None


@dataclass
class GameState:
    """Live state of the variance game."""
    community_revealed: List[int] = field(default_factory=list)
    hidden_cards: List[List[int]] = field(default_factory=list)
    community_remaining: List[int] = field(default_factory=list)
    round_num: int = 0
    quote_log: List[Quote] = field(default_factory=list)
    prior_mean: float = 100.0

    @property
    def true_sum(self) -> float:
        hidden_sum = sum(c for hand in self.hidden_cards for c in hand)
        return float(sum(self.community_revealed)) + hidden_sum

    @property
    def n_hidden_remaining(self) -> int:
        return sum(len(h) for h in self.hidden_cards)

    @property
    def variance_observed(self) -> Optional[float]:
        """Variance of observed community cards (sample variance)."""
        if len(self.community_revealed) < 2:
            return None
        arr = [float(c) for c in self.community_revealed]
        return float(np.var(arr, ddof=1))

    @property
    def true_variance_all_cards(self) -> float:
        """True population variance across all cards (hidden + community)."""
        all_vals = [c for hand in self.hidden_cards for c in hand]
        all_vals += [float(c) for c in self.community_revealed]
        return float(np.var(all_vals, ddof=0))


class VarianceGame:
    """Manages one full variance trading game."""

    def __init__(self, config: GameConfig):
        self.config = config
        self.estimators: List[BayesianVarianceEstimator] = []
        self._rng = random.Random(config.seed)

    def _draw_cards(self, n: int) -> List[int]:
        return [self._rng.randint(self.config.card_min, self.config.card_max)
                for _ in range(n)]

    def reset(self) -> GameState:
        """Deal a new game."""
        hidden = [self._draw_cards(self.config.n_hidden_per_player)
                  for _ in range(self.config.n_players)]
        community = self._draw_cards(self.config.n_community)

        # Create one estimator per player (each sees different information)
        self.estimators = [
            BayesianVarianceEstimator(
                prior_mean=self.config.prior_mean,
                prior_strength=self.config.prior_strength,
            )
            for _ in range(self.config.n_players)
        ]

        return GameState(
            community_revealed=[],
            hidden_cards=hidden,
            community_remaining=community,
            round_num=0,
            prior_mean=self.config.prior_mean,
        )

    def reveal_card(self, state: GameState) -> Optional[int]:
        """Reveal the next community card."""
        if not state.community_remaining:
            return None
        card = state.community_remaining.pop(0)
        state.community_revealed.append(card)
        state.round_num += 1

        # All estimators see the revealed card for variance calculation
        for est in self.estimators:
            est.update(float(card))

        # Update true_variance on all quotes
        tv = state.true_variance_all_cards
        for q in state.quote_log:
            q.true_variance = tv

        return card

    def player_estimate(self, player_id: int, state: GameState) -> VarianceEstimate:
        """Get this player's current variance estimate."""
        return self.estimators[player_id].estimate()

    def record_quote(
        self, state: GameState, player_id: int,
        bid: float, ask: float,
    ) -> Quote:
        """Record a player's variance quote and compute error."""
        est = self.player_estimate(player_id, state)
        tv = state.true_variance_all_cards

        q = Quote(
            player_id=player_id,
            bid=round(max(0, bid), 2),
            ask=round(ask, 2),
            mid=round((bid + ask) / 2, 2),
            spread=round(ask - max(0, bid), 2),
            round_num=state.round_num,
            revealed_sum=state.true_sum,
            true_variance=tv,
        )
        state.quote_log.append(q)
        return q

    def settle(self, state: GameState) -> dict:
        """Settle the game. Returns per-player P&L based on quote accuracy."""
        tv = state.true_variance_all_cards
        results = {}

        for player_id in range(self.config.n_players):
            player_quotes = [q for q in state.quote_log if q.player_id == player_id]

            if not player_quotes:
                results[player_id] = {
                    "pnl": 0.0,
                    "avg_mid_error": 0.0,
                    "n_quotes": 0,
                    "true_variance": tv,
                }
                continue

            # P&L based on how close last quote mid was to true variance
            last = player_quotes[-1]
            pnl = -(last.mid - tv) ** 2 / 100.0  # scaled down for readability

            avg_mid_error = sum(abs(q.mid - q.true_variance)
                                for q in player_quotes) / len(player_quotes)
            avg_spread = sum(q.spread for q in player_quotes) / len(player_quotes)

            results[player_id] = {
                "pnl": round(pnl, 4),
                "avg_mid_error": round(avg_mid_error, 2),
                "avg_spread": round(avg_spread, 2),
                "n_quotes": len(player_quotes),
                "true_variance": round(tv, 2),
            }

        return results

    def summary(self, state: GameState) -> dict:
        """Full game summary."""
        settle = self.settle(state)
        tv = state.true_variance_all_cards
        observed_var = state.variance_observed

        return {
            "true_variance": round(tv, 2),
            "observed_variance": round(observed_var, 2) if observed_var else None,
            "n_rounds": state.round_num,
            "n_hidden_remaining": state.n_hidden_remaining,
            "players_revealed": [len(state.community_revealed)] * self.config.n_players,
            "player_results": settle,
        }
