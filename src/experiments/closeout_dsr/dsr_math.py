"""Pure Dynamic Success Reward math, independent of Habitat imports."""

from math import exp, isfinite
from typing import Tuple


def dynamic_success_reward(
    success_reward: float,
    success_distance: float,
    final_distance: float,
) -> float:
    """Return Grande et al.'s success reward for a successful STOP.

    The caller must invoke this only when the episode success measure is true.
    """

    if not isfinite(success_reward) or success_reward < 0.0:
        raise ValueError("success_reward must be non-negative")
    if not isfinite(success_distance) or success_distance <= 0.0:
        raise ValueError("success_distance must be positive")
    if not isfinite(final_distance) or final_distance < 0.0:
        raise ValueError("final_distance must be non-negative")

    return success_reward * exp(
        (success_distance - final_distance) / success_distance
    )


def replace_constant_success_bonus(
    base_reward: float,
    episode_success: bool,
    success_reward: float,
    success_distance: float,
    final_distance: float,
) -> float:
    """Replace Habitat's already-added constant bonus with DSR on success."""

    if not episode_success:
        return base_reward
    return base_reward - success_reward + dynamic_success_reward(
        success_reward=success_reward,
        success_distance=success_distance,
        final_distance=final_distance,
    )


def terminal_stop_diagnostics(
    episode_over: bool,
    stop_called: bool,
    episode_success: bool,
) -> Tuple[float, float, float]:
    """Return stop_called, premature_stop, and non_stop_failure flags."""

    if not episode_over:
        return 0.0, 0.0, 0.0
    return (
        float(stop_called),
        float(stop_called and not episode_success),
        float(not stop_called and not episode_success),
    )
