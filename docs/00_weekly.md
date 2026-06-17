# Weekly Progress Log

> Update this file **every week**. Add a new entry at the top for each week.
> This is the first thing we check during review. Keep it honest and specific — it also feeds your attendance record (Rule 1).

**How to use:** copy the *Week template* block below for each new week. Newest week goes at the top.

---

## Week template — copy me

### Week N — YYYY-MM-DD

**Attended this week's meeting:** Yes / No (if No, did you email leave? Yes / No)

**Progress this week**
- _What did you actually do / finish?_

**Challenges & blockers**
- _What got in the way? What are you stuck on?_

**Next steps**
- _What will you do next week?_

**Hours spent (optional):** _e.g. 6h_

---

<!-- =================  YOUR ENTRIES BELOW  ================= -->

### Week 1 - 2026-06-17

**Attended this week's meeting:** Not recorded in the available logs.

**Progress this week**
- Chose the **Habitat PointNav baseline** as the first baseline for the RL Navigation for AMR route, and limited Week 1 scope to Habitat RL setup plus smoke-test evidence.
- Set up a reproducible Habitat stack on `ubuntu@10.190.20.110` using Ubuntu 26.04, `micromamba`, Python 3.9.19, Habitat-Sim `0.3.3`, Habitat-Baselines `0.3.3`, and PyTorch `2.8.0+cu128`.
- Verified the current GPU/CUDA stack: NVIDIA GeForce RTX 3060, NVIDIA driver `595.71.05`, CUDA `13.2` from `nvidia-smi`, and CUDA available in PyTorch.
- Installed/verified required system packages for Habitat, including rendering/runtime dependencies and `git-lfs` for Habitat test scene downloads.
- Downloaded the Habitat test scenes and the Habitat test PointNav dataset under the Habitat-Lab data directory.
- Ran the Habitat-Sim renderer smoke test on `skokloster-castle.glb`; it loaded the scene, executed 5 simulator actions, and saved an RGB frame.
- Ran the Week 1 Habitat PointNav smoke test with `habitat/config/benchmark/nav/pointnav/pointnav_habitat_test.yaml`; it loaded `10000` test episodes, reset one episode, executed 5 non-STOP actions, and saved an RGB frame without a runtime crash.
- Recorded the initial random smoke-test metrics: `distance_to_goal=11.814451217651367`, `success=0.0`, `spl=0.0`, and `distance_to_goal_reward=-0.0`. This is expected for a 5-step smoke test; the result is environment evidence, not a trained baseline score.

**Challenges & blockers**
- Habitat-Sim initially needed missing Ubuntu runtime libraries, especially `libOpenGL.so.0`; installing `libopengl0` resolved this.
- Habitat test data required `git-lfs`; without it the test scenes could not be fetched cleanly.
- The full research baseline is not reproduced yet. Week 1 only proves that the simulator, dataset path, and PointNav environment can execute.
- Meeting attendance was not confirmed in the available project logs, so this entry does not claim attendance.

**Next steps**
- In Week 2, select the exact Habitat-Baselines PointNav baseline command/config and decide whether to begin with a pretrained/random-policy evaluation or a tiny PPO training run.
- Choose the cited PointNav / Habitat baseline paper or official baseline reference to replicate.
- Run the first measurable baseline with fixed seed, config, command, dataset split, and output directory recorded.
- Track the required RL navigation metrics: success rate, SPL/path efficiency, episode reward, collision rate, and training stability.
- Start collecting at least 3 successful and 3 failed PointNav cases once a real baseline evaluation runs.
- Add a meeting note after the first confirmed weekly meeting or supervisor check-in.

**Hours spent (optional):** Not recorded.

**Evidence copies in this repository**
- Environment note: `src/results/week01/week01_environment_note.md`
- PointNav smoke-test output: `src/results/week01/pointnav_smoke.txt`
- PointNav smoke-test frame: `src/results/week01/pointnav_smoke_frame.png`
- Habitat-Sim render smoke-test output: `src/results/week01/habitat_test_scene_render_smoke.txt`
- Habitat-Sim smoke-test frame: `src/results/week01/habitat_test_scene_frame.png`
- Habitat import/path smoke-test output: `src/results/week01/habitat_vlnce_smoke.txt`
- PyTorch CUDA smoke-test output: `src/results/week01/torch_cuda_smoke.txt`
- NVIDIA-SMI output: `src/results/week01/nvidia_smi.txt`
- Habitat setup log: `src/results/week01/habitat_rl_setup_20260616_142535.log`
- PointNav smoke-test script: `src/experiments/week01/habitat_pointnav_smoke.py`
