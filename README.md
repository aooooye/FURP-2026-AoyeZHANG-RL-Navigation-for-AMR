# FURP-2026: RL Navigation for AMR

> **Faculty Undergraduate Research Practice (FURP)**
> Undergraduate Research Group · Faculty of Science and Engineering · University of Nottingham Ningbo China

This is your project home for the FURP programme. **Fork this template**, rename your repo, fill in the content each week, and share it with us (or make it public) so we can follow your progress and review your weekly work.

---

## Getting started (do this in Week 1)

1. **Fork / use this template** to create your own repository.
2. **Rename your repo** following the naming convention:
   ```
   FURP-2026/YourName-ProjectTag
   # e.g. FURP-2026/AoyeZHANG-RL-Navigation-for-AMR
   ```
3. **Give us access:** either make the repo **public**, or **share it** with the research group accounts (ask your project lead for the usernames to add as collaborators).
4. **Fill in this README** — replace the placeholders in the *Project Info* section below.
5. **Start your weekly log** from the index in [`docs/00_weekly.md`](docs/00_weekly.md); each completed week is stored in a standalone file.

---

## Project Info

| Field | Your entry |
|---|---|
| Student name(s) | Aoye ZHANG |
| Project title | End-to-End Navigation for an AMR with Reinforcement Learning |
| Project tag | RL-Navigation-for-AMR |
| Track | Research |
| Supervising faculty | Tianxiang Cui |
| Project lead | Aoye ZHANG |
| Team or individual | Individual |
| Cited paper being replicated | *Habitat: A Platform for Embodied AI Research* (Savva et al., ICCV 2019), with PPO training context from *DD-PPO* (Wijmans et al., ICLR 2020) |

**One-line summary:** This project reproduces a controlled Habitat PointNav PPO baseline, evaluates Dynamic Success Reward across three training seeds, and tests whether its clean-condition benefit survives frozen synthetic localization and actuation errors.

## Current result

- In the clean controlled comparison, DSR improved mean Success from `88.67%` to `95.67%` (`+7.00` percentage points) and mean SPL from `76.65%` to `83.37%` (`+6.72` percentage points).
- In the evaluation-only robustness study, the preregistered combined Success robustness advantage was `-2.56` percentage points, with only `1/3` training seeds favorable. The formal conclusion is: **No DSR robustness advantage was observed.**
- Both stages use two Habitat `test-scenes`. The evidence is descriptive and is not a Gibson/HM3D benchmark, statistical-significance result, real-robot result, or Sim2Real validation.

Start with [`src/README.md`](src/README.md) for the experiment/evidence map and [`docs/00_weekly.md`](docs/00_weekly.md) for the weekly-log index.

Additional project-owned assets have been consolidated inside this repository:

- [`docs/README.md`](docs/README.md): documentation, infrastructure, and reference index.
- [`artifacts/README.md`](artifacts/README.md): local transfer/evidence archives and integrity records. Large archives remain intentionally ignored by Git.

---

## Repository structure

This structure is **mandatory** — please keep it intact.

```
/docs
 ├── 00_weekly.md         ← weekly-log index and template
 ├── WeekNN.md            ← one standalone progress log per recorded week
 └── meeting_notes/       ← key takeaways from all team meetings
/src                      ← implementation, protocols, and result evidence
FURP_Showcase.pdf         ← required final poster; not yet present
```

- **`docs/00_weekly.md`** — index and template for the standalone weekly logs.
- **`docs/meeting_notes/`** — one file per meeting with key takeaways and action items.
- **`src/`** — all your code, scripts, notebooks, and experiment materials.
- **`FURP_Showcase.pdf`** — required final poster filename. The repository currently contains only `FURP_Showcase_PLACEHOLDER.md`, so poster delivery is not yet complete.

---

## The three rules for your certificate

To earn your FURP certificate, **all three** must be satisfied:

1. **Attend > 50%** of programme activities (weekly meetings, workshops, scheduled sessions — online or in person).
2. **Submit a poster** — place it as `FURP_Showcase.pdf` in this repo root.
3. **Present at the Poster Showcase** — in person (strongly preferred), or send a stand-in if you truly cannot attend.

> Miss any one of the three, and the certificate is not awarded this round.

**Research Track — minimum for certification:** successful replication of a cited paper with at least **10% innovation** (reproduce the work *and* add something new).

---

## Weekly cadence

Every week, you should:

- ✅ Add or update the appropriate standalone weekly file listed in [`docs/00_weekly.md`](docs/00_weekly.md)
- ✅ Log meeting notes in [`docs/meeting_notes/`](docs/meeting_notes/)
- ✅ Attend the weekly meeting (online or in person)

Consistent weekly engagement is the backbone of a successful FURP project — and it feeds directly into your attendance (Rule 1).

---

## Leave & withdrawal

Any **leave of absence** or **withdrawal** must be notified to us **by email** — a verbal or chat message is not sufficient.

- **Leave:** email *before* the session where possible, state the date(s) and reason. Note that leave still counts against the >50% attendance rule.
- **Withdrawal:** email us to formally withdraw so we can free your project slot and update records.
- **Switching tracks:** email the project lead with the subject *"Project Transfer Request"* and CC your supervising faculty member.

> No email = no record. Always put leave and withdrawal in writing.

---

## Quick checklist

- [x] Forked the template and renamed the repo (`FURP-2026-AoyeZHANG-RL-Navigation-for-AMR`)
- [x] Made the repo public **or** shared it with the research group
- [x] Filled in the *Project Info* table above
- [x] Started `docs/00_weekly.md`
- [ ] (By Showcase) Added `FURP_Showcase.pdf` to the repo root

---

*Bridging the gap between classroom knowledge and cutting-edge research.*
