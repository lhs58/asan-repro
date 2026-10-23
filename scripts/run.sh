#!/usr/bin/env bash
# Collect RUNS measured repetitions of every benchmark in every build mode.
#
#   RUNS=3 CPU_PIN=2 bash scripts/run.sh
#
# Writes results/raw/<timestamp>-<host>.csv with columns
#     bench,mode,wall_s,vmpeak_kb,checksum
# One warm-up repetition per (benchmark, mode) is discarded before measuring,
# so the first page-fault-heavy run does not pollute the sample.
set -uo pipefail

BENCHES="b1_allocs b2_pointer b3_int b4_float b5_string"
MODES="base asan asanw"
RUNS="${RUNS:-3}"
WARMUP="${WARMUP:-1}"
PIN="${CPU_PIN:-}"

STAMP="$(date +%Y%m%d-%H%M%S)"
HOST="$(hostname 2>/dev/null || echo unknown)"
OUT="results/raw/${STAMP}-${HOST}.csv"
mkdir -p results/raw
printf 'bench,mode,wall_s,vmpeak_kb,vmhwm_kb,vmsize_kb,checksum\n' > "$OUT"

pin=""
if [ -n "$PIN" ] && command -v taskset >/dev/null 2>&1; then
  pin="taskset -c $PIN"
fi

# iterations: tuned so a baseline run takes ~1 s on a modern laptop CPU.
args_for() {
  case "$1" in
    b1_allocs)  echo "8000000 4000" ;;
    b2_pointer) echo "300000 1000" ;;
    b3_int)     echo "1048576 500" ;;
    b4_float)   echo "4096 20000" ;;
    b5_string)  echo "4194304 40" ;;
    *)          echo "" ;;
  esac
}

missing=0
for b in $BENCHES; do
  for m in $MODES; do
    [ -x "build/$m/$b" ] || { echo "missing build/$m/$b - run 'make build'" >&2; missing=1; }
  done
done
[ "$missing" -eq 0 ] || exit 1

if [ "$WARMUP" = "1" ]; then
  echo "warm-up..." >&2
  for b in $BENCHES; do
    for m in $MODES; do
      # shellcheck disable=SC2086
      $pin "build/$m/$b" "$m" $(args_for "$b") > /dev/null 2>&1 || true
    done
  done
fi

for r in $(seq 1 "$RUNS"); do
  for b in $BENCHES; do
    for m in $MODES; do
      # shellcheck disable=SC2086
      $pin "build/$m/$b" "$m" $(args_for "$b") >> "$OUT"
      printf '\r  run %s/%s  %-10s %-5s   ' "$r" "$RUNS" "$b" "$m" >&2
    done
  done
done
printf '\r%-45s\n' " " >&2

lines=$(( $(wc -l < "$OUT") - 1 ))
echo "wrote $OUT ($lines measurements)" >&2
if [ "$lines" -lt 9 ]; then
  echo "warning: fewer measurements than expected" >&2
fi
