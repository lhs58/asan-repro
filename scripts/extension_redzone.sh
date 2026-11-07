#!/usr/bin/env bash
# Extension experiment: change exactly ONE factor -- the heap redzone size --
# and measure both sides of the trade-off the paper describes in Sec. 4.3:
#
#   "Size of the heap redzone (default: 128 bytes). This option affects the
#    ability to find heap-buffer-overflow bugs (see Section 3.5). Large values
#    may lead to significant slowdown and increased memory usage, especially if
#    the tested program allocates many small chunks of heap memory."
#
# Part 1 (cost)      : wall time and peak RSS at max_redzone = 32/64/128/256.
# Part 2 (detection) : a write 40 bytes past a 16-byte allocation. If the
#                      redzone is shorter than that offset, the write lands
#                      outside the poisoned region and the bug is missed.
#
# Everything else is held fixed: same binaries, same machine, same session,
# same iteration counts as scripts/run.sh, same setarch -R wrapper.
#
#   RUNS=5 bash scripts/extension_redzone.sh
#
# Output: results/ext/redzone-<stamp>-<host>.csv  (kept out of results/raw/
# so scripts/summarize.py keeps ignoring it) and results/ext/detection.md
set -uo pipefail

BENCHES="b1_allocs b2_pointer b5_string"
REDZONES="32 64 128 256"
RUNS="${RUNS:-5}"
WARMUP="${WARMUP:-1}"

# Same base options as the main measurement; only max_redzone varies.
BASE_OPTS="malloc_context_size=0:quarantine_size_mb=0:detect_leaks=0"

STAMP="$(date +%Y%m%d-%H%M%S)"
HOST="$(hostname 2>/dev/null || echo unknown)"
OUT="results/ext/redzone-${STAMP}-${HOST}.csv"
mkdir -p results/ext
printf 'bench,variant,redzone,wall_s,vmpeak_kb,vmhwm_kb,vmsize_kb,checksum\n' > "$OUT"

aslr=""
if command -v setarch >/dev/null 2>&1; then
  aslr="setarch $(uname -m) -R"
fi

# must match scripts/run.sh
args_for() {
  case "$1" in
    b1_allocs)  echo "56000000 4000" ;;
    b2_pointer) echo "300000 2000" ;;
    b5_string)  echo "4194304 220" ;;
    *)          echo "" ;;
  esac
}

need() { [ -x "$1" ] || { echo "missing $1 - run 'make build'" >&2; exit 1; }; }
for b in $BENCHES; do
  need "build/base/$b"
  need "build/asan/$b"
done

echo "session $STAMP on $HOST, RUNS=$RUNS" >&2

# ---------------------------------------------------------------- part 1: cost
# One baseline measurement per benchmark: the baseline does not depend on any
# ASan option, so it is measured once and reused for every redzone.
for b in $BENCHES; do
  echo "  baseline $b" >&2
  if [ "$WARMUP" = "1" ]; then
    # shellcheck disable=SC2086
    $aslr "build/base/$b" base $(args_for "$b") > /dev/null 2>&1
  fi
  for r in $(seq 1 "$RUNS"); do
    # shellcheck disable=SC2086
    line=$($aslr "build/base/$b" base $(args_for "$b") 2>/dev/null)
    echo "${line},0" | awk -F, '{printf "%s,%s,%s,%s,%s,%s,%s,%s\n",$1,$2,$NF,$3,$4,$5,$6,$7}' \
      >> "$OUT"
  done
done

for rz in $REDZONES; do
  for b in $BENCHES; do
    echo "  redzone=$rz $b" >&2
    if [ "$WARMUP" = "1" ]; then
      # shellcheck disable=SC2086
      ASAN_OPTIONS="$BASE_OPTS:max_redzone=$rz" \
        $aslr "build/asan/$b" asan $(args_for "$b") > /dev/null 2>&1
    fi
    for r in $(seq 1 "$RUNS"); do
      # shellcheck disable=SC2086
      line=$(ASAN_OPTIONS="$BASE_OPTS:max_redzone=$rz" \
             $aslr "build/asan/$b" asan $(args_for "$b") 2>/dev/null)
      echo "${line},$rz" | awk -F, '{printf "%s,%s,%s,%s,%s,%s,%s,%s\n",$1,$2,$NF,$3,$4,$5,$6,$7}' \
        >> "$OUT"
    done
  done
done

echo "wrote $OUT" >&2
echo "measurements: $(( $(wc -l < "$OUT") - 1 ))" >&2

# ----------------------------------------------------------- part 2: detection
# A fixed out-of-bounds write, at a distance that a short redzone cannot cover.
PROBE=build/ext/overflow_probe
mkdir -p build/ext
cat > build/ext/overflow_probe.c <<'SRC'
#include <stdlib.h>
#include <stdio.h>
int main(int argc, char **argv) {
  int offset = (argc > 1) ? atoi(argv[1]) : 40;
  char *p = (char *)malloc(16);
  p[0] = 'a';
  p[offset] = 'x';           /* out of bounds by `offset` bytes */
  printf("no report (wrote at +%d)\n", offset);
  free(p);
  return 0;
}
SRC
clang-14 -O0 -g -fsanitize=address -fno-omit-frame-pointer \
  -o "$PROBE" build/ext/overflow_probe.c || exit 1

DETECT=results/ext/detection.md
{
  echo "# Heap-overflow detection vs. redzone size\n"
  echo "Write at a fixed offset past a 16-byte allocation, under the same"
  echo "\`ASAN_OPTIONS\` as the cost measurement, with ASLR disabled.\n"
  echo "| max_redzone | offset +40 | offset +100 | offset +200 |"
  echo "|---|---|---|---|"
  for rz in $REDZONES; do
    row="| $rz "
    for off in 40 100 200; do
      out=$(ASAN_OPTIONS="$BASE_OPTS:max_redzone=$rz" \
            $aslr "$PROBE" "$off" 2>&1)
      if echo "$out" | grep -q 'ERROR: AddressSanitizer'; then
        row="$row | **detected**"
      else
        row="$row | missed"
      fi
    done
    echo "$row |"
  done
  echo ""
  echo "A short redzone finds fewer of these writes: the overflow has to land"
  echo "inside the poisoned region to be caught (paper Sec. 3.5)."
} > "$DETECT"

echo "wrote $DETECT" >&2
cat "$DETECT" >&2
