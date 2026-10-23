#!/usr/bin/env python3
"""Aggregate results/raw/*.csv into a Paper-vs-Ours summary.

Input   results/raw/*.csv      bench,mode,wall_s,vmpeak_kb,vmhwm_kb,vmsize_kb,checksum
Output  results/summary.csv    machine-readable
        results/summary.md     paste-ready tables for the report

Statistics: mean and *sample* standard deviation (n-1) over the measured
repetitions, as the report requires (mean +/- sd over at least three runs).

Reference numbers from the paper:
    runtime overhead, all accesses   average slowdown 73 %   (Fig. 2)
    runtime overhead, write-only     average slowdown 26 %   (Sec. 4)
    memory overhead                  average 3.37x          (Tab. 1, VmPeak)

Memory note: the paper's 3.37x is a *VmPeak* figure measured in 2012. Current
64-bit ASan reserves 1/8 of the address space for shadow memory, and that
reservation inflates VmPeak by orders of magnitude without reflecting real
memory use. This script therefore reports VmHWM (peak RSS) as the primary
memory metric and keeps VmPeak visible so the discrepancy can be shown and
explained in the report rather than silently compared.
"""

from __future__ import annotations

import csv
import glob
import statistics
import sys
from collections import defaultdict

RAW_GLOB = "results/raw/*.csv"
OUT_MD = "results/summary.md"
OUT_CSV = "results/summary.csv"

MODES = ["base", "asan", "asanw"]
PAPER_SLOWDOWN_PCT = {"asan": 73.0, "asanw": 26.0}
PAPER_MEM = 3.37
ANALOGUE = {
    "b1_allocs": "400.perlbench (2.60x)",
    "b2_pointer": "429.mcf",
    "b3_int": "401.bzip2",
    "b4_float": "470.lbm",
    "b5_string": "483.xalancbmk (2.67x)",
}

# A VmPeak above this many kB (1 TB) means the shadow reservation is included.
SHADOW_SUSPICION_KB = 1 << 40


def load():
    files = sorted(glob.glob(RAW_GLOB))
    if not files:
        sys.exit(f"no raw data under {RAW_GLOB}; run 'make run' first")
    data = defaultdict(lambda: {"wall": [], "peak": [], "rss": [], "sum": []})
    for path in files:
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                key = (row["bench"], row["mode"])
                try:
                    data[key]["wall"].append(float(row["wall_s"]))
                    data[key]["peak"].append(float(row["vmpeak_kb"]))
                    data[key]["rss"].append(float(row["vmhwm_kb"]))
                    data[key]["sum"].append(row.get("checksum", ""))
                except (TypeError, ValueError, KeyError):
                    continue
    return data


def mean_sd(xs):
    if not xs:
        return (float("nan"), float("nan"))
    if len(xs) == 1:
        return (xs[0], 0.0)
    return (statistics.mean(xs), statistics.stdev(xs))


def fmt(m, sd, unit=""):
    if m != m:  # NaN
        return "—"
    return f"{m:.3f} ± {sd:.3f}{unit}"


def ratio(a, b):
    try:
        return a / b if b else float("nan")
    except ZeroDivisionError:
        return float("nan")


