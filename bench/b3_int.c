/* b3_int - byte-at-a-time hashing over a large buffer.
 *
 * Exercises 1-byte loads, the access pattern the paper says is most expensive:
 * every access needs its own shadow check, so the ratio of instrumentation to
 * useful work is as bad as it gets. Proxies for 401.bzip2 territory.
 *
 * usage: b3_int <mode> [bytes] [passes]
 */
#include "common.h"

int main(int argc, char **argv) {
  const char *mode = arg_mode(argc, argv);
  size_t n = (argc > 2) ? (size_t)atol(argv[2]) : ((size_t)1 << 20);
  long passes = (argc > 3) ? atol(argv[3]) : 500L;
  if (n == 0) n = 1;

  unsigned char *buf = (unsigned char *)malloc(n);
  if (!buf) {
    fprintf(stderr, "b3_int: out of memory\n");
    return 2;
  }

  /* deterministic fill, no rand() so runs are reproducible */
  uint32_t s = 2166136261u;
  for (size_t i = 0; i < n; i++) {
    s = s * 1664525u + 1013904223u;
    buf[i] = (unsigned char)(s >> 24);
  }

  uint64_t chk = 0;
  double t0 = now_sec();

  for (long p = 0; p < passes; p++) {
    uint32_t h = 2166136261u; /* FNV-1a */
    for (size_t i = 0; i < n; i++) {
      h ^= buf[i];
      h *= 16777619u;
    }
    chk += h;
  }

  double t1 = now_sec();
  emit("b3_int", mode, t1 - t0, chk);
  free(buf);
  return 0;
}
