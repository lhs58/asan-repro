# Reproduction of *AddressSanitizer: A Fast Address Sanity Checker* (USENIX ATC '12)

CS340 Operating Systems — Research Paper Replication, AY 2026–27.

| | |
|---|---|
| **Paper** | Konstantin Serebryany, Derek Bruening, Alexander Potapenko, Dmitry Vyukov. *AddressSanitizer: A Fast Address Sanity Checker*. USENIX ATC 2012. |
| **Paper PDF** | https://www.usenix.org/system/files/conference/atc12/atc12-final39.pdf |
| **System under test** | AddressSanitizer as shipped with LLVM/Clang (we use the packaged `clang-14` from Ubuntu 22.04). No upstream file is patched. |
| **Our artefact** | The benchmark harness and measurement pipeline in this repository. |
| **Repository status** | Week 1 scaffold — see `docs/plan.md` for the six-week schedule. |

---

## 1. Purpose

The paper claims that shadow-memory instrumentation can be *fast*: it reports an average
**73 % slowdown** on SPEC CPU2006, **3.37× memory** overhead, and a write-only
instrumentation mode at **26 % slowdown**. This repository rebuilds the measurement around
those numbers on hardware and a toolchain that did not exist in 2012, and asks whether the
claims still hold.

Claims are enumerated in [`docs/claims.md`](docs/claims.md); every deviation from the paper's
setup is logged in [`docs/deviations.md`](docs/deviations.md).

## 2. Quick start (container)

```bash
docker build -t asan-repro .
docker run --rm -it -v "$PWD":/work asan-repro make all
```

PowerShell:

```powershell
docker build -t asan-repro .
docker run --rm -it -v "${PWD}:/work" asan-repro make all
```

`make all` = `make build` + `make run` + `make summarize`. It writes
`results/raw/<timestamp>-<host>.csv` and `results/summary.md`.

## 3. Starting code and what we pin

There is no upstream *paper* repository to fork: the artefact under test is the AddressSanitizer
pass and runtime that live inside LLVM. We therefore pin the toolchain instead of a commit:

- Ubuntu 22.04 (see `Dockerfile`)
- `clang-14` / `llvm-14` / `lld-14` from the Ubuntu archive
- the exact versions observed at run time are recorded in [`docs/environment.md`](docs/environment.md)
  by `make env`

**Files modified upstream: none.** Everything we add lives in this repository. This difference
from the usual "reproduce a paper's prototype" shape is recorded as deviation **D1** in
`docs/deviations.md`.

## 4. Build

```bash
make build            # 5 benchmarks x 3 build modes -> build/{base,asan,asanw}/
```

| Mode | Flags | Meaning |
|---|---|---|
| `base` | `-O2 -g` | the paper's comparison baseline (`clang -O2`) |
| `asan` | `-O2 -g -fsanitize=address -fno-omit-frame-pointer` | real AddressSanitizer |
| `asanw` | as `asan` + `-mllvm -asan-instrument-reads=0` | write-only instrumentation; the paper reports 26 % here |

