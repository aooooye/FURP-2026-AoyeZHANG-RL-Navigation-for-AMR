# WP5 closeout evidence audit

Audit time: 2026-08-11 20:41:29 +08:00  
Remote matrix end: 2026-08-11 20:20:26 +08:00  
Scope: frozen Habitat test-scenes baseline-versus-DSR matrix only

## Gate result

- Matrix launcher: `status=passed`, `exit_code=0`.
- Six fresh training runs: all `status=passed`.
- Six fixed 100-episode evaluations: all `status=passed`.
- Each evaluation `checkpoint_path.txt` exactly equals the corresponding fresh training `final_checkpoint_path.txt`.
- Each copied checkpoint SHA-256 matches its evaluation `checkpoint_sha256.txt`.
- `comparison.json` contains exactly six records: baseline/DSR × seeds 100/200/300.
- Every aggregate source is a fresh evaluation summary. Diagnostic and smoke outputs are absent from the aggregate.

## Fresh run provenance

| Condition | Seed | Train | Eval | Path match | Checkpoint SHA-256 | Eval summary SHA-256 |
|---|---:|---|---|---|---|---|
| baseline | 100 | passed | passed | yes | `c1b6e8e2dc6b13c59bc8beb9b3de1368ac23098d16c5e1a9be640130e49f89a7` | `e5f5e07e4e6a2f045e87a901eb16effb4b094691a5332e40e82aef83d8e1746a` |
| baseline | 200 | passed | passed | yes | `5f66e962d19a534fca9cac76c684d349ef9f77660cc225174def8dd6537d3566` | `73e1d85bde37345d224627d2d9e2c0761fea496f850d4da50281c7636e170e7b` |
| baseline | 300 | passed | passed | yes | `848555bba5a965552fea7b9ba92f37ec2d610eb1f02499cb8f4518819913dd2a` | `22faef92293b00a66ad5637f9b39beed775aa8da262c07f925cfe1ae84afad1a` |
| DSR | 100 | passed | passed | yes | `0ce83fd3945ea7a716889d1911b7c741d32893255f90c8470d11381e22e68816` | `fbf52dd544619d273085fa3c8dff815055e03d8222c971b84fdf2d15bace1218` |
| DSR | 200 | passed | passed | yes | `99525d206c846e9c827769070650eb7b397b6b9a401396e288a661a51a5c6449` | `57a158acde9d9cb0f158e08ff8883fddbec82a7164ddc52511e156741ceef683` |
| DSR | 300 | passed | passed | yes | `67dca5803a66db646cf7ce5a711740ed6b8b42861c0fbdc8672e797717070a3c` | `b75c4ad177d809b7705ae0810e2fe9c5701f359bc32e19ce8f6b972cf252ac31` |

## Fixed evaluation results

| Condition | Seed | Success | SPL | Final distance | Reward | Premature STOP | Non-STOP failure |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 100 | 94.00% | 82.26% | 0.1202 m | 7.7631 | 6.00% | 0.00% |
| baseline | 200 | 88.00% | 77.33% | 0.5469 m | 6.9688 | 7.00% | 5.00% |
| baseline | 300 | 84.00% | 70.36% | 0.3644 m | 7.0502 | 13.00% | 3.00% |
| DSR | 100 | 92.00% | 75.90% | 0.4863 m | 6.9845 | 3.00% | 5.00% |
| DSR | 200 | 99.00% | 87.76% | 0.1038 m | 7.7950 | 0.00% | 1.00% |
| DSR | 300 | 96.00% | 86.46% | 0.2372 m | 7.6735 | 3.00% | 1.00% |

| Condition | Success mean ± sample SD | SPL mean ± sample SD | Final distance mean ± sample SD | Premature STOP mean ± sample SD | Non-STOP failure mean ± sample SD |
|---|---:|---:|---:|---:|---:|
| baseline | 88.67% ± 5.03% | 76.65% ± 5.98% | 0.3438 ± 0.2141 m | 8.67% ± 3.79% | 2.67% ± 2.52% |
| DSR | 95.67% ± 3.51% | 83.37% ± 6.50% | 0.2758 ± 0.1941 m | 2.00% ± 1.73% | 2.33% ± 2.31% |

DSR minus baseline: Success `+7.00` percentage points; SPL `+6.72` percentage points; final distance `-0.0681 m`; reward `+0.2236`; premature STOP `-6.67` percentage points; non-STOP failure `-0.33` percentage points.

## Aggregate and archive hashes

- `comparison.json`: `b39e728d5aa9d4be0998c47b33061cfd4eb47835214c732a7b6624f7e3a89fb6`
- `comparison.md`: `144fd2226af588ccfabde421ad70c67f560b46c802d221d63a11520a6da68676`
- `matrix_launcher/run_status.txt`: `9f7502e95faa313dd7732e7745186eb78b8c2589f58bfd18adfb7fc7bc6dd93e`
- Complete remote-results archive: `artifacts/archives/closeout_dsr_remote_20260811.tar`
- Complete archive SHA-256: `0ea7645ce5ff97498932f68fb57af3777b5417de00302e94e6e8abed3c6af40e`

The local result directory contains all short-path training, evaluation, checkpoint, log, status, and aggregate artifacts. Windows rejected 99 video names because their full paths exceeded its path-length limit; all videos remain intact in the complete tar archive and on the remote server.

## Preserved failed setup evidence

- `bootstrap_server_20260811T074916Z.log`: stopped at the Pillow metadata conflict.
- `bootstrap_resume_20260811T083549Z.log`: passed `pip check`, then stopped because git-lfs was unavailable.
- `bootstrap_resume_20260811T084251Z.log`: downloaded data, then stopped because scene files were still LFS pointers.
- `bootstrap_resume_20260811T084748Z.log`: completed environment, EGL render, CUDA, data, and revision validation.

These are infrastructure-recovery attempts. They were preserved and were not mixed into the six-run aggregate.

## Claim boundary

This is a controlled three-seed reward ablation on the two-scene Habitat test-scenes fallback. It is not a Gibson/HM3D benchmark, a statistical-significance claim, a new RL algorithm, or real-robot validation. Training rolling-window metrics are not evaluation results.
