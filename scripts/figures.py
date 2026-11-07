#!/usr/bin/env python3
"""Render the report figures from results/summary.csv.

    results/figures/slowdown.svg / .pdf   Fig. 1  runtime overhead per benchmark
    results/figures/memory.svg   / .pdf   Fig. 2  peak-RSS increase per benchmark

Both formats are vector. The PDF is what the report embeds; the SVG is what
GitHub renders inline in README section 6, so the weekly check can see the
figure without downloading anything.

The pinned container installs python3 and no plotting library (see Dockerfile),
so this script is standard library only and draws both formats by hand. Output
is deterministic: same summary.csv in, byte-identical files out, so a re-run
never produces a noisy diff.

Error bars in Fig. 1 are propagated from the per-mode standard deviations that
scripts/summarize.py records:

    sd(base/asan) = ratio * sqrt( (sd_a/mean_a)^2 + (sd_b/mean_b)^2 )

the usual first-order approximation for a ratio of two independent means.
Fig. 2 has no error bars because summary.csv does not carry a VmHWM spread; the
per-run values are in results/raw/*.csv if the report needs them.

Bars are horizontal so that every value label sits at the end of its own bar and
two nearby values (b1: 10.36x vs 10.35x) can never collide.
"""

from __future__ import annotations

import csv
import math
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUMMARY = ROOT / "results" / "summary.csv"
OUTDIR = ROOT / "results" / "figures"

# Paper reference values, each tied to the claim it supports (docs/claims.md).
PAPER_ASAN = 1.73  # Fig. 2, average 73 % slowdown
PAPER_ASANW = 1.26  # Sec. 4, write-only average 26 % slowdown
PAPER_MEM = 3.37  # Table 1, average VmPeak increase

W, H = 920, 470
LEFT, RIGHT, TOP, BOTTOM = 118, 26, 62, 74

C_ASAN = "#2f6db5"
C_ASANW = "#d9822b"
C_GRID = "#e7e7e7"
C_AXIS = "#3d3d3d"
C_TEXT = "#1f1f1f"
C_MUTED = "#6f6f6f"
C_REF = "#8c8c8c"
C_ERR = "#2b2b2b"

FONT = "Helvetica, Arial, sans-serif"

# Helvetica advance widths, 1/1000 em (AFM). Only the glyphs these figures use.
HELV = {
    " ": 278, "!": 278, '"': 355, "#": 556, "$": 556, "%": 889, "&": 667,
    "'": 191, "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333,
    ".": 278, "/": 278, "0": 556, "1": 556, "2": 556, "3": 556, "4": 556,
    "5": 556, "6": 556, "7": 556, "8": 556, "9": 556, ":": 278, ";": 278,
    "<": 584, "=": 584, ">": 584, "?": 556, "@": 1015, "A": 667, "B": 667,
    "C": 722, "D": 722, "E": 667, "F": 611, "G": 778, "H": 722, "I": 278,
    "J": 500, "K": 667, "L": 556, "M": 833, "N": 722, "O": 778, "P": 667,
    "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722, "V": 667, "W": 944,
    "X": 667, "Y": 667, "Z": 611, "[": 278, "\\": 278, "]": 278, "^": 469,
    "_": 556, "`": 333, "a": 556, "b": 556, "c": 500, "d": 556, "e": 556,
    "f": 278, "g": 556, "h": 556, "i": 222, "j": 222, "k": 500, "l": 222,
    "m": 833, "n": 556, "o": 556, "p": 556, "q": 556, "r": 333, "s": 500,
    "t": 278, "u": 556, "v": 500, "w": 722, "x": 500, "y": 500, "z": 500,
    "{": 334, "|": 260, "}": 334, "~": 584, "\u00d7": 584, "\u00b1": 584,
}


def text_width(s: str, size: float, bold: bool = False) -> float:
    per_mille = sum(HELV.get(ch, 556) for ch in s)
    return per_mille * size / 1000.0 * (1.04 if bold else 1.0)


