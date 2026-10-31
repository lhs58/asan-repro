# ASan reproduction harness
#
#   make build       build 5 benchmarks x 3 modes into build/{base,asan,asanw}/
#   make run         1 warm-up + RUNS measured repetitions -> results/raw/*.csv
#   make summarize   aggregate raw CSV -> results/summary.md
#   make env         record toolchain/OS/CPU -> docs/environment.md
#   make all         build + run + summarize
#   make clean

# `CC ?= clang-14` would NOT work: GNU make defines CC as a built-in default
# (origin "default"), and `?=` only assigns when the variable is undefined. So a
# bare `make build` would silently use gcc, and the clang-only -mllvm flag in the
# asanw build would fail. Override only the built-in default.
ifeq ($(origin CC),default)
CC          := clang-14
endif
OPT         ?= -O2
BASE_FLAGS  ?= $(OPT) -g -Wall -Wextra -Wno-unused-parameter
LDLIBS      ?= -lm

BENCHES := b1_allocs b2_pointer b3_int b4_float b5_string
BUILD   := build

# Runtime settings approximating the paper's evaluation configuration (Sec. 4):
#   no stack unwinding on malloc/free -> malloc_context_size=0
#   quarantine disabled               -> quarantine_size_mb=0
#   small redzones, as in 2012        -> max_redzone=32
#   LeakSanitizer off: it did not exist in 2012 and adds exit-time work
ASAN_OPTS ?= malloc_context_size=0:quarantine_size_mb=0:detect_leaks=0:max_redzone=32
RUNS      ?= 3

ASAN_FLAGS  := -fsanitize=address -fno-omit-frame-pointer -g
ASANW_FLAGS := $(ASAN_FLAGS) -mllvm -asan-instrument-reads=0

.PHONY: all build run summarize env clean shell doctor

all: build run summarize

build:
	@mkdir -p $(BUILD)/base $(BUILD)/asan $(BUILD)/asanw
	@for b in $(BENCHES); do \
	  echo "  CC  base/$$b";  $(CC) $(BASE_FLAGS) -o $(BUILD)/base/$$b  bench/$$b.c $(LDLIBS) || exit 1; \
	  echo "  CC  asan/$$b";  $(CC) $(BASE_FLAGS) $(ASAN_FLAGS)  -o $(BUILD)/asan/$$b  bench/$$b.c $(LDLIBS) || exit 1; \
	  echo "  CC  asanw/$$b"; $(CC) $(BASE_FLAGS) $(ASANW_FLAGS) -o $(BUILD)/asanw/$$b bench/$$b.c $(LDLIBS) || exit 1; \
	done
	@echo "built into $(BUILD)/"

run: build
	@ASAN_OPTIONS="$(ASAN_OPTS)" RUNS=$(RUNS) bash scripts/run.sh

summarize:
	@python3 scripts/summarize.py

env:
	@bash scripts/env.sh > docs/environment.md
	@echo "wrote docs/environment.md"

# One-shot sanity check: a deliberately buggy program must be caught by the asan build.
doctor: build
	@ASAN_OPTIONS="$(ASAN_OPTS)" bash scripts/sanity_bug_check.sh

clean:
	@rm -rf $(BUILD)

shell:
	docker run --rm -it -v "$(CURDIR)":/work asan-repro bash
