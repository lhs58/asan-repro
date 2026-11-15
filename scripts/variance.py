#!/usr/bin/env python3
"""Separate within-session noise from between-session drift.

Input   results/raw/*.csv   one file per measurement session
Output  results/variance.md

A single session of five repetitions can only show how much the machine
wanders *while the session runs*. It cannot show whether the numbers would
come out the same on another evening, after a reboot, or with a different
thermal state. With at least three sessions we can measure both:

    within  = mean over sessions of the propagated sd of the ratio
    between = sd of the per-session ratios / their mean

If `between` is comparable to `within`, the session boundary does not matter
and pooling is safe. If `between` is much larger, the report has to say so and
quote the spread, not a single session's mean.

Session identity comes from the filename, which scripts/run.sh stamps as
<date>-<time>-<host>.csv, so no extra column is needed in the data.
"""

from __future__ import annotations

import csv
import glob
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

RAW_GLOB = "results/raw/*.csv"
OUT = "results/variance.md"


def load():
    files = sorted(glob.glob(RAW_GLOB))
    if not files:
        sys.exit(f"no raw data under {RAW_GLOB}; run 'make run' first")
    # (session, bench, mode) -> [wall_s, ...]
    data = defaultdict(list)
    for path in files:
        session = Path(path).stem
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                try:
                    data[(session, row["bench"], row["mode"])].append(float(row["wall_s"]))
                except (TypeError, ValueError, KeyError):
                    continue
    return data, [Path(p).stem for p in files]


def mean_sd(xs):
    if not xs:
        return float("nan"), float("nan")
    if len(xs) == 1:
        return xs[0], 0.0
    return statistics.mean(xs), statistics.stdev(xs)


def ratio_sd(a, sd_a, b, sd_b):
    """First-order sd of a/b, same formula as scripts/figures.py."""
    if a <= 0 or b <= 0:
        return 0.0
    return (a / b) * math.hypot(sd_a / a, sd_b / b)


def main() -> None:
    data, sessions = load()
    benches = sorted({b for (_, b, _) in data})

    out = ["# Session-to-session variance\n",
           f"{len(sessions)} measurement sessions: "
           + ", ".join(f"`{s}`" for s in sessions) + "\n",
           "`within` is the propagated standard deviation of the slowdown inside "
           "one session; `between` is the standard deviation of the per-session "
           "slowdown means. Both are relative (sd / mean).\n"]

    summary_rows = []
    for b in benches:
        out.append(f"## `{b}`\n")
        out.append("| session | n | baseline (s) | ASan (s) | slowdown | write-only |")
        out.append("|---|---|---|---|---|---|")
        ratios, ratios_w, within_rel, within_rel_w = [], [], [], []
        for s in sessions:
            base = data.get((s, b, "base"), [])
            asan = data.get((s, b, "asan"), [])
            asanw = data.get((s, b, "asanw"), [])
            if not base or not asan:
                continue
            bm, bsd = mean_sd(base)
            am, asd = mean_sd(asan)
            wm, wsd = mean_sd(asanw)
            r = am / bm
            rw = wm / bm if bm else float("nan")
            rsd = ratio_sd(am, asd, bm, bsd)
            rwsd = ratio_sd(wm, wsd, bm, bsd) if bm else 0.0
            ratios.append(r)
            ratios_w.append(rw)
            within_rel.append(rsd / r if r else 0.0)
            within_rel_w.append(rwsd / rw if rw else 0.0)
            out.append(f"| `{s}` | {len(asan)} | {bm:.3f} | {am:.3f} | "
                       f"{r:.2f}× | {rw:.2f}× |")
        if len(ratios) < 2:
            out.append("")
            out.append("_Only one session — between-session spread cannot be "
                       "estimated yet._\n")
            continue

        between = statistics.stdev(ratios) / statistics.mean(ratios)
        between_w = statistics.stdev(ratios_w) / statistics.mean(ratios_w)
        rng = (max(ratios) - min(ratios)) / statistics.mean(ratios)
        w_mean = statistics.mean(within_rel)
        w_mean_w = statistics.mean(within_rel_w)
        out.append(f"| **between sessions** | | | | "
                   f"**{statistics.mean(ratios):.2f}× ± "
                   f"{statistics.stdev(ratios):.2f}** | "
                   f"**{statistics.mean(ratios_w):.2f}× ± "
                   f"{statistics.stdev(ratios_w):.2f}** |")
        out.append("")
        out.append(f"- within-session relative sd: **{w_mean * 100:.1f} %** "
                   f"(write-only {w_mean_w * 100:.1f} %)")
        out.append(f"- between-session relative sd: **{between * 100:.1f} %** "
                   f"(write-only {between_w * 100:.1f} %)")
        out.append(f"- full spread across sessions: **{rng * 100:.1f} %** of the mean")
        verdict = ("comparable — pooling the sessions is safe"
                   if between <= max(2 * w_mean, 0.02)
                   else "larger than the within-session noise — quote the spread")
        out.append(f"- verdict: {verdict}\n")
        summary_rows.append((b, w_mean, between))

    out.append("## Why this matters for the report\n")
    out.append("The report claims mean ± sd over at least three runs. If the "
               "between-session sd is the larger number, then a single session "
               "understates the uncertainty of every number quoted from it, and "
               "the report should cite the multi-session spread instead.\n")

    text = "\n".join(out)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(text)
    print(f"\nwrote {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
