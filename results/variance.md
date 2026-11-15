# Session-to-session variance

4 measurement sessions: `20261031-222633-LAPTOP-6KFUGPE5`, `20261115-223959-LAPTOP-6KFUGPE5`, `20261115-224952-LAPTOP-6KFUGPE5`, `20261115-225245-LAPTOP-6KFUGPE5`

`within` is the propagated standard deviation of the slowdown inside one session; `between` is the standard deviation of the per-session slowdown means. Both are relative (sd / mean).

## `b1_allocs`

| session | n | baseline (s) | ASan (s) | slowdown | write-only |
|---|---|---|---|---|---|
| `20261031-222633-LAPTOP-6KFUGPE5` | 3 | 0.528 | 5.466 | 10.36× | 10.35× |
| `20261115-223959-LAPTOP-6KFUGPE5` | 5 | 0.526 | 5.468 | 10.40× | 10.36× |
| `20261115-224952-LAPTOP-6KFUGPE5` | 5 | 0.526 | 5.445 | 10.35× | 10.27× |
| `20261115-225245-LAPTOP-6KFUGPE5` | 5 | 0.519 | 5.455 | 10.51× | 10.40× |
| **between sessions** | | | | **10.41× ± 0.07** | **10.34× ± 0.05** |

- within-session relative sd: **2.8 %** (write-only 2.7 %)
- between-session relative sd: **0.7 %** (write-only 0.5 %)
- full spread across sessions: **1.5 %** of the mean
- verdict: comparable — pooling the sessions is safe

## `b2_pointer`

| session | n | baseline (s) | ASan (s) | slowdown | write-only |
|---|---|---|---|---|---|
| `20261031-222633-LAPTOP-6KFUGPE5` | 3 | 0.856 | 1.117 | 1.30× | 1.32× |
| `20261115-223959-LAPTOP-6KFUGPE5` | 5 | 0.930 | 1.075 | 1.16× | 1.11× |
| `20261115-224952-LAPTOP-6KFUGPE5` | 5 | 0.845 | 1.078 | 1.28× | 1.23× |
| `20261115-225245-LAPTOP-6KFUGPE5` | 5 | 0.810 | 1.227 | 1.52× | 1.35× |
| **between sessions** | | | | **1.31× ± 0.15** | **1.25× ± 0.11** |

- within-session relative sd: **15.4 %** (write-only 16.7 %)
- between-session relative sd: **11.4 %** (write-only 8.7 %)
- full spread across sessions: **27.4 %** of the mean
- verdict: comparable — pooling the sessions is safe

## `b3_int`

| session | n | baseline (s) | ASan (s) | slowdown | write-only |
|---|---|---|---|---|---|
| `20261031-222633-LAPTOP-6KFUGPE5` | 3 | 0.948 | 0.991 | 1.05× | 1.00× |
| `20261115-223959-LAPTOP-6KFUGPE5` | 5 | 0.919 | 0.974 | 1.06× | 1.02× |
| `20261115-224952-LAPTOP-6KFUGPE5` | 5 | 0.939 | 0.981 | 1.04× | 0.98× |
| `20261115-225245-LAPTOP-6KFUGPE5` | 5 | 0.919 | 0.982 | 1.07× | 1.00× |
| **between sessions** | | | | **1.05× ± 0.01** | **1.00× ± 0.02** |

- within-session relative sd: **4.4 %** (write-only 5.2 %)
- between-session relative sd: **1.1 %** (write-only 1.7 %)
- full spread across sessions: **2.4 %** of the mean
- verdict: comparable — pooling the sessions is safe

## `b4_float`

| session | n | baseline (s) | ASan (s) | slowdown | write-only |
|---|---|---|---|---|---|
| `20261031-222633-LAPTOP-6KFUGPE5` | 3 | 0.768 | 2.078 | 2.70× | 1.31× |
| `20261115-223959-LAPTOP-6KFUGPE5` | 5 | 0.817 | 2.099 | 2.57× | 1.26× |
| `20261115-224952-LAPTOP-6KFUGPE5` | 5 | 0.808 | 2.087 | 2.58× | 1.28× |
| `20261115-225245-LAPTOP-6KFUGPE5` | 5 | 0.848 | 2.088 | 2.46× | 1.21× |
| **between sessions** | | | | **2.58× ± 0.10** | **1.27× ± 0.05** |

- within-session relative sd: **10.7 %** (write-only 11.0 %)
- between-session relative sd: **3.8 %** (write-only 3.6 %)
- full spread across sessions: **9.3 %** of the mean
- verdict: comparable — pooling the sessions is safe

## `b5_string`

| session | n | baseline (s) | ASan (s) | slowdown | write-only |
|---|---|---|---|---|---|
| `20261031-222633-LAPTOP-6KFUGPE5` | 3 | 1.009 | 1.251 | 1.24× | 0.98× |
| `20261115-223959-LAPTOP-6KFUGPE5` | 5 | 0.990 | 1.275 | 1.29× | 0.99× |
| `20261115-224952-LAPTOP-6KFUGPE5` | 5 | 0.969 | 1.254 | 1.29× | 1.00× |
| `20261115-225245-LAPTOP-6KFUGPE5` | 5 | 0.985 | 1.269 | 1.29× | 1.00× |
| **between sessions** | | | | **1.28× ± 0.03** | **0.99× ± 0.01** |

- within-session relative sd: **3.0 %** (write-only 3.0 %)
- between-session relative sd: **2.0 %** (write-only 1.1 %)
- full spread across sessions: **4.3 %** of the mean
- verdict: comparable — pooling the sessions is safe

## Why this matters for the report

The report claims mean ± sd over at least three runs. If the between-session sd is the larger number, then a single session understates the uncertainty of every number quoted from it, and the report should cite the multi-session spread instead.
