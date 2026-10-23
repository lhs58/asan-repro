/* common.h - shared helpers for the benchmark harness.
 *
 * Every benchmark prints exactly ONE csv row to stdout:
 *
 *     <bench>,<mode>,<wall_seconds>,<VmPeak_kB>,<VmHWM_kB>,<VmSize_kB>,<checksum>
 *
 * All three memory fields come from /proc/self/status, the same source the
 * paper used for its memory-overhead table (Table 1).
 *
 * WHY THREE FIELDS AND NOT ONE
 * ----------------------------
 * The paper reports VmPeak and gets a 3.37x increase. Modern 64-bit ASan
 * reserves one eighth of the address space for shadow memory at startup. A
 * PROT_NONE reservation still counts toward VmSize/VmPeak, so an instrumented
 * binary can show a *terabyte-scale* VmPeak that has nothing to do with real
 * memory pressure. VmHWM (peak resident set) is not affected by the unused
 * reservation, because untouched shadow pages are never faulted in.
 *
 * Primary metric for the report should therefore be VmHWM; VmPeak is recorded
 * so the discrepancy with the paper can be shown and explained, not so it can
 * be silently compared to Table 1.
 *
 * The checksum lets us confirm that the baseline and instrumented builds
 * computed the same thing.
 */
#ifndef ASAN_REPRO_COMMON_H
#define ASAN_REPRO_COMMON_H

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static inline double now_sec(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

/* Parse "<key>   <number> kB" lines. `key` includes the colon, e.g. "VmPeak:".
 * strtol skips the whitespace between the colon and the number. */
static inline long parse_kb(const char *line, const char *key) {
  size_t klen = strlen(key);
  if (strncmp(line, key, klen) != 0) return -1;
  return strtol(line + klen, NULL, 10);
}

typedef struct {
  long vmpeak; /* kB, peak virtual size - polluted by the shadow reservation */
  long vmhwm;  /* kB, peak resident set - the honest memory metric */
  long vmsize; /* kB, current virtual size */
} meminfo_t;

static inline meminfo_t read_meminfo(void) {
  meminfo_t m = {-1, -1, -1};
  FILE *f = fopen("/proc/self/status", "r");
  if (!f) return m;

  char line[256];
  while (fgets(line, sizeof(line), f)) {
    if (m.vmpeak < 0 && strncmp(line, "VmPeak:", 7) == 0) {
      m.vmpeak = parse_kb(line, "VmPeak:");
    } else if (m.vmhwm < 0 && strncmp(line, "VmHWM:", 6) == 0) {
      m.vmhwm = parse_kb(line, "VmHWM:");
    } else if (m.vmsize < 0 && strncmp(line, "VmSize:", 7) == 0) {
      m.vmsize = parse_kb(line, "VmSize:");
    }
    if (m.vmpeak >= 0 && m.vmhwm >= 0 && m.vmsize >= 0) break;
  }
  fclose(f);
  return m;
}

static inline void emit(const char *bench, const char *mode, double secs,
                        uint64_t chk) {
  meminfo_t m = read_meminfo();
  printf("%s,%s,%.6f,%ld,%ld,%ld,%llu\n", bench, mode, secs, m.vmpeak, m.vmhwm,
         m.vmsize, (unsigned long long)chk);
  fflush(stdout);
}

/* argv[1] is the build-mode label, supplied by scripts/run.sh. */
static inline const char *arg_mode(int argc, char **argv) {
  return (argc > 1) ? argv[1] : "unknown";
}

#endif /* ASAN_REPRO_COMMON_H */
