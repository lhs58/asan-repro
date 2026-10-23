# Claims under test

The course requires one to three claims, each tied to a specific table or figure in
the paper. We test three. Everything else in the paper is treated as background,
not as a claim we assert.

Paper: Serebryany, Bruening, Potapenko, Vyukov. *AddressSanitizer: A Fast Address
Sanity Checker*. USENIX ATC 2012.

---

## C1 — Runtime overhead is moderate: average 73 % slowdown

**Paper location.** Figure 2 ("The average slowdown on SPEC CPU2006 on 64-bit
Linux") and the paragraph in §4 that follows it. The two extreme cases are
400.perlbench at 2.60× and 483.xalancbmk at 2.67×, described as "very
malloc-intensive and [making] a huge number of 1- and 2-byte memory accesses".

**Configuration the paper used.** 64-bit Linux, HP Z600, 2 × quad-core Xeon E5620,
24 GB RAM; baseline is the same source built with `clang -O2`; 32-byte redzones,
stack unwinding disabled during `malloc`/`free`, quarantine size zero.

**How we test it.** `b1`–`b5` measure wall time of five workloads built three ways
(`base`, `asan`, `asanw`) from identical sources, on one machine, in one session,
`n = 3` repetitions after a discarded warm-up. Slowdown = mean(asan) / mean(base).

**What "supported" would look like.** Mean slowdown in the neighbourhood of
1.7×, and the malloc-/byte-access-heavy workloads (`b1`, `b5`) well above the
arithmetic-heavy one (`b4`). We do **not** expect to match 73 % exactly: the
workloads differ (see `deviations.md` D2) and so does the hardware (D5).

**What would count against it.** A mean far below ~1.2× or far above ~3×, or an
ordering in which the FP workload is the most expensive — either would suggest
the instrumentation cost model in the paper no longer describes current ASan.

---

## C2 — Memory overhead is about 3.4×

**Paper location.** Table 1 ("Memory usage with AddressSanitizer"), measured by
reading `VmPeak` from `/proc/self/status` at process termination. Per-benchmark
range in the paper is 1.40× (429.mcf) to 24.55× (453.povray); the total row is
3.37×.

**How we test it.** Identical mechanism: each benchmark reads its own `VmPeak`
from `/proc/self/status` before exiting and prints it. Because the workload
sizes are fixed by command-line arguments, the baseline footprint is reproducible.

**What "supported" would look like.** Mean VmPeak increase in the 2×–5× band,
with the smallest increase on the workload allocating the fewest objects.

**Caveat to state in the report.** VmPeak is a high-water mark of *virtual*
address space, so it conflates heap redzones with the fixed shadow-mapping
reservation. The paper acknowledges this implicitly by reporting what it read
from `/proc`, and so must we.

---

## C3 — Write-only instrumentation cuts the average slowdown to 26 %

**Paper location.** §4, the sentence "We also measured AddressSanitizer
performance when only writes are instrumented: the average slowdown is 26 %."
There is no separate figure for it.

**How we test it.** A third build, `asanw`, adds
`-mllvm -asan-instrument-reads=0` to the ASan build so only stores are checked.
Everything else is held constant.

**What "supported" would look like.** `asanw` noticeably faster than `asan` on
the read-dominated workloads (`b3`, `b5`) and close to it on the write-heavy one
(`b1`), with the mean somewhere between 1.1× and 1.4×.

**Risk.** This pass option may be unavailable or renamed in modern Clang. If the
build fails, record it as a deviation and fall back to C1 + C2 only — the course
requires one to three claims, not three.

---

## Explicitly not tested

- **The deployment claim** (§4.2): "over 300 previously unknown bugs in
  Chromium in 10 months". Not reproducible from a paper: it depends on a
  proprietary codebase, a build farm, and wall-clock time.
- **Comparison with Valgrind, Dr. Memory, Mudflap** (§4.1). The Varglind and
  Dr. Memory numbers (20× and 10×) are quoted from reference [8], not measured by
  the authors. Reproducing them would require running SPEC under Valgrind, which
  we cannot obtain.
- **Binary-size growth** (1.5×–3.2×, average 2.5×). Cheap to measure and a good
  candidate for the *extension* experiment instead of a core claim.
- **Scale/Offset sensitivity** (§4): "2 % speedup to 15 % slowdown". Possible
  extension if `-mllvm -asan-mapping-scale` still exists in the pinned Clang.
