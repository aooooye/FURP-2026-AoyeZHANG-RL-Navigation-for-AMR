"""Pure, testable helpers for the frozen PointNav robustness protocol."""

from __future__ import annotations

import hashlib
import json
import math
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping, MutableMapping, Optional

import numpy as np


RNG_ALGORITHM = "sha256-box-muller-v1"
POINTGOAL_SENSOR_UUID = "pointgoal_with_gps_compass"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(payload: Any) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _random_key(
    noise_seed: int,
    scene_id: str,
    episode_id: str,
    channel: str,
    step_index: Optional[int],
) -> bytes:
    # A canonical JSON array avoids delimiter collisions while preserving the
    # frozen logical key: seed | scene | episode | channel | step.
    return json.dumps(
        [
            int(noise_seed),
            str(scene_id),
            str(episode_id),
            str(channel),
            None if step_index is None else int(step_index),
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def stateless_standard_normal(
    noise_seed: int,
    scene_id: str,
    episode_id: str,
    channel: str,
    step_index: Optional[int] = None,
) -> float:
    """Return one scheduling-independent standard-normal sample.

    SHA-256 supplies two open-interval uniform variates and Box-Muller maps
    them to a normal variate. This avoids Python ``hash`` and NumPy RNG-state
    dependence across vector-worker scheduling.
    """

    digest = hashlib.sha256(
        _random_key(noise_seed, scene_id, episode_id, channel, step_index)
    ).digest()
    denominator = float(1 << 64)
    u1 = (int.from_bytes(digest[:8], "big") + 0.5) / denominator
    u2 = (int.from_bytes(digest[8:16], "big") + 0.5) / denominator
    return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)


def clipped_gaussian(
    *,
    mean: float,
    std: float,
    lower: float,
    upper: float,
    noise_seed: int,
    scene_id: str,
    episode_id: str,
    channel: str,
    step_index: Optional[int] = None,
) -> float:
    if std < 0.0:
        raise ValueError("standard deviation must be non-negative")
    if lower > upper:
        raise ValueError("lower bound exceeds upper bound")
    value = mean + std * stateless_standard_normal(
        noise_seed, scene_id, episode_id, channel, step_index
    )
    return min(upper, max(lower, value))


def wrap_radians(angle: float) -> float:
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def sample_localization_biases(
    protocol: Mapping[str, Any],
    *,
    noise_seed: int,
    scene_id: str,
    episode_id: str,
) -> tuple[float, float]:
    model = protocol["noise_models"]["localization"]
    distance = model["distance_bias_m"]
    bearing = model["bearing_bias_deg"]
    distance_bias_m = clipped_gaussian(
        mean=0.0,
        std=float(distance["std"]),
        lower=float(distance["clip"][0]),
        upper=float(distance["clip"][1]),
        noise_seed=noise_seed,
        scene_id=scene_id,
        episode_id=episode_id,
        channel="localization_distance_bias",
    )
    bearing_bias_deg = clipped_gaussian(
        mean=0.0,
        std=float(bearing["std"]),
        lower=float(bearing["clip"][0]),
        upper=float(bearing["clip"][1]),
        noise_seed=noise_seed,
        scene_id=scene_id,
        episode_id=episode_id,
        channel="localization_bearing_bias",
    )
    return distance_bias_m, bearing_bias_deg


def sample_action_amount(
    protocol: Mapping[str, Any],
    *,
    action_name: str,
    noise_seed: int,
    scene_id: str,
    episode_id: str,
    step_index: int,
) -> Optional[float]:
    model = protocol["noise_models"]["actuation"]
    if action_name == "move_forward":
        spec = model["forward_distance_m"]
        channel = "forward_distance"
    elif action_name in ("turn_left", "turn_right"):
        spec = model["turn_angle_deg"]
        channel = "turn_angle"
    else:
        return None
    return clipped_gaussian(
        mean=float(spec["nominal"]),
        std=float(spec["std"]),
        lower=float(spec["clip"][0]),
        upper=float(spec["clip"][1]),
        noise_seed=noise_seed,
        scene_id=scene_id,
        episode_id=episode_id,
        channel=channel,
        step_index=step_index,
    )


def perturb_pointgoal(
    observations: Mapping[str, Any],
    *,
    distance_bias_m: float,
    bearing_bias_deg: float,
    enabled: bool,
    sensor_uuid: str = POINTGOAL_SENSOR_UUID,
) -> Mapping[str, Any]:
    """Apply polar PointGoal noise without modifying the input mapping."""

    if not enabled:
        return observations
    if sensor_uuid not in observations:
        raise KeyError(f"missing PointGoal observation: {sensor_uuid}")
    pointgoal = np.asarray(observations[sensor_uuid])
    if pointgoal.ndim != 1 or pointgoal.shape[0] != 2:
        raise ValueError(
            f"expected a 2-D polar PointGoal vector, got {pointgoal.shape}"
        )
    noisy = pointgoal.copy()
    noisy[0] = max(0.0, float(pointgoal[0]) + distance_bias_m)
    noisy[1] = wrap_radians(
        float(pointgoal[1]) + math.radians(bearing_bias_deg)
    )
    copied: MutableMapping[str, Any] = dict(observations)
    copied[sensor_uuid] = noisy
    return copied


@contextmanager
def temporary_actuation_amount(
    agent: Any, action_key: Any, amount: Optional[float]
) -> Iterator[None]:
    """Temporarily change one Habitat-Sim ActionSpec and always restore it."""

    if amount is None:
        yield
        return
    action_space = agent.agent_config.action_space
    if action_key not in action_space:
        raise KeyError(f"simulator action is absent: {action_key!r}")
    actuation = action_space[action_key].actuation
    if actuation is None or not hasattr(actuation, "amount"):
        raise TypeError(f"simulator action has no scalar actuation amount: {action_key!r}")
    original = float(actuation.amount)
    actuation.amount = float(amount)
    try:
        yield
    finally:
        actuation.amount = original


def action_trace_entry(step_index: int, action_name: str, amount: Optional[float]) -> bytes:
    return (
        json.dumps(
            {
                "action": action_name,
                "amount": amount,
                "step_index": int(step_index),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def json_scalar(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    raise TypeError(f"unsupported telemetry scalar: {type(value).__name__}")
