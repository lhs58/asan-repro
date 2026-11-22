#!/usr/bin/env bash
# Extension experiment: change exactly ONE factor -- the compiler optimisation
# level -- and measure how ASan's relative cost depends on it.
#
# The paper reports every number at -O2 only (Sec. 4). Two hypotheses:
#   a) at -O0 the baseline is slower, so the instrumentation's *relative* cost
#      shrinks and the slowdown is clearly below the -O2 figure;
#   b) b4_float's 2.56x at -O2 comes mainly from lost auto-vectorisation (D16),
#      so it shrinks markedly at -O0, where nothing is vectorised anyway.
#
# 5 benchmarks x 4 levels x 2 builds x (1 warm-up + RUNS measured).
# Everything else is held fixed and matches scripts/run.sh: same sources, same
# iteration counts, same setarch -R wrapper (D14), same ASAN_OPTIONS minus
# max_redzone, which clang-14 clamps anyway (D18).
#
#   RUNS=5 bash scripts/extension_opt.sh      (normally via `make extension-opt`)
#
# Output: results/ext/opt-<stamp>-<host>.csv, columns
#     bench,level,mode,wall_s,vmpeak_kb,vmhwm_kb,vmsize_kb,checksum
# Kept out of results/raw/ so scripts/summarize.py keeps ignoring it.
set -uo pipefail

BENCHES="b1_allocs b2_pointer b3_int b4_float b5_string"
LEVELS="0 1 2 3"
MODES="base asan"
RUNS="${RUNS:-5}"
WARMUP="${WARMUP:-1}"

export ASAN_OPTIONS="malloc_context_size=0:quarantine_size_mb=0:detect_leaks=0"

STAMP="$(date +%Y%m%d-%H%M%S)"
HOST="$(hostname 2>/dev/null || echo unknown)"
OUT="results/ext/opt-${STAMP}-${HOST}.csv"
mkdir -p results/ext
printf 'bench,level,mode,wall_s,vmpeak_kb,vmhwm_kb,vmsize_kb,checksum\n' > "$OUT"

# Same reason as scripts/run.sh: without it ~27% of ASan runs die silently.
aslr=""
if command -v setarch >/dev/null 2>&1; then
  aslr="setarch $(uname -m) -R"
fi

# must match scripts/run.sh
args_for() {
  case "$1" in
    b1_allocs)  echo "56000000 4000" ;;
    b2_pointer) echo "300000 2000" ;;
    b3_int)     echo "1048576 1100" ;;
    b4_float)   echo "4096 400000" ;;
    b5_string)  echo "4194304 220" ;;
    *)          echo "" ;;
  esac
}

missing=0
for n in $LEVELS; do
  for m in $MODES; do
    for b in $BENCHES; do
      [ -x "build/$m-O$n/$b" ] || { echo "missing build/$m-O$n/$b - run 'make build-opt'" >&2; missing=1; }
    done
  done
done
[ "$missing" -eq 0 ] || exit 1

echo "session $STAMP on $HOST, RUNS=$RUNS" >&2
failed=0
for n in $LEVELS; do
  for b in $BENCHES; do
    for m in $MODES; do
      bin="build/$m-O$n/$b"
      if [ "$WARMUP" = "1" ]; then
        # shellcheck disable=SC2086
        $aslr "$bin" "$m" $(args_for "$b") > /dev/null 2>&1 || true
      fi
      for r in $(seq 1 "$RUNS"); do
        printf '\r  -O%s %-10s %-4s run %s/%s   ' "$n" "$b" "$m" "$r" "$RUNS" >&2
        # shellcheck disable=SC2086
        if line=$($aslr "$bin" "$m" $(args_for "$b")); then
          # bench,mode,... -> bench,level,mode,...
          echo "$line" | awk -F, -v lv="O$n" 'BEGIN{OFS=","} {$1=$1 OFS lv; print}' >> "$OUT"
        else
          echo "  FAILED: $bin (exit $?)" >&2
          failed=$((failed + 1))
        fi
      done
    done
  done
done
printf '\r%-50s\n' " " >&2

lines=$(( $(wc -l < "$OUT") - 1 ))
echo "wrote $OUT ($lines measurements)" >&2
expected=$(( 5 * 4 * 2 * RUNS ))
if [ "$lines" -ne "$expected" ] || [ "$failed" -ne 0 ]; then
  echo "warning: expected $expected measurements, got $lines ($failed failed)" >&2
  exit 1
fi