def main():
    data = load()
    benches = sorted({b for (b, _) in data})
    if not benches:
        sys.exit("no usable rows in the raw data")

    rows = []
    for b in benches:
        base_m, base_s = mean_sd(data[(b, "base")]["wall"])
        asan_m, asan_s = mean_sd(data[(b, "asan")]["wall"])
        asanw_m, asanw_s = mean_sd(data[(b, "asanw")]["wall"])
        base_rss, _ = mean_sd(data[(b, "base")]["rss"])
        asan_rss, _ = mean_sd(data[(b, "asan")]["rss"])
        base_peak, _ = mean_sd(data[(b, "base")]["peak"])
        asan_peak, _ = mean_sd(data[(b, "asan")]["peak"])

        sums = set(x for x in data[(b, "asan")]["sum"] if x)
        rows.append(dict(
            bench=b,
            n=len(data[(b, "asan")]["wall"]),
            base=(base_m, base_s), asan=(asan_m, asan_s), asanw=(asanw_m, asanw_s),
            ratio=ratio(asan_m, base_m), ratio_w=ratio(asanw_m, base_m),
            base_rss=base_rss, asan_rss=asan_rss, rss_ratio=ratio(asan_rss, base_rss),
            base_peak=base_peak, asan_peak=asan_peak, peak_ratio=ratio(asan_peak, base_peak),
            checksums=sums,
        ))

    def avg(key):
        vals = [r[key] for r in rows if r[key] == r[key]]
        return statistics.mean(vals) if vals else float("nan")

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["bench", "n", "base_s", "base_sd", "asan_s", "asan_sd",
                    "asanw_s", "asanw_sd", "slowdown", "slowdown_write_only",
                    "base_rss_kb", "asan_rss_kb", "rss_increase",
                    "base_vmpeak_kb", "asan_vmpeak_kb", "vmpeak_increase"])
        for r in rows:
            w.writerow([
                r["bench"], r["n"],
                f"{r['base'][0]:.6f}", f"{r['base'][1]:.6f}",
                f"{r['asan'][0]:.6f}", f"{r['asan'][1]:.6f}",
                f"{r['asanw'][0]:.6f}", f"{r['asanw'][1]:.6f}",
                f"{r['ratio']:.4f}", f"{r['ratio_w']:.4f}",
                f"{r['base_rss']:.1f}", f"{r['asan_rss']:.1f}", f"{r['rss_ratio']:.4f}",
                f"{r['base_peak']:.1f}", f"{r['asan_peak']:.1f}", f"{r['peak_ratio']:.4f}",
            ])

    n_runs = rows[0]["n"]
    out = [f"# Reproduction results\n",
           f"Generated by `scripts/summarize.py` from `results/raw/*.csv` "
           f"(n = {n_runs} measured runs per point, warm-up discarded).\n",
           "## Runtime overhead\n",
           "| Benchmark | Baseline (s) | ASan (s) | Slowdown | Write-only (s) | "
           "Slowdown | Paper's analogue |",
           "|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| `{r['bench']}` | {fmt(*r['base'])} | {fmt(*r['asan'])} | "
                   f"{r['ratio']:.2f}× | {fmt(*r['asanw'])} | {r['ratio_w']:.2f}× | "
                   f"{ANALOGUE.get(r['bench'], '')} |")
    asan_pct = (avg("ratio") - 1.0) * 100.0
    asanw_pct = (avg("ratio_w") - 1.0) * 100.0
    out.append(f"| **Mean** | | | **{1 + asan_pct / 100:.2f}× ({asan_pct:+.1f} %)** | | "
               f"**{1 + asanw_pct / 100:.2f}× ({asanw_pct:+.1f} %)** | "
               f"paper: {1 + PAPER_SLOWDOWN_PCT['asan'] / 100:.2f}× "
               f"(+{PAPER_SLOWDOWN_PCT['asan']:.0f} %), write-only "
               f"{1 + PAPER_SLOWDOWN_PCT['asanw'] / 100:.2f}× "
               f"(+{PAPER_SLOWDOWN_PCT['asanw']:.0f} %) |")
    out.append("")

    out.append("## Memory overhead\n")
    out.append("| Benchmark | Baseline RSS (MB) | ASan RSS (MB) | Increase | "
               "Baseline VmPeak (MB) | ASan VmPeak (MB) |")
    out.append("|---|---|---|---|---|---|")
    for r in rows:
        out.append(f"| `{r['bench']}` | {r['base_rss'] / 1024:.1f} | "
                   f"{r['asan_rss'] / 1024:.1f} | {r['rss_ratio']:.2f}× | "
                   f"{r['base_peak'] / 1024:.1f} | {r['asan_peak'] / 1024:.1f} |")
    out.append(f"| **Mean** | | | **{avg('rss_ratio'):.2f}×** "
               f"(paper: {PAPER_MEM:.2f}×) | | |")
    out.append("")

    big = [r for r in rows if r["asan_peak"] > SHADOW_SUSPICION_KB]
    if big:
        out.append("> **VmPeak is not usable as the paper's metric here.** "
                   "The ASan builds report VmPeak in the terabyte range: the "
                   "one-eighth shadow reservation is mapped as PROT_NONE and "
                   "counted in VmSize, but untouched pages are never resident. "
                   "Peak RSS (VmHWM) is the comparable quantity; the VmPeak "
                   "column is kept to document the effect.\n")
    else:
        out.append("> VmPeak stayed below 1 TB, so the shadow reservation did "
                   "not dominate the measurement on this machine. If that "
                   "changes, re-read the caveat in `bench/common.h`.\n")

    inconsistent = [r["bench"] for r in rows if len(r["checksums"]) > 1]
    if inconsistent:
        out.append(f"> **WARNING:** more than one checksum observed for: "
                   f"{', '.join(inconsistent)}. The builds are not computing the "
                   f"same thing — timings must be discarded.\n")
    else:
        out.append("> Checksums are identical across modes for every benchmark, "
                   "so the instrumented builds computed the same results.\n")

    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print("\n".join(out))
    print(f"\nwrote {OUT_MD} and {OUT_CSV}", file=sys.stderr)


if __name__ == "__main__":
    main()
