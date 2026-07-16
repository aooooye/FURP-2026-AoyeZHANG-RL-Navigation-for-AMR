# `/src` — your work goes here

Put all your code, scripts, notebooks, experiment configs, and project materials in this folder.

**Research Track reminder:** your project should reproduce a cited paper and add **at least 10% innovation** (something new on top of the replication). Organise this folder however suits your project, but keep it tidy enough that a reviewer can follow what you did.

Suggested (not mandatory) layout:

```
/src
 ├── README.md          ← how to run your code / what's here
 ├── data/              ← datasets (or links if too large to commit)
 ├── experiments/       ← scripts, notebooks, configs
 └── results/           ← outputs, figures, logs
```

> Don't commit large datasets or secrets/credentials. Link to data sources instead.

## Current experiment layout

```text
src/
├── experiments/
│   ├── week01/                 # Habitat PointNav random-action smoke test
│   ├── week02/                 # preflight, deterministic follower, tiny PPO run
│   └── week3-4/                # fixed-budget PPO training and evaluation workflow
└── results/
    ├── week01/                 # verified environment and smoke-test evidence
    ├── week02/                 # completed Week 2 evidence and metric record
    └── week3-4/                # Weeks 3 & 4 baseline, metrics, and case evidence
```

Execution instructions are in `src/experiments/week02/README.md` and `src/experiments/week3-4/README.md`. Verified runs are stored under the matching `src/results/` week directories; Habitat training itself ran on the Ubuntu/Habitat host.