class Canvas:
    """Device-independent drawing list, rendered by either backend."""

    def __init__(self) -> None:
        self.items: list[tuple] = []

    def rect(self, x: float, y: float, w: float, h: float, fill: str,
             rx: float = 0.0) -> None:
        self.items.append(("rect", x, y, w, h, fill, rx))

    def line(self, x1: float, y1: float, x2: float, y2: float, colour: str,
             width: float = 1.0, dash: str = "") -> None:
        self.items.append(("line", x1, y1, x2, y2, colour, width, dash))

    def text(self, x: float, y: float, s: str, size: float,
             colour: str = C_TEXT, anchor: str = "start", bold: bool = False) -> None:
        self.items.append(("text", x, y, s, size, colour, anchor, bold))


def _hex(colour: str) -> tuple[int, int, int]:
    c = colour.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def to_svg(canvas: Canvas, path: Path, title: str) -> None:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="{escape(title)}">',
        f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
    ]
    for item in canvas.items:
        kind = item[0]
        if kind == "rect":
            _, x, y, w, h, fill, rx = item
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                f'fill="{fill}"' + (f' rx="{rx:.1f}"' if rx else "") + "/>"
            )
        elif kind == "line":
            _, x1, y1, x2, y2, colour, width, dash = item
            d = f' stroke-dasharray="{dash}"' if dash else ""
            parts.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="{colour}" stroke-width="{width}"{d}/>'
            )
        else:
            _, x, y, s, size, colour, anchor, bold = item
            weight = ' font-weight="bold"' if bold else ""
            parts.append(
                f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" '
                f'font-size="{size}" fill="{colour}" text-anchor="{anchor}"'
                f'{weight}>{escape(s)}</text>'
            )
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8", newline="\n")


def _pdf_escape(s: str) -> str:
    out = []
    for ch in s:
        if ch in "()\\":
            out.append("\\" + ch)
        elif 32 <= ord(ch) <= 126:
            out.append(ch)
        else:
            out.append("\\%03o" % ch.encode("latin-1", "replace")[0])
    return "".join(out)


def to_pdf(canvas: Canvas, path: Path, title: str) -> None:
    """Minimal single-page PDF: filled rectangles, lines, Helvetica text."""
    ops: list[str] = []

    def colour_op(colour: str, stroke: bool) -> str:
        r, g, b = _hex(colour)
        return f"{r / 255:.4f} {g / 255:.4f} {b / 255:.4f} {'RG' if stroke else 'rg'}"

    for item in canvas.items:
        kind = item[0]
        if kind == "rect":
            _, x, y, w, h, fill, _rx = item
            ops.append(colour_op(fill, stroke=False))
            ops.append(f"{x:.2f} {H - y - h:.2f} {w:.2f} {h:.2f} re f")
        elif kind == "line":
            _, x1, y1, x2, y2, colour, width, dash = item
            ops.append(colour_op(colour, stroke=True))
            ops.append(f"{width:.2f} w")
            ops.append(f"[{' '.join(dash.split()) if dash else ''}] 0 d")
            ops.append(f"{x1:.2f} {H - y1:.2f} m {x2:.2f} {H - y2:.2f} l S")
        else:
            _, x, y, s, size, colour, anchor, bold = item
            width = text_width(s, size, bold)
            dx = -width / 2 if anchor == "middle" else (-width if anchor == "end" else 0.0)
            font = "/F2" if bold else "/F1"
            ops.append(
                f"BT {font} {size:.2f} Tf 1 0 0 1 {x + dx:.2f} {H - y:.2f} Tm "
                f"{colour_op(colour, stroke=False)} ({_pdf_escape(s)}) Tj ET"
            )

    content = ("\n".join(ops) + "\n").encode("latin-1", "replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] /Resources "
        f"<< /Font << /F1 5 0 R /F2 6 0 R >> >> /Contents 4 0 R >>".encode(),
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n"
        + content + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
        b"/Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold "
        b"/Encoding /WinAnsiEncoding >>",
        b"<< /Title (" + _pdf_escape(title).encode("latin-1") + b") /Producer "
        b"(scripts/figures.py) >>",
    ]

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R /Info 7 0 R >>\n"
        f"startxref\n{xref_at}\n%%EOF\n"
    ).encode()
    path.write_bytes(bytes(out))


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        sys.exit(f"figures: {path} not found - run 'make run' and 'make summarize' first")
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        sys.exit(f"figures: {path} is empty")
    return rows


