# Week 7 - 2026-08-11

**Attended this week's meeting:** Yes

**Progress this week**

- Completed the pinned Habitat 0.3.3 runtime on the RTX 4070 server and passed the CUDA, EGL rendering, dataset, configuration, and Habitat revision checks.
- Recovered from a Pillow metadata conflict, missing `git-lfs`, and unresolved LFS scene pointers without changing the frozen experiment protocol. Failed bootstrap attempts were preserved separately from formal experiment evidence.
- Completed six fresh fixed-budget training runs: baseline and DSR for training seeds `100`, `200`, and `300`. All six runs finished with `status=passed`.
- Completed six corresponding fixed evaluations using evaluation seed `2026` and 100 episodes per policy. All evaluations finished with `status=passed` and used the final checkpoint produced by the matching fresh training run.
- Verified checkpoint paths and SHA-256 values between every training/evaluation pair.
- Obtained the following three-seed mean results:
  - Baseline Success: `88.67%`; DSR Success: `95.67%` (`+7.00` percentage points).
  - Baseline SPL: `76.65%`; DSR SPL: `83.37%` (`+6.72` percentage points).
  - Mean final distance improved from `0.3438 m` to `0.2758 m`.
  - Premature STOP decreased from `8.67%` to `2.00%` (`-6.67` percentage points).
- Completed a strict evidence audit confirming that the final aggregate contains exactly six fresh formal evaluations and excludes diagnostic, smoke, and training rolling-window metrics.
- Recovered the complete result evidence locally and created the first-stage archive with a recorded SHA-256 hash.

**Challenges & blockers**

- The evaluation profile contains only two Habitat test scenes and three training seeds. The results are descriptive and do not establish statistical significance or generalization to unseen Gibson/HM3D scenes.
- Windows could not copy 99 video files individually because of long paths. The videos remain preserved in the complete tar archive and were not regenerated.
- The DSR result must be described as a controlled reward ablation using an existing method, not as a newly invented RL algorithm.

**Next steps**

- Test whether the clean-condition DSR gain survives controlled target-localization and action-execution errors.
- Freeze a separate evaluation-only robustness protocol before inspecting noisy results.
- Reuse the same six final checkpoints without retraining or fine-tuning.
- Keep noisy results separate from the clean comparison.

**Hours spent (optional):** 40

**Evidence copies in this repository**

- `src/results/closeout_dsr/comparison.json`
- `src/results/closeout_dsr/comparison.md`
- `src/results/closeout_dsr/wp5_evidence_audit_20260811.md`
- `src/results/closeout_dsr/`

**Local evidence archive**

- `artifacts/archives/closeout_dsr_remote_20260811.tar`
- SHA-256: `0ea7645ce5ff97498932f68fb57af3777b5417de00302e94e6e8abed3c6af40e`
