# Li Haisheng (1240009615)

- GitHub: @lhs58
- 负责部分：环境 / 构建 / 工作负载 / 测量流水线 / 结果汇总（Roles A–C）

## Commits

| Commit | Date | What |
|---|---|---|
| `9ff4807` | 2026-10-23 | `repo:` initial scaffold for the AddressSanitizer reproduction |
| `79ed665` | 2026-10-31 | `build:` pin clang-14 and make measurements deterministic |
| `8e7c3c5` | 2026-10-31 | `results:` first full measurement session, n=3, 5 benchmarks × 3 modes |
| `988d6e5` | 2026-11-07 | `figures:` give Fig. 2 error bars and state the measured RSS spread |
| `018886c` | 2026-11-07 | `ext:` sweep the heap redzone size (negative result: the knob is clamped) |
| `76c611f` | 2026-11-15 | `results:` first independent n=5 session (75 measurements) |
| `833a420` | 2026-11-15 | `results:` two more independent n=5 sessions (150 measurements) |
| `ced5184` | 2026-11-15 | `scripts:` separate within-session noise from between-session drift |
| `c3eea01` | 2026-11-15 | `results:` regenerate summary and figures from all four sessions |

## Detail

- Pinned toolchain: `Dockerfile` (Ubuntu 22.04 + clang-14), `Makefile` targets
  (`build/run/summarize/variance/figures/doctor/env/extension/clean`), `scripts/env.sh`,
  commit-message hook installer.
- Five benchmarks in `bench/` plus `bench/common.h` (the one-CSV-row contract, `VmHWM` vs `VmPeak`)
  and `scripts/sanity_bug_check.sh` (the `make doctor` target).
- Measurement pipeline: `scripts/run.sh`, `scripts/summarize.py`, `scripts/variance.py`; the four
  committed sessions in `results/raw/` (270 measured runs) and `results/summary.md`,
  `results/variance.md`.
- Documents: `docs/claims.md`, `docs/deviations.md` (D1–D20), `docs/plan.md`, `docs/environment.md`.
- Diagnostics that changed the protocol: the `setarch -R` requirement (27.5 % of instrumented runs
  died with `SIGSEGV` without it, D14) and the discovery that `VmPeak` is unusable under modern
  shadow reservation (D13).