def _f(row: dict[str, str], key: str) -> float:
    try:
        return float(row[key])
    except (KeyError, ValueError):
        sys.exit(f"figures: summary.csv is missing a numeric column {key!r}")


def ratio_sd(mean_a: float, sd_a: float, mean_b: float, sd_b: float) -> float:
    """First-order standard deviation of mean_a / mean_b."""
    if mean_a <= 0 or mean_b <= 0:
        return 0.0
    return (mean_a / mean_b) * math.hypot(sd_a / mean_a, sd_b / mean_b)


def nice_ticks(vmax: float, target: int = 5) -> tuple[list[float], float]:
    if vmax <= 0:
        return [0.0, 1.0], 1.0
    raw = vmax / target
    mag = 10 ** math.floor(math.log10(raw))
    step = 10 * mag
    for m in (1, 2, 2.5, 5, 10):
        if m * mag >= raw:
            step = m * mag
            break
    top = math.ceil(vmax / step) * step
    return [i * step for i in range(int(round(top / step)) + 1)], top


def plot(rows: list[dict[str, str]],
         series: list[tuple[str, str, str, str]],
         refs: list[tuple[float, str]],
         title: str, subtitle: str, xlabel: str) -> Canvas:
    """series: (value_col, sd_col_or_empty, colour, legend_label)."""
    canvas = Canvas()
    plot_w = W - LEFT - RIGHT
    plot_h = H - TOP - BOTTOM
    x0, ytop = LEFT, TOP
    x1, ybottom = LEFT + plot_w, TOP + plot_h

    values = [ref for ref, _ in refs]
    for col, sd_col, _c, _l in series:
        for row in rows:
            values.append(_f(row, col) + (_f(row, sd_col) if sd_col else 0.0))
    ticks, vmax = nice_ticks(max(values) * 1.06)

    def sx(v: float) -> float:
        return x0 + (v / vmax) * plot_w

    canvas.rect(0, 0, W, H, "#ffffff")
    canvas.text(LEFT, 28, title, 16, C_TEXT, bold=True)
    canvas.text(LEFT, 48, subtitle, 12, C_MUTED)

    for t in ticks:
        canvas.line(sx(t), ytop, sx(t), ybottom, C_GRID if t else C_AXIS, 1.0)
        canvas.text(sx(t), ybottom + 20, f"{t:g}", 11, C_MUTED, anchor="middle")

    canvas.line(x0, ybottom, x1, ybottom, C_AXIS, 1.0)
    canvas.text((x0 + x1) / 2, ybottom + 48, xlabel, 12, C_TEXT, anchor="middle")

    for ref, _label in refs:
        canvas.line(sx(ref), ytop, sx(ref), ybottom, C_REF, 1.2, "6 4")

    n = len(rows)
    band = plot_h / n
    k = len(series)
    bar_h = min(21.0, band * 0.34)
    gap = 3.0
    total = k * bar_h + (k - 1) * gap

    for i, row in enumerate(rows):
        cy = ytop + band * (i + 0.5)
        top = cy - total / 2
        canvas.text(x0 - 10, cy + 4, row["bench"], 12, C_TEXT, anchor="end")
        for j, (col, sd_col, colour, _label) in enumerate(series):
            v = _f(row, col)
            by = top + j * (bar_h + gap)
            length = max(2.0, (v / vmax) * plot_w)
            canvas.rect(x0, by, length, bar_h, colour, rx=1.5)
            right = x0 + length
            if sd_col:
                sd = _f(row, sd_col)
                lo, hi = max(0.0, v - sd), v + sd
                mx = x0 + (v / vmax) * plot_w
                canvas.line(mx, by + 1, mx, by + bar_h - 1, C_ERR, 1.0)
                for cap in (lo, hi):
                    cx = x0 + (cap / vmax) * plot_w
                    canvas.line(cx, by + bar_h / 2 - 4, cx, by + bar_h / 2 + 4, C_ERR, 1.0)
                right = max(right, x0 + (hi / vmax) * plot_w)
            canvas.text(right + 8, by + bar_h / 2 + 3.5, f"{v:.2f}\u00d7", 10.5, C_TEXT)

    entries = [(colour, label, False) for _c, _s, colour, label in series]
    entries += [(C_REF, label, True) for _r, label in refs]
    widths = [18 + text_width(label, 11) + 14 for _c, label, _k in entries]
    box_w = sum(widths) + 8
    box_x = x1 - box_w
    box_y = ybottom - 30
    canvas.rect(box_x, box_y, box_w, 24, "#ffffff")
    canvas.line(box_x, box_y, box_x + box_w, box_y, C_GRID, 1.0)
    lx = box_x + 8
    for (colour, label, is_ref), wd in zip(entries, widths):
        if is_ref:
            canvas.line(lx, box_y + 12, lx + 12, box_y + 12, C_REF, 1.2, "6 4")
        else:
            canvas.rect(lx, box_y + 7, 12, 10, colour, rx=1.0)
        canvas.text(lx + 18, box_y + 16, label, 11, C_TEXT)
        lx += wd

    return canvas


