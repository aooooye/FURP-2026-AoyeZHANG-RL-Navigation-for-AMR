#!/usr/bin/env python3
"""Run a deterministic PointNav oracle/control on Habitat test episodes."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import habitat
import numpy as np
from habitat.config.default import get_config
from habitat.config.read_write import read_write
from habitat.datasets.pointnav.pointnav_dataset import PointNavDatasetV1
from habitat.tasks.nav.shortest_path_follower import ShortestPathFollower
from PIL import Image


DEFAULT_CONFIG = (
    "habitat-lab/habitat/config/benchmark/nav/pointnav/"
    "pointnav_habitat_test.yaml"
)


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--max-steps", type=int, default=500)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    config = get_config(args.config)
    if not PointNavDatasetV1.check_config_paths_exist(config.habitat.dataset):
        raise RuntimeError("Habitat PointNav test dataset or scenes are missing")

    dataset = habitat.make_dataset(
        id_dataset=config.habitat.dataset.type,
        config=config.habitat.dataset,
    )

    with read_write(config):
        config.habitat.environment.max_episode_steps = args.max_steps
        if "teleport" in config.habitat.task.actions:
            del config.habitat.task.actions["teleport"]

    records: list[dict[str, Any]] = []
    successes = 0

    with habitat.Env(config=config, dataset=dataset) as env:
        for index in range(args.episodes):
            observations = env.reset()
            episode = env.current_episode
            goal = episode.goals[0]
            goal_radius = getattr(goal, "radius", None)
            if goal_radius is None:
                try:
                    goal_radius = config.habitat.task.measurements.success.success_distance
                except AttributeError:
                    goal_radius = config.habitat.simulator.forward_step_size

            follower = ShortestPathFollower(
                env.sim,
                float(goal_radius),
                return_one_hot=False,
            )

            actions: list[int] = []
            no_path = False
            while not env.episode_over and len(actions) < args.max_steps:
                action = follower.get_next_action(goal.position)
                if action is None:
                    no_path = True
                    break
                observations = env.step(action)
                actions.append(int(action))

            metrics = json_safe(env.get_metrics())
            success = bool(metrics.get("success", 0.0))
            successes += int(success)

            rgb = observations.get("rgb")
            frame_path = args.output_dir / f"episode_{index + 1:02d}_final.png"
            if rgb is not None:
                Image.fromarray(rgb).save(frame_path)

            record = {
                "index": index + 1,
                "episode_id": str(episode.episode_id),
                "scene_id": str(episode.scene_id),
                "geodesic_distance": json_safe(episode.info.get("geodesic_distance")),
                "steps": len(actions),
                "success": success,
                "no_path": no_path,
                "metrics": metrics,
                "final_frame": str(frame_path),
            }
            records.append(record)
            print(json.dumps(record, ensure_ascii=False, sort_keys=True))

    required_successes = math.ceil(args.episodes * 2 / 3)
    summary = {
        "config": args.config,
        "episodes_requested": args.episodes,
        "episodes_run": len(records),
        "successes": successes,
        "required_successes": required_successes,
        "passed": successes >= required_successes,
    }

    with (args.output_dir / "shortest_path_episodes.jsonl").open(
        "w", encoding="utf-8"
    ) as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    (args.output_dir / "shortest_path_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
