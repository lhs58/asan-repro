/* b5_string - whitespace-delimited token scanning over a synthetic text buffer.
 *
 * Proxies for text processing (400.perlbench, 483.xalancbmk), described in the
 * paper as "very malloc-intensive and make a huge number of 1- and 2-byte
 * memory accesses". The inner loop does a compare against a byte literal for
 * every byte, which is the worst case for shadow-check instrumentation.
 *
 * usage: b5_string <mode> [bytes] [passes]
 */
#include "common.h"

int main(int argc, char **argv) {
  const char *mode = arg_mode(argc, argv);
  size_t n = (argc > 2) ? (size_t)atol(argv[2]) : ((size_t)4 << 20);
  long passes = (argc > 3) ? atol(argv[3]) : 40L;
  if (n < 16) n = 16;

  unsigned char *buf = (unsigned char *)malloc(n);
  if (!buf) {
    fprintf(stderr, "b5_string: out of memory\n");
    return 2;
  }

  /* build "words" of 3..11 letters separated by spaces or newlines */
  uint32_t s = 12345u;
  size_t i = 0;
  while (i < n) {
    long len = 3 + (long)(s % 9u);
    for (long k = 0; k < len && i < n; k++) {
      s = s * 1103515245u + 12345u;
      buf[i++] = (unsigned char)('a' + (s >> 16) % 26u);
    }
    if (i < n) {
      s = s * 1103515245u + 12345u;
      buf[i++] = ((s >> 8) & 1u) ? ' ' : '\n';
    }
  }

  uint64_t chk = 0;
  double t0 = now_sec();

  for (long p = 0; p < passes; p++) {
    size_t words = 0, chars = 0;
    int in_word = 0;
    for (size_t j = 0; j < n; j++) {
      unsigned char ch = buf[j];
      if (ch == ' ' || ch == '\n') {
        in_word = 0;
      } else {
        chars++;
        if (!in_word) {
          in_word = 1;
          words++;
        }
      }
    }
    chk += (uint64_t)words * 31u + chars;
  }

  double t1 = now_sec();
  emit("b5_string", mode, t1 - t0, chk);
  free(buf);
  return 0;
}
