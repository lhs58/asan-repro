# Reproducibility check (Week 6)

The plan asks for one thing: clone into a fresh directory, follow the README literally, and confirm
`make all` works without editing paths. This document records what was actually verified, and by whom,
so that the claim is not stronger than the evidence.

**Status: static audit passed; the containerised `make all` was not re-executed on the machine
used for this audit** (no WSL2, no Docker, no clang on that host). The audit therefore checks
everything that can be checked without a Linux toolchain, and says exactly what remains.

## What was verified (2026-11-25)

| Check | Method | Result |
|---|---|---|
| Fresh-clone usability | `git clone` into an empty directory, no path edits | clone succeeds; 56 files; default branch `main` |
| Documented `make` targets exist | extract every `make <target>` from `README.md`, `docs/report.md`, `docs/plan.md` and compare with `Makefile` | all resolve (`all build run summarize variance figures extension extension-opt build-opt env doctor clean shell`) |
| Internal links resolve | parse every relative Markdown link in the repository, `Test-Path` each target | all resolve, including the report's `../results/figures/*.svg` references |
| Nothing over 50 MB | `git ls-files` + file sizes | largest tracked file is 160 KB (`results/figures/optlevel.png`); no file near the limit |
| No build outputs or credentials committed | `git ls-files` review | `build/`, `results/raw/*.csv` only as committed evidence; no keys, no images, no `.env` |
| Four distinct authors | `git shortlog -sne` | four members present (one author string split: `QISIHAO` / `QiSihao`) |
| Evidence completeness | row counts in `results/raw/*.csv` vs the documented `n` | 45 + 75 + 75 + 75 = **270 rows = n = 18 per point** (the previously documented `n = 13` was an arithmetic slip, now corrected) |
| Script syntax | `bash -n`, `python -m py_compile` | **not possible** on the audit host: Git Bash cannot start under the sandbox, no Python on `PATH` |

## What was not executed, and how to close it

The benchmark build and run were last executed on the WSL2 machine (Ubuntu 22.04.5, clang-14,
`LAPTOP-6KFUGPE5`) that produced `results/raw/`. Nobody re-ran the full pipeline after the Week-6
documentation changes, which touch only Markdown — but that is a reason to expect success, not
evidence of it.

To close the check, on a machine with Docker (or the same WSL2 setup):

```bash
git clone https://github.com/lhs58/asan-repro && cd asan-repro
docker build -t asan-repro .
docker run --rm -it -v "$PWD":/work asan-repro make all      # ~9 min
docker run --rm -it -v "$PWD":/work asan-repro make doctor   # bug detection still fires
git status --short                                           # expect no tracked-file changes
```

The third command is the real test: `make summarize` must regenerate `results/summary.md` byte for
byte from the committed raw CSV, and `make figures` must regenerate the committed figures. If either
differs, the committed summary and the committed data disagree, which is the failure mode this check
exists to catch.

## Known-fragile points in the pipeline

1. **`setarch -R` is mandatory.** Without it, roughly a quarter of instrumented runs die with
   `SIGSEGV` on kernels with `mmap_rnd_bits=32` (D14). `scripts/run.sh` applies it; a reader who
   bypasses the script and calls the binaries directly will see spurious crashes.
2. **Iteration counts are tuned to this machine.** Baseline runs are calibrated to 0.5–1.0 s (D17).
   On a much slower host the `b1_allocs` measurement approaches minutes; on a much faster one, timer
   resolution starts to matter.
3. **`max_redzone=32` is silently clamped** by the clang-14 runtime (D18), so the redzone check in
   `results/ext/summary.md` measures the default behaviour, not the paper's 32-byte setting.
4. **`-O` level changes the answer by 28 % relative** (D20, §5 of the report). Any re-run must use
   `-O2` to be comparable with `results/summary.md`.