Runtime settings for the `asan` modes are chosen to approximate the paper's configuration
(§4: *"32-byte redzones, disabled the stack unwinding during malloc and free and set the
quarantine size to zero"*):

```
ASAN_OPTIONS = malloc_context_size=0:quarantine_size_mb=0:detect_leaks=0:max_redzone=32
```

These are approximations, not exact equivalents — see deviations **D3**–**D5**.

## 5. Run

```bash
make run                        # 1 warm-up + 3 measured repetitions per (benchmark, mode)
RUNS=5 make run                 # more repetitions
CPU_PIN=2 make run              # pin to one core (recommended on noisy machines)
```

Output columns: `bench,mode,wall_s,vmpeak_kb,vmhwm_kb,vmsize_kb,checksum`.
All three memory fields are read from `/proc/self/status` — the same source the
paper used for Table 1. **Peak RSS (`vmhwm_kb`) is the primary memory metric**:
modern 64-bit ASan reserves one eighth of the address space for shadow memory,
and that PROT_NONE reservation inflates `VmPeak` into the terabyte range without
reflecting real memory use. `vmpeak_kb` is recorded so the effect can be shown
and explained, not so it can be compared to Table 1 directly. See the comment
block at the top of `bench/common.h`.

**Expected runtime** on a typical 8-core laptop CPU, containerised:
about 15 s per benchmark per mode per repetition — roughly **8–10 minutes** for
`RUNS=3` including the warm-up. Record the number you actually observe here.

## 6. Results

`make summarize` produces [`results/summary.md`](results/summary.md) with mean ± standard
deviation over repetitions and the Paper-vs-Ours comparison. The table below is the shape it
produces; values are filled in only after real runs.

### 6.1 Runtime overhead (paper: Figure 2, average 73 %)

Session `results/raw/20261031-222633-LAPTOP-6KFUGPE5.csv`, n = 3 per point,
warm-up discarded, baseline ≈ 0.5–1 s per run.

| Benchmark | Baseline (s) | ASan (s) | Slowdown | Write-only (s) | Slowdown | Closest CPU2006 analogue |
|---|---|---|---|---|---|---|
| `b1_allocs` — heap churn | 0.528 ± 0.011 | 5.466 ± 0.231 | 10.36× | 5.459 ± 0.209 | 10.35× | 400.perlbench (2.60×) * |
| `b2_pointer` — pointer chasing | 0.856 ± 0.132 | 1.117 ± 0.172 | 1.30× | 1.134 ± 0.271 | 1.32× | 429.mcf |
| `b3_int` — byte-wise hashing | 0.948 ± 0.043 | 0.991 ± 0.042 | 1.05× | 0.950 ± 0.066 | 1.00× | 401.bzip2 |
| `b4_float` — FP arrays | 0.768 ± 0.035 | 2.078 ± 0.078 | 2.70× | 1.010 ± 0.043 | 1.31× | 470.lbm * |
| `b5_string` — token scanning | 1.009 ± 0.051 | 1.251 ± 0.039 | 1.24× | 0.985 ± 0.036 | 0.98× | 483.xalancbmk (2.67×) |
| **Mean, all five** | | | **3.33× (+233 %)** | | **2.99× (+199 %)** | paper: 1.73× / 1.26× |
| **Mean, b2–b5 only** | | | **1.57× (+57 %)** | | **1.15× (+15 %)** | paper: 1.73× / 1.26× |

`*` Not a valid proxy — see the notes below. `b1_allocs` performs almost no work
besides `malloc`/`free`, so its ratio is an **upper bound on allocator overhead**,
not a replication of perlbench. `b4_float` is dominated by de-vectorisation
rather than by shadow checks. Both means are reported so the reader can see how
much the second one depends on that exclusion.

### 6.2 Memory overhead (paper: Table 1, average 3.37× — but see the caveat)

| Benchmark | Baseline RSS (MB) | ASan RSS (MB) | Increase | ASan VmPeak (MB) |
|---|---|---|---|---|
| `b1_allocs` | 2.0 | 6.9 | 3.38× | 20 971 560 |
| `b2_pointer` | 10.9 | 20.1 | 1.84× | 20 971 560 |
| `b3_int` | 2.8 | 5.7 | 2.04× | 20 971 561 |
| `b4_float` | 1.9 | 4.8 | 2.48× | 20 971 560 |
| `b5_string` | 5.8 | 8.7 | 1.50× | 20 971 564 |
| **Mean** | | | **2.25×** (paper: 3.37×) | — |

The paper's 3.37× is a `VmPeak` measurement from 2012. Current ASan reserves
1/8 of the address space as shadow, so `VmPeak` is dominated by an unused
mapping and cannot be compared to Table 1. Peak RSS is the honest quantity;
the report must say this explicitly and treat "our 3.37× analogue" as a
different metric from the paper's figure. This is a deviation (**D13** in
`docs/deviations.md`), not a failure to reproduce.

### 6.3 Known comparability limits

The paper measures SPEC CPU2006 (licensed software, 2× Xeon E5620, 2010). We cannot obtain
SPEC, so the workloads are purpose-built stand-ins that isolate the access patterns the paper
singles out as expensive (small and 1–2-byte accesses, malloc churn). **Absolute slowdowns are
therefore not directly comparable to Figure 2**; what is comparable is the *ordering* of the
benchmarks and the approximate magnitude. This is the central subject of the report's
discrepancy analysis, not a defect to hide.

## 7. Layout

```
bench/        five C benchmarks + shared timing/measurement header
scripts/      build/run/summarize/env helpers, commit-msg hook installer
docs/         claims, deviations, environment record, six-week plan
results/      raw per-run CSV (committed — this is the evidence trail) + summary
Dockerfile    pinned toolchain
Makefile      build / run / summarize / env / clean
```

## 8. Credit and licence

- AddressSanitizer is part of LLVM, distributed under *Apache-2.0 WITH LLVM-exception*.
  This repository **does not redistribute** upstream code; the tool is consumed as a pinned
  Ubuntu package.
- The paper is © 2012 by the authors; USENIX permits reproduction for classroom use.
- Our code is MIT — see [`LICENSE`](LICENSE) and [`NOTICE.md`](NOTICE.md).

## 9. Contribution statement

> Replace with the real split before submission; it must match the commits.

| Member | Student ID | GitHub | Contribution |
|---|---|---|---|
| TBD | TBD | TBD | environment, container, build system |
| TBD | TBD | TBD | benchmarks and bug-detection sanity checks |
| TBD | TBD | TBD | measurement runs, statistics, figures |
| TBD | TBD | TBD | report, deviations log, presentation |

## 10. AI usage statement

> Fill in truthfully and specifically. Draft skeleton — adjust to what actually happened:

AI assistants were used for: (a) locating the paper and its key figures, (b) drafting the
initial repository skeleton (`make` targets, scripts, benchmark programs) and (c) explaining
AddressSanitizer's shadow-memory design during the reading phase. All experimental design
decisions, the choice of `ASAN_OPTIONS`, every measurement run, the statistical analysis and
all conclusions were carried out and verified by the group; the benchmark programs were
reviewed and modified by the group before use. No results in this report were generated by an
AI system.
