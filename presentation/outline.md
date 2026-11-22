# Presentation outline (skeleton, not the report)

Course format: 5 min talk + 2 min Q&A, PPT or PDF, English, **every slide
numbered** (footer `n / 8`; backup slides `B1`–`B4`). All four members speak;
anyone who does not speak gets no marks. Overtime costs marks (presentation
efficiency is 25 %).

Every number on a slide must be copied from the file named in its *Source*
line, never retyped from memory. Figures: use the PNGs in `results/figures/`
(PowerPoint does not take the PDFs and renders SVG unreliably).

## Timing

| # | Slide | Speaker | Time | Section |
|---|---|---|---|---|
| 1 | Title | 潘昊东 Pan Haodong | 0:15 | Intro |
| 2 | The paper and its three claims | 潘昊东 Pan Haodong | 1:00 | Intro |
| 3 | What we rebuilt, and what we could not | 张启勋 Zhang Qixun | 0:40 | Approach |
| 4 | Making the measurement trustworthy | 张启勋 Zhang Qixun | 0:35 | Approach |
| 5 | Runtime overhead (C1, C3) | 李海晟 Li Haisheng | 0:45 | Results |
| 6 | Memory (C2) and the -O sweep | 李海晟 Li Haisheng | 0:30 | Results |
| 7 | Critical analysis | 戚思浩 Qi Sihao | 0:45 | Critical |
| 8 | Conclusion | 戚思浩 Qi Sihao | 0:30 | Conclusion |
| | **Total** | 4 × 1:15 | **5:00** | |

> **Timing conflict to resolve as a group.** The brief asks for both
> Intro 1:00 / Approach 1:00 / Results 1:30 / Critical 1:00 / Conclusion 0:30
> *and* 75 s per speaker with Qi covering Critical + Conclusion. Both cannot
> hold: Critical + Conclusion alone is 1:30. This outline keeps 75 s per
> speaker (the hard rule is that everyone speaks), which gives
> Intro 1:15 (incl. title) / Approach 1:15 / Results 1:15 / Critical 0:45 /
> Conclusion 0:30. If the section budget matters more, move slide 6 to Qi and
> shorten slide 2.

---

## 1 / 8 — Title · Pan Haodong · 0:15

**Reproducing *AddressSanitizer: A Fast Address Sanity Checker* (USENIX ATC '12)**

- CS340 Operating Systems, research paper replication, AY 2026–27
- Pan Haodong · Zhang Qixun · Li Haisheng · Qi Sihao (with student IDs)
- Repository: https://github.com/lhs58/asan-repro

*Source:* `README.md` (header table).

## 2 / 8 — The paper and its three claims · Pan Haodong · 1:00

- ASan finds out-of-bounds and use-after-free bugs via compiler instrumentation plus a 1/8 shadow memory
- Claims tested: **C1** mean slowdown 1.73× (+73 %); **C2** memory 3.37×; **C3** write-only 1.26×
- Not tested: the 300 Chromium bugs and the Valgrind comparison (not reproducible from the paper)

*Source:* `docs/claims.md` (C1–C3, "Explicitly not tested").

## 3 / 8 — What we rebuilt, and what we could not · Zhang Qixun · 0:40

- clang-14 on Ubuntu 22.04 / WSL2, unmodified, instead of LLVM 3.1 (2012)
- 5 purpose-built C workloads instead of SPEC CPU2006 (licensed, retired)
- Three builds per workload from the same source: `base` -O2, `asan`, `asanw` (writes only)

*Source:* `docs/deviations.md` D1–D3, D12; `Makefile` (`build`).

## 4 / 8 — Making the measurement trustworthy · Zhang Qixun · 0:35

- Without ASLR disabled, 11 of 40 ASan runs (27.5 %) crashed silently → every run under `setarch -R`
- n = 13 per point across four separate sessions; between-session drift < within-session noise
- `make doctor`: all four bug classes detected; checksums identical across all builds

*Source:* `docs/deviations.md` D14, D19; `results/variance.md`; `scripts/sanity_bug_check.sh`.

## 5 / 8 — Runtime overhead (C1, C3) · Li Haisheng · 0:45

- Figure: `results/figures/slowdown.png`
- Mean 3.32×, but **1.55× excluding `b1_allocs`** (paper 1.73×); write-only 1.12× excluding b1 (paper 1.26×)
- `b1_allocs` 10.4× is an upper bound on allocator cost, not a perlbench replica

*Source:* `results/summary.md` (runtime table); `README.md` §6 ("Mean, b2–b5 only" row); D15.

## 6 / 8 — Memory (C2) and the optimisation-level sweep · Li Haisheng · 0:30

- Peak RSS 2.25× vs paper 3.37× (the paper used VmPeak; see backup B3)
- Extension: mean slowdown excluding b1 rises 1.39× (-O0) → 1.69× (-O2) → 1.78× (-O3)
- Figure: `results/figures/optlevel.png`; the paper's 73 % holds only at -O2

*Source:* `results/summary.md` (memory table); `results/ext/opt-summary.md`; D20.

## 7 / 8 — Critical analysis · Qi Sihao · 0:45

- `b4_float` 2.77× is *not* de-vectorisation: already 2.54× at -O1, where nothing is vectorised (D20 overturns D16's explanation)
- The paper's redzone trade-off cannot be reproduced: `max_redzone` is clamped in clang-14 (D18)
- Limits: 5 micro-benchmarks, not SPEC; WSL2 timing noise (b2_pointer ±15 %)

*Source:* `results/ext/opt-summary.md` (Conclusion); D16, D18, D20; `results/variance.md` (b2).

## 8 / 8 — Conclusion · Qi Sihao · 0:30

- C1 and C3 broadly hold on realistic workloads (1.55× / 1.12× vs 1.73× / 1.26×)
- C2 is not comparable as stated: VmPeak is unusable on modern ASan; RSS gives 2.25×
- New: ASan's relative cost depends on the optimisation level, which the paper never reports

*Source:* `README.md` §6 ("Mean, b2–b5 only"); `results/summary.md`; `results/ext/opt-summary.md`.

---

## Backup slides (not part of the 5 minutes; for Q&A only)

### B1 — Full deviation table

- All 20 deviations, one line each: item, paper vs ours, reason
- Highlight D3 (compiler generation), D13 (memory metric), D14 (ASLR)

*Source:* `docs/deviations.md` D1–D20.

### B2 — Why `b1_allocs` is an upper bound

- Allocation-only loop: tiny malloc/free pairs with almost no work between them
- Allocator overhead is not amortised, unlike perlbench, which spends most of its time outside malloc
- Both means always reported: 3.32× with it, 1.55× without

*Source:* D15; `README.md` §6; `results/summary.md` ("What each workload does and does not measure").

### B3 — Why VmPeak reads 20 TB

- ASan reserves a 1/8 address-space shadow mapped PROT_NONE; it counts toward VmPeak/VmSize
- Untouched pages are never resident, so ASan VmPeak ≈ 20 971 560 MB in every run
- Peak RSS (VmHWM) is the comparable quantity; the paper's 3.37× was measured on VmPeak in 2012

*Source:* D13; `results/summary.md` (memory table, VmPeak columns).

### B4 — Optimisation-level sweep, full numbers

- Per-workload table, -O0..-O3, base and asan seconds and slowdown
- Checksums identical across all levels and both modes
- One session on a different machine from the main runs: compare ratios only

*Source:* `results/ext/opt-summary.md`; `results/ext/opt-20261122-102110-localhost.csv`.
