/* b2_pointer - pointer chasing over a heap-allocated linked list.
 *
 * Proxies for the CPU2006 benchmarks whose cost is dominated by dependent loads
 * through memory (429.mcf, 473.astar). Instrumentation adds an extra dependent
 * load per access, so this pattern should expose overhead that pure arithmetic
 * does not.
 *
 * usage: b2_pointer <mode> [nodes] [passes]
 */
#include "common.h"

typedef struct Node {
  struct Node *next;
  long v;
  char pad[8];
} Node;

int main(int argc, char **argv) {
  const char *mode = arg_mode(argc, argv);
  long n = (argc > 2) ? atol(argv[2]) : 300000L;
  long passes = (argc > 3) ? atol(argv[3]) : 1000L;
  if (n < 1) n = 1;

  Node *head = NULL;
  for (long i = 0; i < n; i++) {
    Node *x = (Node *)malloc(sizeof(*x));
    if (!x) {
      fprintf(stderr, "b2_pointer: out of memory\n");
      return 2;
    }
    x->v = i;
    x->next = head;
    head = x;
  }

  uint64_t chk = 0;
  double t0 = now_sec();

  for (long p = 0; p < passes; p++) {
    long acc = 0;
    for (const Node *x = head; x; x = x->next) acc += x->v;
    chk += (uint64_t)acc;
  }

  double t1 = now_sec();
  emit("b2_pointer", mode, t1 - t0, chk);

  while (head) {
    Node *nx = head->next;
    free(head);
    head = nx;
  }
  return 0;
}
