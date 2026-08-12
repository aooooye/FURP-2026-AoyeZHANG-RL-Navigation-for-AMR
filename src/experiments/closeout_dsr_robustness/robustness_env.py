"""Repository-local Habitat environment for controlled test-time noise."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Optional

import gym
import habitat
import numpy as np
from habitat import Dataset
from habitat.gym.gym_wrapper import HabGymWrapper
from habitat.sims.habitat_simulator.actions import HabitatSimActions

from dynamic_success_reward_env import StopDiagnosticRLTaskEnv
from protocol_guard import load_json, validate_protocol
from robustness_core import (
    action_trace_entry,
    perturb_pointgoal,
    sample_action_amount,
    sample_localization_biases,
    sha256_file,
    temporary_actuation_amount,
)

if TYPE_CHECKING:
    from omegaconf import DictConfig


class RobustnessRLTaskEnv(StopDiagnosticRLTaskEnv):
    """Standard evaluation plus observation/action perturbations and telemetry."""

    def __init__(
        self, config: "DictConfig", dataset: Optional[Dataset] = None
    ) -> None:
        super().__init__(config=config, dataset=dataset)
        protocol_path = Path(self._required_env("ROBUSTNESS_PROTOCOL_PATH"))
        expected_protocol_hash = self._required_env("ROBUSTNESS_PROTOCOL_SHA256")
        if sha256_file(protocol_path) != expected_protocol_hash:
            raise ValueError("robustness protocol SHA-256 mismatch in worker")
        self._protocol = load_json(protocol_path)
        validate_protocol(self._protocol)

        self._phase = self._required_env("ROBUSTNESS_RUN_PHASE")
        self._condition = self._required_env("ROBUSTNESS_CONDITION")
        self._method = self._required_env("ROBUSTNESS_METHOD")
        self._training_seed = int(self._required_env("ROBUSTNESS_TRAIN_SEED"))
        self._noise_seed = int(self._required_env("ROBUSTNESS_NOISE_SEED"))
        self._checkpoint_sha256 = self._required_env("ROBUSTNESS_CHECKPOINT_SHA256")
        self._checkpoint_manifest_sha256 = self._required_env(
            "ROBUSTNESS_CHECKPOINT_MANIFEST_SHA256"
        )
        self._noise_manifest_sha256 = self._required_env(
            "ROBUSTNESS_NOISE_MANIFEST_SHA256"
        )
        self._run_identity_sha256 = self._required_env(
            "ROBUSTNESS_RUN_IDENTITY_SHA256"
        )
        self._telemetry_dir = Path(
            self._required_env("ROBUSTNESS_EPISODE_SHARD_DIR")
        )
        self._telemetry_dir.mkdir(parents=True, exist_ok=True)

        if self._condition not in self._protocol["conditions"]:
            raise ValueError(f"unknown robustness condition: {self._condition}")
        self._localization_enabled = self._condition in (
            "localization",
            "combined",
        )
        self._actuation_enabled = self._condition in ("actuation", "combined")
        self._sensor_uuid = str(self._protocol["pointgoal_sensor_uuid"])
        self._episode_initialized = False

    @staticmethod
    def _required_env(name: str) -> str:
        value = os.environ.get(name, "").strip()
        if not value:
            raise RuntimeError(f"required robustness environment variable is unset: {name}")
        return value

    def _start_episode(self) -> None:
        episode = self._env.current_episode
        self._scene_id = str(episode.scene_id)
        self._episode_id = str(episode.episode_id)
        self._step_index = 0
        self._episode_reward = 0.0
        self._action_counts = {
            "stop": 0,
            "move_forward": 0,
            "turn_left": 0,
            "turn_right": 0,
        }
        self._action_trace = hashlib.sha256()
        if self._localization_enabled:
            (
                self._distance_bias_m,
                self._bearing_bias_deg,
            ) = sample_localization_biases(
                self._protocol,
                noise_seed=self._noise_seed,
                scene_id=self._scene_id,
                episode_id=self._episode_id,
            )
        else:
            self._distance_bias_m = 0.0
            self._bearing_bias_deg = 0.0
        self._telemetry_written = False
        self._episode_initialized = True

    def _noisy_observations(self, observations: Mapping[str, Any]):
        return perturb_pointgoal(
            observations,
            distance_bias_m=self._distance_bias_m,
            bearing_bias_deg=self._bearing_bias_deg,
            enabled=self._localization_enabled,
            sensor_uuid=self._sensor_uuid,
        )

    def reset(self, *args, return_info: bool = False, **kwargs):
        result = super().reset(*args, return_info=return_info, **kwargs)
        self._start_episode()
        if return_info:
            observations, info = result
            return self._noisy_observations(observations), info
        return self._noisy_observations(result)

    def _action_name(self, args: tuple[Any, ...], kwargs: Mapping[str, Any]) -> str:
        if "action" in kwargs:
            action = kwargs["action"]
        elif args:
            action = args[0]
        else:
            raise ValueError("step called without an action")
        if isinstance(action, Mapping):
            action = action["action"]
        if isinstance(action, (int, np.integer)):
            return str(self._env.task.get_action_name(int(action)))
        return str(action)

    @staticmethod
    def _sim_action_key(action_name: str):
        if action_name == "move_forward":
            return HabitatSimActions.move_forward
        if action_name == "turn_left":
            return HabitatSimActions.turn_left
        if action_name == "turn_right":
            return HabitatSimActions.turn_right
        return None

    def _write_episode(self, info: Mapping[str, Any]) -> None:
        if self._telemetry_written:
            raise RuntimeError(
                f"duplicate terminal telemetry for {self._scene_id}/{self._episode_id}"
            )
        required = self._protocol["metrics"]
        missing = [name for name in required if name not in info and name != "reward"]
        if missing:
            raise KeyError(f"terminal Habitat info is missing metrics: {missing}")
        record = {
            "schema_version": 1,
            "phase": self._phase,
            "condition": self._condition,
            "training_method": self._method,
            "training_seed": self._training_seed,
            "noise_seed": self._noise_seed,
            "scene_id": self._scene_id,
            "episode_id": self._episode_id,
            "checkpoint_sha256": self._checkpoint_sha256,
            "protocol_sha256": self._required_env("ROBUSTNESS_PROTOCOL_SHA256"),
            "checkpoint_manifest_sha256": self._checkpoint_manifest_sha256,
            "noise_manifest_sha256": self._noise_manifest_sha256,
            "run_identity_sha256": self._run_identity_sha256,
            "steps": int(getattr(self._env, "_elapsed_steps", self._step_index)),
            "success": bool(info["success"]),
            "spl": float(info["spl"]),
            "distance_to_goal": float(info["distance_to_goal"]),
            "reward": float(self._episode_reward),
            "stop_called": bool(info["stop_called"]),
            "premature_stop": bool(info["premature_stop"]),
            "non_stop_failure": bool(info["non_stop_failure"]),
            "localization_distance_bias_m": float(self._distance_bias_m),
            "localization_bearing_bias_deg": float(self._bearing_bias_deg),
            "action_counts": self._action_counts,
            "action_trace_sha256": self._action_trace.hexdigest(),
        }
        shard = self._telemetry_dir / f"episodes-{os.getpid()}.jsonl"
        with shard.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
            handle.flush()
        self._telemetry_written = True

    def step(self, *args, **kwargs):
        if not self._episode_initialized:
            raise RuntimeError("robustness environment must be reset before step")
        action_name = self._action_name(args, kwargs)
        amount = None
        if self._actuation_enabled:
            amount = sample_action_amount(
                self._protocol,
                action_name=action_name,
                noise_seed=self._noise_seed,
                scene_id=self._scene_id,
                episode_id=self._episode_id,
                step_index=self._step_index,
            )
        action_key = self._sim_action_key(action_name)
        agent = self._env._sim.get_agent(
            self._env._sim.habitat_config.default_agent_id
        )
        with temporary_actuation_amount(agent, action_key, amount):
            observations, reward, done, info = super().step(*args, **kwargs)

        self._episode_reward += float(reward)
        self._action_counts.setdefault(action_name, 0)
        self._action_counts[action_name] += 1
        self._action_trace.update(
            action_trace_entry(self._step_index, action_name, amount)
        )
        self._step_index += 1
        if done:
            self._write_episode(info)
        return self._noisy_observations(observations), reward, done, info


@habitat.registry.register_env(name="RobustnessGymHabitatEnv")
class RobustnessGymHabitatEnv(gym.Wrapper):
    """Habitat-Baselines Gym wrapper with unchanged discrete action indices."""

    def __init__(
        self, config: "DictConfig", dataset: Optional[Dataset] = None
    ) -> None:
        base_env = RobustnessRLTaskEnv(config=config, dataset=dataset)
        super().__init__(HabGymWrapper(env=base_env))
