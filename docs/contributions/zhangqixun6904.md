# Zhang Qixun (1240006904)

- GitHub: @zhangqixun6904
- 负责部分：文档一致性核对、报告与声明撰写（Week 6）

## Commits

| Commit | Date | What |
|---|---|---|
| `6f03bce` | 2026-10-31 | this file — group membership record |
| *Week 6* | 2026-11-25 | documentation consistency pass + `docs/report.md` + contribution / AI usage statements |
| *Week 6* | 2026-11-25 | `summarize.py` note fix + regenerated summary, the deck (`slides.pptx` / `.pdf`), speaker notes, `outline.md` and `results/README.md` corrections |

## Week 6 in detail

- Wrote [`docs/report.md`](../report.md): claims under test, method, results for C1–C3, the
  discrepancy analysis (allocator upper bound, read-side cost of `b4_float`, the clamped redzone,
  the ASLR failures), the `-O` extension and its interpretation, threats to validity, and both
  required statements.
- Fixed a real inconsistency: the committed data hold **270 rows = n = 18 per point**
  (3 + 5 + 5 + 5), but `README.md` (three places) and deviation D19 said `n = 13`. Re-checked against
  `results/raw/*.csv` row counts and corrected everywhere.
- Removed a stale claim from `README.md` §6.1: `b4_float` was still described as
  "dominated by de-vectorisation", an explanation D20 had already refuted.
- Filled the placeholder contribution and AI usage statements in `README.md` §9–§10 from `git log`
  and `docs/ai-log.md` rather than from memory.

## Week 6, second pass (2026-11-25)

- **The deck.** Wrote and laid out `presentation/slides.pptx` (12 slides: 8 numbered, footers
  `n / 8`, plus backup `B1`–`B4`) and exported `presentation/slides.pdf` from the same source, so the
  talk no longer depends on `outline.md` being read off a laptop. Every number on a slide is the one
  already in `results/`.
- **Speaker script for slides 3–4** (his own slot, 75 s) plus ten prepared Q&A answers with the file
  each answer comes from: `presentation/notes-zhangqixun.md`.
- **Fixed the generator, not just the output.** `scripts/summarize.py` still *generated* the refuted
  "de-vectorisation" sentence for `b4_float`, so the note would have come back on the next
  `make summarize`. Corrected the note, regenerated, and diffed: `results/summary.csv` byte-identical,
  `results/summary.md` changed in exactly that sentence — which also proves every committed summary
  number is reproducible from the committed raw CSVs.
- Corrected the same `n = 13` arithmetic slip where it had also survived, in
  `presentation/outline.md`; brought `results/README.md` up to date (the `ext/` directory it did not
  mention, and the PNG figure backend).
