"""Repository-local Habitat 0.3.3 environment implementing paper-defined DSR."""

from typing import TYPE_CHECKING, Optional

import gym
import habitat
from habitat import Dataset
from habitat.core.environments import RLTaskEnv
from habitat.gym.gym_wrapper import HabGymWrapper

from dsr_math import (
    replace_constant_success_bonus,
    terminal_stop_diagnostics,
)

if TYPE_CHECKING:
    from omegaconf import DictConfig


class DynamicSuccessRewardRLTaskEnv(RLTaskEnv):
    """Replace the constant success bonus with Dynamic Success Reward.

    Standard Habitat 0.3.3 already adds ``success_reward`` on a successful
    episode. This subclass adds only the difference between the DSR value and
    that constant, leaving slack and geodesic-progress rewards unchanged.
    Failed STOP actions receive no success bonus and no custom penalty.
    """

    _distance_measure_name = "distance_to_goal"

    def __init__(
        self, config: "DictConfig", dataset: Optional[Dataset] = None
    ) -> None:
        super().__init__(config=config, dataset=dataset)
        self._success_distance = float(
            self.config.task.measurements.success.success_distance
        )
        if self._success_distance <= 0.0:
            raise ValueError("success distance must be positive")

    def get_reward(self, observations):
        reward = super().get_reward(observations)
        if not self._episode_success():
            return reward

        metrics = self._env.get_metrics()
        if self._distance_measure_name not in metrics:
            raise KeyError(
                "DSR requires the distance_to_goal measurement in Habitat metrics"
            )

        return replace_constant_success_bonus(
            base_reward=float(reward),
            episode_success=True,
            success_reward=float(self._success_reward),
            success_distance=self._success_distance,
            final_distance=float(metrics[self._distance_measure_name]),
        )


class StopDiagnosticRLTaskEnv(RLTaskEnv):
    """Keep standard rewards and expose terminal STOP failure categories."""

    def get_info(self, observations):
        info = dict(super().get_info(observations))
        stop_called = bool(
            getattr(self._env.task, "is_stop_called", False)
        )
        success = bool(self._episode_success())
        episode_over = bool(self._env.episode_over)
        stop_flag, premature_flag, non_stop_flag = terminal_stop_diagnostics(
            episode_over=episode_over,
            stop_called=stop_called,
            episode_success=success,
        )
        info["stop_called"] = stop_flag
        info["premature_stop"] = premature_flag
        info["non_stop_failure"] = non_stop_flag
        return info


@habitat.registry.register_env(name="DynamicSuccessRewardGymHabitatEnv")
class DynamicSuccessRewardGymHabitatEnv(gym.Wrapper):
    """Gym wrapper used by Habitat-Baselines vector environments."""

    def __init__(
        self, config: "DictConfig", dataset: Optional[Dataset] = None
    ) -> None:
        base_env = DynamicSuccessRewardRLTaskEnv(
            config=config, dataset=dataset
        )
        super().__init__(HabGymWrapper(env=base_env))


@habitat.registry.register_env(name="StopDiagnosticGymHabitatEnv")
class StopDiagnosticGymHabitatEnv(gym.Wrapper):
    """Standard Habitat reward/dynamics plus numeric STOP diagnostics."""

    def __init__(
        self, config: "DictConfig", dataset: Optional[Dataset] = None
    ) -> None:
        base_env = StopDiagnosticRLTaskEnv(config=config, dataset=dataset)
        super().__init__(HabGymWrapper(env=base_env))
