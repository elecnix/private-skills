#!/bin/bash
# episode-proposal.sh — Helper script for lecture-episode-selector
# Manages tmp files for iterative proposal refinement

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE_DIR="$(dirname "$SCRIPT_DIR")"

# ─── Usage ───
usage() {
  cat << EOF
Usage: episode-proposal.sh <command> [args...]

Commands:
  init                      Create working directory
  add-candidate <json>      Add candidate idea from TickTick
  add-candidates <json>      Add multiple candidates (newline-delimited JSON)
  set-existing              Append existing episode ledger
  run-refine                Run proposal-refiner subagent
  present                   Print current proposal for user review
  apply-feedback <text>     Add user feedback and re-run refine
  get-proposal              Output proposal path
  cleanup                   Remove working directory

Examples:
  episode-proposal.sh init
  tickrs task list --project-id 639b3e518f08b7851bff5500 --status incomplete --json \
    | jq -c '.data[]' \
    | episode-proposal.sh add-candidates
  episode-proposal.sh run-refine
  episode-proposal.sh present
  episode-proposal.sh apply-feedback "Merge 1+2, drop 3"
  episode-proposal.sh cleanup

EOF
}

# ─── Init ───
do_init() {
  WORK_DIR=$(mktemp -d /tmp/episode-proposal-XXXXXX)
  echo "$WORK_DIR"
  
  # Create base files
  cat > "$WORK_DIR/candidates.md" << 'HEADER'
# Episode Candidates

HEADER

  cat > "$WORK_DIR/proposal.md" << 'HEADER'
# Episode Proposal

*Not yet generated — run 'episode-proposal.sh run-refine' after adding candidates*

HEADER

  touch "$WORK_DIR/feedback.md"
}

