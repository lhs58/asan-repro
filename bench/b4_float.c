/* b4_float - double-precision array arithmetic.
 *
 * Proxies for the floating-point benchmarks in CPU2006 (450.soplex, 470.lbm)
 * which showed the *smallest* overhead: ASan instruments memory accesses, not
 * floating-point arithmetic, so an inner loop that stays in registers and
 * strides predictably pays almost nothing. Expect a small slowdown here; if you
 * see a large one, something in the build is wrong.
 *
 * usage: b4_float <mode> [width] [reps]
 */
#include "common.h"

#include <math.h>

int main(int argc, char **argv) {
  const char *mode = arg_mode(argc, argv);
  int n = (argc > 2) ? atoi(argv[2]) : 4096;
  long reps = (argc > 3) ? atol(argv[3]) : 20000L;
  if (n < 1) n = 1;

  double *a = (double *)malloc(sizeof(double) * (size_t)n);
  double *b = (double *)malloc(sizeof(double) * (size_t)n);
  double *c = (double *)malloc(sizeof(double) * (size_t)n);
  if (!a || !b || !c) {
    fprintf(stderr, "b4_float: out of memory\n");
    return 2;
  }
  for (int i = 0; i < n; i++) {
    a[i] = (double)i * 0.5;
    b[i] = 1.0 / (double)(i + 1);
    c[i] = 0.0;
  }

  double t0 = now_sec();
  for (long r = 0; r < reps; r++) {
    for (int i = 0; i < n; i++) {
      c[i] = a[i] * b[i] + c[i] * 0.5;
      if (c[i] > 1.0e9) c[i] = sqrt(c[i]);
    }
  }
  double acc = 0.0;
  for (int i = 0; i < n; i++) acc += c[i];
  double t1 = now_sec();

  emit("b4_float", mode, t1 - t0, (uint64_t)acc);
  free(a);
  free(b);
  free(c);
  return 0;
}
