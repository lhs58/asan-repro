# Six-week plan

Hard external constraints (from the course instructions):

- Repositories are checked **every Sunday at 23:59**; at least one meaningful
  commit must land in each week. A missed week cannot be recovered.
- Every commit message must contain the committer's student ID and full name.
- The final version must be tagged `v1.0`.
- Nothing larger than 50 MB, no build outputs, no disk images, no credentials.

Six checks between now and the presentation:
**10/25 · 11/01 · 11/08 · 11/15 · 11/22 · 11/29**, then presentation **12/01**.

---

## Week 1 — 10/22 → 10/25 (first check)

**Goal:** the repository exists, is public, builds, and has already produced one
real number.

| Task | Owner | Done when |
|---|---|---|
| Form the group, collect student ID + name + GitHub handle for all four | lead | posted in the group chat |
| Every member sets their own `git config user.name/user.email` | all | `git log --format='%an <%ae>'` shows four distinct authors by week 2 |
| `docker build` + `make build` succeeds | env | five binaries in each of `build/{base,asan,asanw}/` |
| `make doctor` reports all four bug classes detected | env | four "detected" lines, one "clean" line |
| First `make run` + `make summarize` completes | measure | a `results/raw/*.csv` file is committed |
| Submit the group form with the repository URL | lead | screenshot of the confirmation |

**Exit criterion for the Sunday check:** at least one commit containing the
container, the build system and a first raw CSV.

## Week 2 — 10/26 → 11/01

**Goal:** the measurement is trustworthy, not just running.

- Tune the iteration counts so each baseline run is 1–3 s (edit `args_for` in
  `scripts/run.sh`), and record the final numbers in the README.
- Establish noise control: pin to a core (`CPU_PIN=1`), fix the CPU governor if
  possible, close background load, and run three separate sessions to see
  whether session-to-session variance exceeds run-to-run variance.
- Write `docs/environment.md` into the repository (`make env`).
- **11/01 is the paper-change deadline.** If by then nothing builds, this is the
  moment to switch — by email to the TA, not silently.

## Week 3 — 11/02 → 11/08

**Goal:** the first complete `Paper vs Ours` table.

- Full run: 5 benchmarks × 3 modes × ≥5 repetitions, one session.
- Fill in C1 and C2 rows; compute the mean slowdown and the memory increase.
- Sanity-check the checksum column is identical across modes — if it is not, the
  instrumented build is computing something different and the timings are void.
- Produce the first two figures (bar chart of slowdown per benchmark; memory
  increase per benchmark).

## Week 4 — 11/09 → 11/15

**Goal:** the discrepancy analysis exists, with evidence rather than guesses.

- Explain each benchmark that differs from the paper's analogue by more than
  ~30 %: is it the workload, the compiler, the allocator, or the hardware?
- Controlled re-run for the top two explanations: change **one** factor and
  measure (`-O0` vs `-O2`; `max_redzone` 32 vs default; `quarantine` 0 vs 256 MB).
- Vote on the extension experiment (default proposal: **compiler generation
  sweep**, clang-14 vs a second Clang version, same binaries otherwise).

## Week 5 — 11/16 → 11/22

**Goal:** the extension is finished and interpreted against the paper's claim.

- Run the one-factor extension, ≥5 repetitions, same session and machine.
- Add the result to `docs/deviations.md` if it reveals a setting that mattered.
- Draft the report sections *Reproduction Setup*, *Results*, *Analysis of
  Discrepancies*.

## Week 6 — 11/23 → 11/29

**Goal:** submission-ready.

- Finish the report: introduction and claims, extension, conclusion, references.
- Add the **contribution statement** and the **AI usage statement** (both are
  explicitly required by the writing-quality criterion).
- Verify reproducibility claim: clone into a fresh directory, follow the README
  literally, confirm `make all` works without editing paths.
- Tag `v1.0`, check `git log` for four distinct authors, confirm no file over
  50 MB (`git ls-files -z | xargs -0 du -h | sort -h | tail`).

## 12/01 — presentation

Separate instruction document; not covered here.

---

## Role split (adjust to reality)

| Role | Owns | Never |
|---|---|---|
| A — environment | Dockerfile, Makefile, `make env`, reproducibility check | tunes benchmarks |
| B — workloads | `bench/*.c`, bug-class checks, checksum validity | edits scripts |
| C — measurement | `scripts/run.sh`, `summarize.py`, statistics, figures | interprets results alone |
| D — writing | README, report, deviations log, presentation | writes numbers not in `results/` |

Everyone commits every week. One person committing for the group loses the
"individual contributions" criterion outright.