def main() -> None:
    rows = load_rows(SUMMARY)
    for row in rows:
        base = _f(row, "base_s")
        row["slowdown_sd"] = str(
            ratio_sd(_f(row, "asan_s"), _f(row, "asan_sd"), base, _f(row, "base_sd"))
        )
        row["slowdown_write_only_sd"] = str(
            ratio_sd(_f(row, "asanw_s"), _f(row, "asanw_sd"), base, _f(row, "base_sd"))
        )

    figures = [
        (
            plot(
                rows,
                [
                    ("slowdown", "slowdown_sd", C_ASAN, "ASan, all accesses"),
                    ("slowdown_write_only", "slowdown_write_only_sd", C_ASANW,
                     "write-only"),
                ],
                [(PAPER_ASAN, f"paper {PAPER_ASAN:.2f}\u00d7"),
                 (PAPER_ASANW, f"paper {PAPER_ASANW:.2f}\u00d7")],
                "Runtime overhead vs. clang -O2 baseline",
                "Five workloads, n = 3 runs after one discarded warm-up; bars are "
                "mean slowdown, whiskers the propagated standard deviation.",
                "slowdown (x baseline)",
            ),
            "slowdown",
            "Runtime overhead of AddressSanitizer on five workloads",
        ),
        (
            plot(
                rows,
                [("rss_increase", "", C_ASAN, "peak RSS increase")],
                [(PAPER_MEM, f"paper {PAPER_MEM:.2f}\u00d7 (VmPeak)")],
                "Peak memory increase over the baseline",
                "VmHWM (peak resident set) read from /proc/self/status; the paper's "
                "3.37\u00d7 is a VmPeak figure and is shown for orientation only.",
                "increase (x baseline)",
            ),
            "memory",
            "Peak memory increase of AddressSanitizer on five workloads",
        ),
    ]

    OUTDIR.mkdir(parents=True, exist_ok=True)
    for canvas, name, title in figures:
        to_svg(canvas, OUTDIR / f"{name}.svg", title)
        to_pdf(canvas, OUTDIR / f"{name}.pdf", title)
        print(f"wrote results/figures/{name}.svg and .pdf", file=sys.stderr)


if __name__ == "__main__":
    main()
