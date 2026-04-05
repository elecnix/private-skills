#!/bin/bash
# ticktick-reconcile.sh — Process pending writeahead entries against the TickTick API
# Moves confirmed entries from writeahead → commit, leaves failures in writeahead
#
# Usage: ticktick-reconcile.sh [--dry-run]

set -euo pipefail

LEDGER_DIR="$HOME/Source/private-skills/lecture-pipeline"
WA="$LEDGER_DIR/ticktick-writeahead.jsonl"
COMMIT="$LEDGER_DIR/ticktick-commit.jsonl"
FAILED="$LEDGER_DIR/ticktick-failed-reconcile.jsonl"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
  echo "=== DRY RUN — no changes will be made ==="
fi

if [ ! -s "$WA" ]; then
  echo "✅ No pending writeahead entries."
  exit 0
fi

echo "=== TickTick Reconcile ==="
echo "Pending: $(wc -l < "$WA") entries"
echo ""

> "$COMMIT.tmp"
> "$FAILED.tmp"
reconciled=0
failed=0

while IFS= read -r line; do
  task_id=$(echo "$line" | python3 -c "import json,sys; print(json.load(sys.stdin)['task_id'])" 2>&1)
  title=$(echo "$line" | python3 -c "import json,sys; print(json.load(sys.stdin)['title'])" 2>&1)

  if [ "$DRY_RUN" = true ]; then
    echo "  [DRY RUN] Would complete: $task_id — $title"
    ((reconciled++)) || true
    echo "$line" >> "$COMMIT.tmp"
    continue
  fi

  if tickrs task complete "$task_id" --quiet 2>&1; then
    echo "  ✅ $task_id — $title"
    ((reconciled++)) || true
    # Add reconciled timestamp
    echo "$line" | python3 -c "
import json, sys, datetime
d = json.load(sys.stdin)
d['reconciled_at'] = datetime.datetime.now().astimezone().isoformat()
d.pop('attempt_result', None)
print(json.dumps(d))
" >> "$COMMIT.tmp"
  else
    echo "  ❌ $task_id — $title (will retry next time)"
    ((failed++)) || true
    # Update attempt count
    echo "$line" | python3 -c "
import json, sys, datetime
d = json.load(sys.stdin)
d['retry_count'] = d.get('retry_count', 0) + 1
d['retry_at'] = datetime.datetime.now().astimezone().isoformat()
d['attempt_result'] = f'Reconcile attempt {d[\"retry_count\"]} failed'
print(json.dumps(d))
" >> "$FAILED.tmp"
  fi
done < "$WA"

if [ "$DRY_RUN" = false ]; then
  # Swap files atomically
  mv "$COMMIT.tmp" "$COMMIT"
  mv "$FAILED.tmp" "$WA"
  
  echo ""
  echo "=== Results ==="
  echo "  Reconciled: $reconciled (moved to ticktick-commit.jsonl)"
  echo "  Failed:     $failed (remaining in ticktick-writeahead.jsonl)"
  
  if [ -s "$WA" ]; then
    echo ""
    echo "⚠️  $failed entries still pending — run again later"
  else
    echo ""
    echo "✅ All entries reconciled!"
  fi
else
  echo ""
  echo "=== Dry Run Summary ==="
  echo "  Would reconcile: $reconciled entries"
fi
