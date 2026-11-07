#!/usr/bin/env python3
"""Summarise the redzone-size extension into results/ext/summary.md.

Input   results/ext/redzone-*.csv   bench,variant,redzone,wall_s,vmpeak_kb,...
        results/ext/detection.md    written by scripts/extension_redzone.sh
Output  results/ext/summary.md      paste-ready table for the report

The question: the paper says a bigger heap redzone costs more time and memory
but finds more heap-buffer-overflows (Sec. 4.3 / Sec. 3.5). We vary exactly one
factor -- max_redzone -- and measure both sides.
"""

from __future__ import annotations

import csv
import glob
import statistics
import sys
from collections import defaultdict

RAW_GLOB = "results/ext/redzone-*.csv"
OUT = "results/ext/summary.md"


def main() -> None:
    files = sorted(glob.glob(RAW_GLOB))
    if not files:
        sys.exit(f"no data under {RAW_GLOB}; run 'make extension' first")

    # (bench, redzone) -> {"wall": [...], "rss": [...]}
    data: dict[tuple[str, str], dict[str, list[float]]] = defaultdict(
        lambda: {"wall": [], "rss": [], "chk": []}
    )
    for path in files:
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                key = (row["bench"], row["redzone"])
                try:
                    data[key]["wall"].append(float(row["wall_s"]))
                    data[key]["rss"].append(float(row["vmhwm_kb"]))
                    data[key]["chk"].append(row["checksum"])
                except (TypeError, ValueError, KeyError):
                    continue

    benches = sorted({b for (b, _) in data})
    redzones = sorted({int(r) for (_, r) in data if int(r) > 0})

    def mean(xs: list[float]) -> float:
        return statistics.mean(xs) if xs else float("nan")

    def sd(xs: list[float]) -> float:
        return statistics.stdev(xs) if len(xs) > 1 else 0.0

    out = ["# Extension: heap redzone size\n",
           "One factor changed (`ASAN_OPTIONS=...:max_redzone=N`), everything else",
           "fixed: same binaries, same machine, same session, same iteration counts,",
           "ASLR disabled. n = "
           f"{len(data[(benches[0], str(redzones[0]))]['wall'])} runs per point.\n",
           "## Cost side (paper Sec. 4.3: larger redzone may cost time and memory)\n"]

    for b in benches:
        base_wall = mean(data[(b, "0")]["wall"])
        base_rss = mean(data[(b, "0")]["rss"])
        out.append(f"### `{b}`\n")
        out.append("| max_redzone | wall (s) | slowdown vs baseline | peak RSS (MB) | RSS increase |")
        out.append("|---|---|---|---|---|")
        out.append(f"| baseline (no ASan) | {base_wall:.3f} ± {sd(data[(b, '0')]['wall']):.3f} "
                   f"| 1.00× | {base_rss / 1024:.1f} | 1.00× |")
        for rz in redzones:
            xs = data[(b, str(rz))]["wall"]
            rs = data[(b, str(rz))]["rss"]
            if not xs:
                continue
            out.append(
                f"| {rz} | {mean(xs):.3f} ± {sd(xs):.3f} | "
                f"{mean(xs) / base_wall:.2f}× | {mean(rs) / 1024:.1f} | "
                f"{mean(rs) / base_rss:.2f}× |"
            )
        out.append("")

    out.append("## Detection side (paper Sec. 3.5)\n")
    try:
        with open("results/ext/detection.md", encoding="utf-8") as fh:
            body = fh.read()
        # drop the H1; the section header above already says what this is
        out.append("\n".join(body.splitlines()[1:]).strip())
    except FileNotFoundError:
        out.append("_detection.md missing — rerun scripts/extension_redzone.sh_")
    out.append("")

    chk_bad = [b for b in benches
               if len({c for (bb, rz), v in data.items() if bb == b for c in v["chk"]}) > 1]
    if chk_bad:
        out.append(f"> **WARNING:** checksums differ for {', '.join(chk_bad)} — "
                   "the redzone should not change computed results.\n")
    else:
        out.append("> Checksums are identical across all redzone sizes, so the "
                   "option changed performance only, not the computed results.\n")

    text = "\n".join(out)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(text)
    print(f"\nwrote {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
