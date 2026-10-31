#!/usr/bin/env bash
# Correctness counterpart to the performance measurement.
#
# The paper claims ASan detects out-of-bounds accesses to heap, stack and global
# objects plus use-after-free, with no false positives (Sec. 3.5-3.6). The
# `base` build must run these programs silently; the `asan` build must report
# each one. Run with:
#
#   make doctor
#
# Note: ASAN_OPTIONS is deliberately reset here. The performance configuration
# (quarantine_size_mb=0) weakens use-after-free detection, which is the whole
# point of this check.
set -uo pipefail

export ASAN_OPTIONS=detect_leaks=0
CC="${CC:-clang-14}"

# See scripts/run.sh: without ADDR_NO_RANDOMIZE, roughly a quarter of ASan runs
# on this WSL2 kernel die with SIGSEGV before printing a report, which would
# masquerade as "the bug was not detected".
aslr=""
if command -v setarch >/dev/null 2>&1; then
  aslr="setarch $(uname -m) -R"
fi
OUT=build/bugs
mkdir -p "$OUT"
fail=0

run_case() {
  name="$1"
  cat > "$OUT/$name.c"

  if ! "$CC" -O0 -g -fsanitize=address -fno-omit-frame-pointer \
        -o "$OUT/$name" "$OUT/$name.c" 2>"$OUT/$name.build.log"; then
    printf '  BUILD FAIL  %-22s\n' "$name"
    fail=1
    return
  fi

  $aslr "$OUT/$name" > "$OUT/$name.log" 2>&1
  rc=$?
  kind=$(grep -o 'ERROR: AddressSanitizer: [a-z-]*' "$OUT/$name.log" | head -n 1)

  if [ "$rc" -ne 0 ] && [ -n "$kind" ]; then
    printf '  detected    %-22s %s\n' "$name" "$kind"
  else
    printf '  MISSED      %-22s (exit=%d)\n' "$name" "$rc"
    fail=1
  fi
}

echo "checking bug classes from the paper's claims:"

run_case heap_overflow <<'SRC'
#include <stdlib.h>
#include <string.h>
int main(void) {
  char *p = (char *)malloc(10);
  memset(p, 'a', 10);
  p[10] = 'x';            /* one past the end */
  free(p);
  return 0;
}
SRC

run_case stack_overflow <<'SRC'
int main(void) {
  volatile char a[10];
  a[12] = 'x';            /* past the end of a stack object */
  return (int)a[0];
}
SRC

run_case global_overflow <<'SRC'
char g[8];
int main(void) {
  g[8] = 'x';             /* past the end of a global */
  return (int)g[0];
}
SRC

run_case use_after_free <<'SRC'
#include <stdlib.h>
int main(void) {
  char *p = (char *)malloc(16);
  free(p);
  p[0] = 'x';             /* write to freed memory */
  return 0;
}
SRC

# Control: a correct program must NOT be reported (the "no false positives"
# half of the claim). This one is a smoke test, not a proof.
cat > "$OUT/clean_control.c" <<'SRC'
#include <stdlib.h>
#include <string.h>
int main(void) {
  char *p = (char *)malloc(32);
  memset(p, 'a', 32);
  p[31] = 'z';
  free(p);
  return 0;
}
SRC
if "$CC" -O2 -g -fsanitize=address -fno-omit-frame-pointer \
      -o "$OUT/clean_control" "$OUT/clean_control.c" 2>/dev/null; then
  $aslr "$OUT/clean_control" > "$OUT/clean_control.log" 2>&1
  if [ $? -eq 0 ]; then
    printf '  clean       %-22s no report (as expected)\n' clean_control
  else
    printf '  FALSE POS   %-22s unexpected report\n' clean_control
    fail=1
  fi
else
  printf '  BUILD FAIL  %-22s\n' clean_control
  fail=1
fi

echo ""
if [ "$fail" -eq 0 ]; then
  echo "all four bug classes detected, control program clean"
else
  echo "at least one check failed - inspect $OUT/*.log" >&2
fi
exit "$fail"