# ─── Add single candidate ───
do_add_candidate() {
  if [ -z "${WORK_DIR:-}" ]; then
    echo "Error: No working directory. Run 'init' first." >&2
    exit 1
  fi
  
  local json="$1"
  local task_id=$(echo "$json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null || echo "")
  local title=$(echo "$json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('title',''))" 2>/dev/null || echo "")
  local content=$(echo "$json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('content',''))" 2>/dev/null || echo "")
  local project_id=$(echo "$json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('projectId',''))" 2>/dev/null || echo "")
  local tags=$(echo "$json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(','.join(d.get('tags',[])))" 2>/dev/null || echo "")
  local priority=$(echo "$json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('priority',0))" 2>/dev/null || echo "0")
  
  # Extract URLs from content
  local urls=$(echo "$content" | grep -oE 'https?://[^ ]+' | tr '\n' ' ')
  
  cat >> "$WORK_DIR/candidates.md" << EOF

---

## Candidate: $task_id

**Title:** $title
**Project:** $project_id
**Tags:** $tags
**Priority:** $priority
**URLs:** $urls

### Content
$content

EOF
}

# ─── Add multiple candidates (newline-delimited JSON) ───
do_add_candidates() {
  if [ -z "${WORK_DIR:-}" ]; then
    echo "Error: No working directory. Run 'init' first." >&2
    exit 1
  fi
  
  local count=0
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    do_add_candidate "$line"
    count=$((count + 1))
  done
  
  echo "Added $count candidates"
}

# ─── Append existing episodes ───
do_set_existing() {
  if [ -z "${WORK_DIR:-}" ]; then
    echo "Error: No working directory. Run 'init' first." >&2
    exit 1
  fi
  
  cat >> "$WORK_DIR/candidates.md" << 'HEADER'

---

# Existing Episodes (for dedup reference)

HEADER

  if [ -f "$HOME/Documents/Lecture/episode-ledger.jsonl" ]; then
    cat "$HOME/Documents/Lecture/episode-ledger.jsonl" >> "$WORK_DIR/candidates.md"
  fi
  
  echo "Added existing episode ledger"
}

# ─── Run proposal-refiner subagent ───
do_run_refine() {
  if [ -z "${WORK_DIR:-}" ]; then
    echo "Error: No working directory. Run 'init' first." >&2
    exit 1
  fi
  
  # Count candidates
  local n_candidates=$(grep -c "^## Candidate:" "$WORK_DIR/candidates.md" 2>/dev/null || echo "0")
  local n_existing=$(grep -c "^20[0-9][0-9]-" "$WORK_DIR/candidates.md" 2>/dev/null || echo "0")
  
  echo "Refining $n_candidates candidates against $n_existing existing episodes..."
  
  # Run the subagent
  # Note: The parent agent handles the actual subagent call
  # This script just prepares the context
  
  # Update proposal header
  cat > "$WORK_DIR/proposal.md" << EOF
# Episode Proposal

*Generated: $(date -Iseconds)*
*Candidates: $n_candidates*
*Existing episodes: $n_existing*

*Run 'episode-proposal.sh run-refine' via the parent agent's subagent call...*

EOF
  
  echo "Prepared for refinement. Parent agent should call proposal-refiner subagent."
}

# ─── Present proposal ───
do_present() {
  if [ -z "${WORK_DIR:-}" ]; then
    echo "Error: No working directory. Run 'init' first." >&2
    exit 1
  fi
  
  if [ -f "$WORK_DIR/proposal.md" ]; then
    cat "$WORK_DIR/proposal.md"
  else
    echo "No proposal yet. Run 'run-refine' first."
  fi
}

# ─── Apply feedback ───
do_apply_feedback() {
  if [ -z "${WORK_DIR:-}" ]; then
    echo "Error: No working directory. Run 'init' first." >&2
    exit 1
  fi
  
  local feedback="$1"
  
  cat >> "$WORK_DIR/feedback.md" << EOF

---

## Feedback $(date -Iseconds)

$feedback

EOF
  
  echo "Feedback recorded. Run 'run-refine' to apply."
}

# ─── Get proposal path ───
do_get_proposal() {
  if [ -z "${WORK_DIR:-}" ]; then
    echo "Error: No working directory. Run 'init' first." >&2
    exit 1
  fi
  echo "$WORK_DIR/proposal.md"
}

# ─── Get candidates path ───
do_get_candidates() {
  if [ -z "${WORK_DIR:-}" ]; then
    echo "Error: No working directory. Run 'init' first." >&2
    exit 1
  fi
  echo "$WORK_DIR/candidates.md"
}

# ─── Get feedback path ───
do_get_feedback() {
  if [ -z "${WORK_DIR:-}" ]; then
    echo "Error: No working directory. Run 'init' first." >&2
    exit 1
  fi
  echo "$WORK_DIR/feedback.md"
}

# ─── Cleanup ───
do_cleanup() {
  if [ -n "${WORK_DIR:-}" ] && [ -d "$WORK_DIR" ]; then
    rm -rf "$WORK_DIR"
    echo "Cleaned up $WORK_DIR"
  fi
}

# ─── Main ───
COMMAND="${1:-}"
WORK_DIR="${EPISODE_PROPOSAL_DIR:-}"

case "$COMMAND" in
  init)
    do_init
    ;;
  add-candidate)
    do_add_candidate "$(cat /dev/stdin)"
    ;;
  add-candidates)
    do_add_candidates
    ;;
  set-existing)
    do_set_existing
    ;;
  run-refine)
    do_run_refine
    ;;
  present)
    do_present
    ;;
  apply-feedback)
    shift
    do_apply_feedback "$*"
    ;;
  get-proposal)
    do_get_proposal
    ;;
  get-candidates)
    do_get_candidates
    ;;
  get-feedback)
    do_get_feedback
    ;;
  cleanup)
    do_cleanup
    ;;
  help|--help|-h)
    usage
    ;;
  *)
    echo "Unknown command: $COMMAND"
    usage
    exit 1
    ;;
esac
