# Source and experiment evidence

This directory contains the Habitat PointNav implementation, experiment protocols, and locally recovered evidence for the project. Start with the summary below rather than treating every smoke, diagnostic, or training log as a formal result.

## Current research status

The controlled study has two completed stages:

1. **Clean baseline versus DSR.** Across training seeds `100/200/300`, mean Success was `88.67%` for baseline and `95.67%` for Dynamic Success Reward (DSR), a difference of `+7.00` percentage points. Mean SPL improved by `+6.72` percentage points and premature STOP decreased by `6.67` percentage points.
2. **Controlled test-time robustness.** The same six final checkpoints were evaluated under localization error, actuation error, and their combination. The preregistered combined Success robustness advantage was `-2.56` percentage points, with only `1/3` training seeds in the favorable direction. The formal interpretation is: **No DSR robustness advantage was observed.**

These are descriptive results from two Habitat `test-scenes`, not a Gibson/HM3D benchmark, statistical-significance result, real-robot result, or Sim2Real validation.

## Directory map

```text
src/
├── experiments/
│   ├── week01/                    # environment and PointNav smoke script
│   ├── week02/                    # preflight, shortest-path control, tiny PPO
│   ├── week3-4/                    # fixed-budget learned baseline workflow
│   ├── closeout_dsr/              # frozen clean baseline-vs-DSR experiment
│   └── closeout_dsr_robustness/   # frozen evaluation-only robustness study
└── results/
    ├── week01/                    # environment and smoke evidence
    ├── week02/                    # control/tiny-PPO evidence and review record
    ├── week3-4/                    # learned baseline evaluation and cases
    ├── closeout_dsr/              # clean three-seed formal matrix
    └── closeout_dsr_robustness/   # 6 clean + 54 noisy formal evaluations
```

## Evidence guide

| Stage | Protocol or implementation | Primary result | Human-readable review |
|---|---|---|---|
| Week 1 environment gate | [`experiments/week01/`](experiments/week01/) | [`results/week01/`](results/week01/) | [`../docs/Week01.md`](../docs/Week01.md) |
| Week 2 controlled pipeline | [`experiments/week02/README.md`](experiments/week02/README.md) | [`results/week02/`](results/week02/) | [`../docs/Week02.md`](../docs/Week02.md) |
| Week 3 learned baseline | [`experiments/week3-4/README.md`](experiments/week3-4/README.md) | [`results/week3-4/README.md`](results/week3-4/README.md) | [`../docs/week3-4.md`](../docs/week3-4.md) |
| Clean baseline vs DSR | [`experiments/closeout_dsr/README.md`](experiments/closeout_dsr/README.md) | [`results/closeout_dsr/comparison.json`](results/closeout_dsr/comparison.json) | [`results/closeout_dsr/comparison.md`](results/closeout_dsr/comparison.md) |
| Test-time robustness | [`experiments/closeout_dsr_robustness/README.md`](experiments/closeout_dsr_robustness/README.md) | [`results/closeout_dsr_robustness/comparison.json`](results/closeout_dsr_robustness/comparison.json) | [`results/closeout_dsr_robustness/conclusion.md`](results/closeout_dsr_robustness/conclusion.md) |

## Result hierarchy

- Formal clean claims come only from the six fresh evaluations aggregated in `results/closeout_dsr/comparison.json`.
- Formal robustness claims come only from the exact 60-run matrix aggregated in `results/closeout_dsr_robustness/comparison.json`.
- Smoke runs validate execution only. Diagnostic runs, training rolling-window metrics, and old checkpoints are not formal performance records.
- The robustness results do not overwrite or invalidate the clean result: the supported narrative is **clean improvement, but no observed robustness advantage under the frozen synthetic-noise protocol**.

## Large local artifacts

Checkpoints (`*.pth`), TensorBoard events, videos, and complete archives may be ignored by Git. A Git clone alone is therefore not a complete evidence backup. The verified external archives are:

- `artifacts/archives/closeout_dsr_remote_20260811.tar` (SHA-256: `0ea7645ce5ff97498932f68fb57af3777b5417de00302e94e6e8abed3c6af40e`)
- `artifacts/archives/closeout_dsr_robustness_20260812.tar` (SHA-256: `8319275aa62145f4977c2cd6588c1c760705af23bb637fb43a4fac06edf55cf1`)

Do not commit datasets, credentials, or unreviewed large binary artifacts.
