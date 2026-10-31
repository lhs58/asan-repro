# Deviations from the paper's setup

The report requires a complete table of deviations, each with the original
setting, the setting actually used, and the reason. This file is that table.
**Update it as the project proceeds — a deviation discovered in week 5 still
belongs here, and an empty "reason" column loses marks.**

| ID | Item | Paper's setting | Ours | Reason |
|---|---|---|---|---|
| D1 | Starting code | The authors' ASan prototype inside LLVM 3.1, not separately published | Unmodified `clang-14` from the Ubuntu 22.04 archive | The 2012 prototype no longer exists as a separate artefact; ASan was upstreamed into LLVM. We therefore reproduce the *system under test*, not a fork of it. Nothing upstream is patched. |
| D2 | Workloads | SPEC CPU2006, 18 benchmarks | 5 purpose-built C benchmarks (`b1`–`b5`) | SPEC CPU2006 is commercially licensed and retired; it cannot be obtained for a course project. Workloads are matched to the access patterns the paper singles out (malloc churn, 1–2-byte accesses, pointer chasing, FP). Reduced scale is permitted by the course instructions if stated. |
| D3 | Compiler version | LLVM 3.1 (2012) | clang-14 (LLVM 14) | Building LLVM 3.1 on a current Linux distribution is fragile and out of scope. This is the single largest deviation: the instrumentation pass, the allocator and the runtime have all changed in 13 years, and C3 in `claims.md` depends on a pass option whose modern spelling must be verified. |
| D4 | Heap redzone size | 32 bytes | `max_redzone=32` | Modern ASan computes redzones from allocation size, bounded by `max_redzone`; there is no literal "32-byte redzone" switch. `max_redzone=32` is the closest equivalent, not an exact match. |
| D5 | Stack unwinding on malloc/free | Disabled for the performance runs | `malloc_context_size=0` | Same intent: remove call-stack capture from the measured path. |
| D6 | Quarantine size | 0 | `quarantine_size_mb=0` | Matches the paper's performance configuration. Consequence: use-after-free detection is weakened, so the correctness check (`make doctor`) deliberately runs with default settings instead. |
| D7 | LeakSanitizer | Did not exist in 2012 | Disabled during measurement (`detect_leaks=0`) | LSan runs at exit and adds cost the 2012 tool never paid. |
| D8 | Hardware | HP Z600, 2 × quad-core Xeon E5620 @ 2.40 GHz, 24 GB RAM | Intel Core i9-14900HX, 32 logical CPUs visible in WSL2 (see `docs/environment.md`) | Not available. Absolute times are not comparable; ratios are compared instead, and this is stated wherever numbers are quoted. |
| D9 | OS / kernel | 64-bit Linux, 2012-era kernel | Ubuntu 22.04.5 under WSL2, kernel `6.18.54.1-microsoft-standard-WSL2` | The VM, not bare metal. WSL2 virtualises timing-sensitive paths (interrupt handling, page allocation) and adds scheduling jitter, so the ratios carry more noise than the paper's numbers did. |
| D10 | Clock / statistics | Single run, no spread reported | Mean ± sample sd over ≥3 repetitions after one discarded warm-up | The course requires mean ± sd; the paper predates that norm. Our numbers are therefore more conservative, not less. |
| D11 | CPU frequency behaviour | Not stated | Not controllable: WSL2 exposes no `cpufreq` governor, and laptop turbo/thermal behaviour is managed by the Windows host | 2010 servers ran at fixed clocks; this CPU does not. Most likely cause of run-to-run noise, together with D9. |
| D12 | Write-only instrumentation | Internal pass option of the 2012 tool | `-mllvm -asan-instrument-reads=0` | Flag spelling differs between LLVM generations; verify it is accepted by clang-14, otherwise mark claim C3 untested. |
| D13 | Memory metric | `VmPeak` from `/proc/self/status` | `VmHWM` (peak RSS) as primary; `VmPeak` recorded for comparison only | Current 64-bit ASan maps a 1/8-address-space shadow reservation as PROT_NONE. Untouched pages are never resident but still count toward VmPeak, so the paper's 3.37× cannot be reproduced on the same field. Report both and state the difference. **Observed:** ASan VmPeak ≈ 20 971 560 MB (≈ 20 TB) in every run, confirming the effect. |
| D14 | Address-space randomisation | Not mentioned; 2012 kernels used far less mmap entropy | All measured processes run under `setarch <arch> -R` (ADDR_NO_RANDOMIZE); the host's `vm.mmap_rnd_bits` was also lowered 32 → 28 | With `mmap_rnd_bits=32`, ASan's fixed shadow mapping collided at random: **11 of 40 runs (27.5 %) died with SIGSEGV before printing any report**, while the identical binary reported the bug correctly the other 29 times. Under `setarch -R`, 40/40 runs reported correctly and a correct program never crashed. Without this, a quarter of the measurements would have been silently wrong. The wrapper is applied to the baseline too, so the comparison stays internal. |
| D15 | `b1_allocs` interpretation | perlbench: 2.60× | Measured 10.36×, reported as an *upper bound on allocator overhead* and excluded from the secondary mean | `b1_allocs` is an allocation-only loop: it does almost no work between `malloc` and `free`, so the allocator cost is not amortised by anything. perlbench spends most of its time outside the allocator. The 10.36× is therefore a property of the workload, not a contradiction of the paper. **Both means are reported** (all five: 3.33×; b2–b5: 1.57×) so the exclusion is visible and its effect is quantifiable. |
| D16 | `b4_float` interpretation | 470.lbm / 450.soplex showed the smallest overhead in the paper | 2.70× — driven by de-vectorisation, not shadow checks | ASan instrumentation prevents the auto-vectoriser from vectorising the inner loop, so the ratio reflects a change in code generation as much as the shadow-memory check. The paper's claim "floating-point code pays the least" is therefore **only weakly tested** here; the write-only build (1.31×) is a better probe of the instrumentation cost alone. |
| D17 | Iteration counts | SPEC's own run rules | Tuned on 2026-10-31 so each *baseline* run takes ≈ 0.5–1.0 s | The first session used 7–20× smaller counts and every baseline finished in 0.05–0.48 s, leaving run-to-run noise at up to 24 % of the mean. That session was deleted rather than averaged in (different iteration counts are not comparable). Recorded here because it changed every reported number. |

## Standing rules

- Every deviation gets a row **when it happens**, not when the report is written.
- If a deviation makes a claim untestable, say so in the report rather than
  quietly dropping the claim.
- Anything in this table that changes a number must also be mentioned in the
  caption of the figure or table that reports that number.
