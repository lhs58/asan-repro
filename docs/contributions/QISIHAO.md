# Qi Sihao (1240012742)

- GitHub: @QISIHAO
- 负责部分：统计与图表（figures pipeline and Fig. 1–2）

## Commits

| Commit | Date | What |
|---|---|---|
| `7193b39` | 2026-10-31 | this file — group membership record |
| `5dafd5d` | 2026-11-07 | `figures:` render Fig. 1 and Fig. 2 from `summary.csv` |

## Detail

- Wrote [`scripts/figures.py`](../../scripts/figures.py) (389 lines) and the `make figures` target:
  reads `results/summary.csv`, renders the runtime and memory figures as SVG and PDF with
  propagated error bars, and writes the Markdown captions used in the README.
- Updated `README.md` §6 and `results/README.md` so that the figure source path and the choice of
  peak RSS over `VmPeak` are stated next to the figures themselves.
- The figures were subsequently re-rendered at 300 dpi with an added Fig. 3 by Pan Haodong; the
  plotting pipeline is still the original one.
