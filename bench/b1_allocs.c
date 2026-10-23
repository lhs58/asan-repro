/* b1_allocs - heap churn.
 *
 * Stands in for the malloc-intensive SPEC CPU2006 benchmarks that dominate the
 * paper's Figure 2: 400.perlbench (2.60x) and 483.xalancbmk (2.67x). Both are
 * described as "very malloc-intensive and make a huge number of 1- and 2-byte
 * memory accesses".
 *
 * The pattern: a live set of small objects is repeatedly freed and reallocated,
 * with sizes spread over 16..160 bytes so the allocator hits several size
 * classes instead of one.
 *
 * usage: b1_allocs <mode> [iterations] [live_objects]
 */
#include "common.h"

int main(int argc, char **argv) {
  const char *mode = arg_mode(argc, argv);
  long iters = (argc > 2) ? atol(argv[2]) : 8000000L;
  long live = (argc > 3) ? atol(argv[3]) : 4000L;
  if (live < 1) live = 1;

  unsigned char **slot = calloc((size_t)live, sizeof(*slot));
  if (!slot) {
    fprintf(stderr, "b1_allocs: out of memory\n");
    return 2;
  }

  uint64_t chk = 0;
  double t0 = now_sec();

  for (long i = 0; i < iters; i++) {
    long k = i % live;
    if (slot[k]) {
      /* touch before free so the region is resident */
      chk += slot[k][0] + (uint64_t)slot[k][3];
      free(slot[k]);
    }
    size_t sz = 16u + (size_t)(i % 7L) * 24u; /* 16, 40, 64, ... 160 bytes */
    slot[k] = (unsigned char *)malloc(sz);
    if (!slot[k]) {
      fprintf(stderr, "b1_allocs: malloc failed at %ld\n", i);
      return 3;
    }
    memset(slot[k], (int)(i & 0xff), sz);
  }

  for (long k = 0; k < live; k++) free(slot[k]);

  double t1 = now_sec();
  emit("b1_allocs", mode, t1 - t0, chk);
  free(slot);
  return 0;
}
