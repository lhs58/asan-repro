# Pan Haodong (1240010383)

- GitHub: @jeff-feng-dot
- 负责部分：报告撰写 / 展示 / Week-5 扩展实验

## Commits

| Commit | Date | What |
|---|---|---|
| `cd528fc` | 2026-11-01 | this file — group membership record |
| `2531cf4` | 2026-11-22 | `ext:` sweep the optimisation level `-O0..-O3`, base vs asan |
| `8c19758` | 2026-11-22 | `figures:` 300 dpi PNG output and Fig. 3 (slowdown per optimisation level) |
| `b2b01a9` | 2026-11-22 | `presentation:` 8-slide outline with speakers, timing and source per slide |
| `140e159` | 2026-11-22 | `docs:` record the `-O` sweep as D20 and start the AI usage log |

## Week 5 in detail

- Hypothesis-driven extension: if ASan's checks are optimisation barriers, the *relative* cost
  should grow with `-O`. Built `scripts/extension_opt.sh` (four optimisation levels × three modes ×
  five repetitions = 200 measurements) and `scripts/summarize_opt.py`, and wrote the result up in
  [`results/ext/opt-summary.md`](../../results/ext/opt-summary.md).
- Second hypothesis — that `b4_float`'s cost is de-vectorisation — was tested and **rejected**
  (already 2.54× at `-O1`, where clang-14 runs no loop vectoriser; `-Rpass` shows the loop is not
  vectorised in either `-O2` build). Recorded as D20, with the refutation written down instead of
  the tidier story.
- Presentation: [`presentation/outline.md`](../../presentation/outline.md), speakers s1–s2.
- Logged all of the above — including the fact that an AI assistant wrote the extension scripts and
  made the verdict change — in [`docs/ai-log.md`](../ai-log.md).
