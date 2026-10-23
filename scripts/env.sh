#!/usr/bin/env bash
# Emit the environment record the report's setup section requires:
# hardware, OS, kernel, compiler and tool versions.
#   make env            -> docs/environment.md
set -u

echo "# Environment record"
echo
echo "Generated: $(date -Iseconds 2>/dev/null || date)"
echo

echo "## Operating system"
echo '```'
if [ -r /etc/os-release ]; then
  sed -n '1,6p' /etc/os-release
else
  uname -s
fi
echo '```'
echo

echo "## Kernel"
echo '```'
uname -a
echo '```'
echo

echo "## CPU and memory"
echo '```'
if command -v lscpu >/dev/null 2>&1; then
  lscpu | sed -n '1,14p'
else
  echo "logical CPUs: $(nproc 2>/dev/null || echo unknown)"
fi
if [ -r /proc/meminfo ]; then
  sed -n '1p' /proc/meminfo
fi
echo '```'
echo

echo "## Toolchain"
echo '```'
found=0
for c in clang-14 clang-15 clang-18 clang gcc cc make lld ld; do
  if command -v "$c" >/dev/null 2>&1; then
    printf '%-10s ' "$c"
    "$c" --version 2>/dev/null | head -n 1
    found=1
  fi
done
[ "$found" -eq 1 ] || echo "no compiler found on PATH"
if command -v valgrind >/dev/null 2>&1; then
  printf '%-10s ' valgrind
  valgrind --version 2>/dev/null
fi
if command -v python3 >/dev/null 2>&1; then
  printf '%-10s ' python3
  python3 --version 2>&1
fi
echo '```'
echo

echo "## Container runtime"
echo '```'
if command -v docker >/dev/null 2>&1; then
  docker --version 2>/dev/null || echo "docker present but not reachable"
else
  echo "no docker on PATH (running outside the container?)"
fi
echo '```'
echo

echo "## Notes"
echo
echo "- Anything that affects timings belongs here: CPU governor, turbo/boost,"
echo "  whether other containers were running, whether the host is a laptop on"
echo "  battery, and the container's CPU quota."
echo "- Record the wall-clock time of each measurement session in"
echo "  \`results/raw/<timestamp>-<host>.csv\` (the filename carries it)."
