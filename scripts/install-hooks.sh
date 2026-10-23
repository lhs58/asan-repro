#!/usr/bin/env bash
# Install the commit-msg hook that enforces the CS340 rule:
#   every commit message must contain "Member: <student ID> <full name>"
#
#   bash scripts/install-hooks.sh
#
# Every group member must run this in their own clone. The hook lives in
# .git/hooks/ and is therefore NOT committed; the template .gitmessage is.
set -euo pipefail

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "not inside a git repository" >&2
  exit 1
fi

hookdir="$(git rev-parse --git-dir)/hooks"
mkdir -p "$hookdir"

cat > "$hookdir/commit-msg" <<'HOOK'
#!/bin/sh
# CS340 rule: every commit message must carry the committer's student ID and
# full name, e.g.  "Member: 1220012345 Zhang San".
if ! grep -Eq '^Member:[[:space:]]*[0-9]{6,}[[:space:]]+[^[:space:]]' "$1"; then
  echo "" >&2
  echo "commit-msg: missing required line in the commit message:" >&2
  echo "" >&2
  echo "    Member: <student ID> <full name>" >&2
  echo "" >&2
  echo "Example message:" >&2
  echo "    bench: add heap-churn benchmark" >&2
  echo "" >&2
  echo "    Why: proxy for the malloc-intensive CPU2006 cases" >&2
  echo "    Ref: Figure 2" >&2
  echo "" >&2
  echo "    Member: 1220012345 Zhang San" >&2
  echo "" >&2
  exit 1
fi
HOOK

chmod +x "$hookdir/commit-msg" 2>/dev/null || true
echo "installed $hookdir/commit-msg"

# Also point git at the shared message template, if not already set.
if [ -f .gitmessage ]; then
  git config --local commit.template .gitmessage
  echo "set commit.template -> .gitmessage"
fi

# Remind about identity, the most common cause of mis-attributed commits.
echo ""
echo "Your local identity (must be YOUR OWN account):"
git config user.name || echo "  user.name  : NOT SET"
git config user.email || echo "  user.email : NOT SET"
