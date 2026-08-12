"""Register the project-local DSR environment, then run Habitat-Baselines."""

import multiprocessing as mp
import runpy

# Habitat VectorEnv defaults to forkserver. Preloading the registration module
# guarantees that clean workers can resolve the custom habitat.env_task.
mp.set_forkserver_preload(["dynamic_success_reward_env"])

# Importing this module registers DynamicSuccessRewardGymHabitatEnv.
import dynamic_success_reward_env  # noqa: F401,E402


if __name__ == "__main__":
    # Execute the upstream module's real __main__ path so Hydra registration and
    # compatibility checks stay identical to the pinned Habitat-Baselines code.
    runpy.run_module("habitat_baselines.run", run_name="__main__")
