from __future__ import annotations

import platform
from pathlib import Path

import habitat_sim
import numpy as np
from PIL import Image


ROOT = Path.home()
OUT_DIR = ROOT / "week01_habitat_evidence"
OUT_DIR.mkdir(exist_ok=True)

SCENE = ROOT / "habitat-lab" / "data" / "scene_datasets" / "habitat-test-scenes" / "skokloster-castle.glb"
NAVMESH = ROOT / "habitat-lab" / "data" / "scene_datasets" / "habitat-test-scenes" / "skokloster-castle.navmesh"


def build_simulator() -> habitat_sim.Simulator:
    sim_cfg = habitat_sim.SimulatorConfiguration()
    sim_cfg.scene_id = str(SCENE)
    sim_cfg.enable_physics = False

    rgb_sensor = habitat_sim.CameraSensorSpec()
    rgb_sensor.uuid = "rgb"
    rgb_sensor.sensor_type = habitat_sim.SensorType.COLOR
    rgb_sensor.resolution = [256, 256]
    rgb_sensor.position = [0.0, 1.5, 0.0]

    agent_cfg = habitat_sim.agent.AgentConfiguration()
    agent_cfg.sensor_specifications = [rgb_sensor]

    return habitat_sim.Simulator(habitat_sim.Configuration(sim_cfg, [agent_cfg]))


sim = build_simulator()
try:
    if NAVMESH.exists():
        sim.pathfinder.load_nav_mesh(str(NAVMESH))

    agent = sim.initialize_agent(0)
    state = habitat_sim.AgentState()
    if sim.pathfinder.is_loaded:
        state.position = sim.pathfinder.get_random_navigable_point()
    else:
        state.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    agent.set_state(state)

    observations = sim.get_sensor_observations()
    rgb = observations["rgb"]
    if rgb.shape[-1] == 4:
        rgb_to_save = rgb[:, :, :3]
    else:
        rgb_to_save = rgb

    frame_path = OUT_DIR / "habitat_test_scene_frame.png"
    Image.fromarray(rgb_to_save).save(frame_path)

    agent_position = [float(state.position[i]) for i in range(3)]

    lines = [
        "Habitat-Sim test scene render smoke test",
        f"python: {platform.python_version()}",
        f"habitat_sim: {habitat_sim.__file__}",
        f"scene: {SCENE}",
        f"scene_present: {SCENE.exists()}",
        f"navmesh: {NAVMESH}",
        f"navmesh_present: {NAVMESH.exists()}",
        f"pathfinder_loaded: {sim.pathfinder.is_loaded}",
        f"agent_position: {agent_position}",
        f"rgb_shape: {list(rgb.shape)}",
        f"rgb_dtype: {rgb.dtype}",
        f"rgb_min: {int(rgb_to_save.min())}",
        f"rgb_max: {int(rgb_to_save.max())}",
        f"frame_saved: {frame_path}",
        "result: ok",
    ]
finally:
    sim.close()

output = OUT_DIR / "habitat_test_scene_render_smoke.txt"
output.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
print(f"saved: {output}")
