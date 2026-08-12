"""Register the local robustness environment, then run Habitat-Baselines."""

import multiprocessing as mp
import runpy


mp.set_forkserver_preload(
    ["dynamic_success_reward_env", "robustness_env"]
)

import robustness_env  # noqa: F401,E402


if __name__ == "__main__":
    runpy.run_module("habitat_baselines.run", run_name="__main__")
