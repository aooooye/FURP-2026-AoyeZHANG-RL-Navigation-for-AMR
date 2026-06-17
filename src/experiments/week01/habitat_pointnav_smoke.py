from pathlib import Path

import habitat
from habitat.config.default import get_config
from habitat.config.read_write import read_write
from habitat.datasets.pointnav.pointnav_dataset import PointNavDatasetV1
from habitat.utils.test_utils import sample_non_stop_action
from PIL import Image


CONFIG = "habitat-lab/habitat/config/benchmark/nav/pointnav/pointnav_habitat_test.yaml"
OUT_DIR = Path("week01_evidence")
OUT_DIR.mkdir(exist_ok=True)

config = get_config(CONFIG)
if not PointNavDatasetV1.check_config_paths_exist(config.habitat.dataset):
    raise RuntimeError("Habitat PointNav test dataset is missing")

dataset = habitat.make_dataset(
    id_dataset=config.habitat.dataset.type,
    config=config.habitat.dataset,
)

with read_write(config):
    config.habitat.environment.max_episode_steps = 10
    if "teleport" in config.habitat.task.actions:
        del config.habitat.task.actions["teleport"]

with habitat.Env(config=config, dataset=dataset) as env:
    observations = env.reset()
    actions = []
    for _ in range(5):
        action = sample_non_stop_action(env.action_space)
        observations = env.step(action)
        actions.append(str(action))

    metrics = env.get_metrics()
    rgb = observations.get("rgb")
    if rgb is not None:
        Image.fromarray(rgb).save(OUT_DIR / "pointnav_smoke_frame.png")

    lines = [
        "Week 1 Habitat PointNav smoke test",
        f"config: {CONFIG}",
        f"episodes_loaded: {len(dataset.episodes)}",
        f"current_episode_id: {env.current_episode.episode_id}",
        f"scene_id: {env.current_episode.scene_id}",
        f"steps_executed: {len(actions)}",
        f"actions: {actions}",
        f"episode_over: {env.episode_over}",
        f"metrics: {metrics}",
        f"rgb_saved: {OUT_DIR / 'pointnav_smoke_frame.png'}",
    ]
    (OUT_DIR / "pointnav_smoke.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
