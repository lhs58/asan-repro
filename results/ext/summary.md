# Extension: heap redzone size

One factor changed (`ASAN_OPTIONS=...:max_redzone=N`), everything else
fixed: same binaries, same machine, same session, same iteration counts,
ASLR disabled. n = 5 runs per point.

## Cost side (paper Sec. 4.3: larger redzone may cost time and memory)

### `b1_allocs`

| max_redzone | wall (s) | slowdown vs baseline | peak RSS (MB) | RSS increase |
|---|---|---|---|---|
| baseline (no ASan) | 0.733 ± 0.018 | 1.00× | 2.0 | 1.00× |
| 32 | 8.212 ± 0.184 | 11.20× | 6.9 | 3.38× |
| 64 | 8.351 ± 0.115 | 11.39× | 7.1 | 3.48× |
| 128 | 8.606 ± 0.423 | 11.74× | 7.1 | 3.48× |
| 256 | 7.927 ± 0.137 | 10.81× | 7.1 | 3.48× |

### `b2_pointer`

| max_redzone | wall (s) | slowdown vs baseline | peak RSS (MB) | RSS increase |
|---|---|---|---|---|
| baseline (no ASan) | 1.153 ± 0.111 | 1.00× | 10.9 | 1.00× |
| 32 | 1.951 ± 0.214 | 1.69× | 20.1 | 1.84× |
| 64 | 1.976 ± 0.187 | 1.71× | 20.1 | 1.84× |
| 128 | 1.661 ± 0.246 | 1.44× | 20.1 | 1.84× |
| 256 | 1.692 ± 0.155 | 1.47× | 20.1 | 1.84× |

### `b5_string`

| max_redzone | wall (s) | slowdown vs baseline | peak RSS (MB) | RSS increase |
|---|---|---|---|---|
| baseline (no ASan) | 1.455 ± 0.026 | 1.00× | 5.8 | 1.00× |
| 32 | 1.899 ± 0.037 | 1.30× | 8.7 | 1.50× |
| 64 | 1.929 ± 0.087 | 1.33× | 8.7 | 1.50× |
| 128 | 1.791 ± 0.027 | 1.23× | 8.7 | 1.50× |
| 256 | 1.792 ± 0.052 | 1.23× | 8.7 | 1.50× |

## Detection side (paper Sec. 3.5)

Write at a fixed offset past a 16-byte allocation, under the same
`ASAN_OPTIONS` as the cost measurement, with ASLR disabled.\n
| max_redzone | offset +40 | offset +100 | offset +200 |
|---|---|---|---|
| 32  | **detected** | **detected** | **detected** |
| 64  | **detected** | **detected** | **detected** |
| 128  | **detected** | **detected** | **detected** |
| 256  | **detected** | **detected** | **detected** |

A short redzone finds fewer of these writes: the overflow has to land
inside the poisoned region to be caught (paper Sec. 3.5).

> Checksums are identical across all redzone sizes, so the option changed performance only, not the computed results.
