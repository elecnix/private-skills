#!/bin/bash
# dedup-check.sh — Scan all published episodes (filesystem + Craft) and report
# what topics/sources/angles have already been covered. Use BEFORE planning
# new episodes to ensure novelty.
#
# Usage:
#   dedup-check.sh [topic_keyword_or_url]
#   With args: checks if proposed topic overlaps with existing
#   Without args: prints full episode ledger

set -euo pipefail

LECTURE_DIR="$HOME/Documents/Lecture/That's Interesting Stuff"
CRAFT_MCP="https://mcp.craft.do/links/13ps5w3NPCu/mcp"

# ─── Color output ───
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

# ─── Phase 1: Local filesystem scan ───
echo -e "${CYAN}=== Published Episodes (Local) ===${NC}"
echo ""

declare -a ALL_TOPICS=()
declare -a ALL_SOURCES=()
declare -a ALL_ANGLES=()

if [ -d "$LECTURE_DIR" ]; then
  for topic_dir in "$LECTURE_DIR"/*/; do
    [ -d "$topic_dir" ] || continue
    topic_name=$(basename "$topic_dir")
    [[ "$topic_name" == "youtube-logs.jsonl" ]] && continue
    ALL_TOPICS+=("$topic_name")

    echo -e "${GREEN}📂 $topic_name${NC}"

    if [ -f "$topic_dir/00-briefing.md" ]; then
      # Extract sources from briefing
      grep -i "http" "$topic_dir/00-briefing.md" 2>/dev/null | sed 's/^[ \t-]*//' | while read -r line; do
        echo -e "  Source: $line"
      done
    fi

    # Scan for key sub-topics in research notes and scripts
    if [ -f "$topic_dir/03-podcast-script.md" ]; then
      # Extract key terms: proper nouns, technical concepts
      grep -ioE '[A-Z][a-zA-Z]+ [A-Z][a-zA-Z]+' "$topic_dir/03-podcast-script.md" 2>/dev/null | \
        sort -u | head -20 | while read -r term; do
          echo -e "  Topic: $term"
        done
    fi
    echo ""
  done
fi

# ─── Phase 2: YouTube logs scan (if exists) ───
YOUTUBE_LOG="$LECTURE_DIR/youtube-logs.jsonl"
if [ -f "$YOUTUBE_LOG" ]; then
  echo -e "${CYAN}=== Published on YouTube ===${NC}"
  cat "$YOUTUBE_LOG" | python3 -c "
import json, sys
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    try:
        d = json.loads(line)
        title = d.get('title', d.get('videoId', '?'))
        video_id = d.get('videoId', d.get('id', ''))
        date = d.get('date', d.get('publishedAt', d.get('scheduledAt', '')))
        print(f'  {date} | {title} | https://youtu.be/{video_id}')
    except:
        continue
" 2>/dev/null || echo "  (Could not parse logs)"
  echo ""
fi

# ─── Phase 3: Craft Episodes scan ───
echo -e "${CYAN}=== Craft Episodes (via Craft MCP) ===${NC}"
# Fetch all docs in the Lecture folder and look for episode-like names
craft documents-list --folder-ids bae9e298-2b97-71c6-a069-0dcaf15d3388 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for doc in data.get('documents', []):
        title = doc.get('title', '')
        if any(k in title.lower() for k in ['episode', 'never sleep', 'interesting', 'autonomous', 'agent', 'template']):
            print(f'  📄 {title} (id: {doc[\"id\"]})')
except:
    print('  (Could not fetch Craft docs)')
" 2>/dev/null
echo ""

# ─── Phase 4: Topic overlap check (if keyword provided) ───
if [ $# -gt 0 ]; then
  QUERY="$*"
  echo -e "${CYAN}=== Checking overlap with: \"$QUERY\" ===${NC}"
  echo ""

  overlap_found=false
  OVERLAP_SUMMARY=""

  if [ -d "$LECTURE_DIR" ]; then
    for topic_dir in "$LECTURE_DIR"/*/; do
      [ -f "$topic_dir/03-podcast-script.md" ] || continue
      topic_name=$(basename "$topic_dir")

      # Case-insensitive grep of query keywords in existing scripts
      MATCHES=""
      for keyword in $QUERY; do
        found=$(grep -cil "$keyword" "$topic_dir/03-podcast-script.md" 2>/dev/null || true)
        if [ "$found" -gt 0 ]; then
          MATCHES="$MATCHES \"$keyword\""
        fi
      done
      if [ -n "$MATCHES" ]; then
        overlap_found=true
        echo -e "${YELLOW}⚠️  Overlap found in: $topic_name${NC}"
        echo -e "   Matched keywords: $MATCHES"
        # Show the section headers where overlap occurs
        grep -in "$QUERY" "$topic_dir/03-podcast-script.md" 2>/dev/null | head -5 | sed 's/^/     /'
        echo ""
      fi
    done
  fi

  if [ "$overlap_found" = false ]; then
    echo -e "${GREEN}✅ No significant overlap detected. Topic appears novel.${NC}"
  fi
fi

# ─── Phase 5: Unique source URL inventory ───
echo -e "${CYAN}=== All unique source URLs across episodes ===${NC}"
echo ""
if [ -d "$LECTURE_DIR" ]; then
  grep -rhi "http" "$LECTURE_DIR"/*/00-briefing.md "$LECTURE_DIR"/*/01-research-notes.md 2>/dev/null | \
    grep -oE 'https?://[^ ]+' | sort -u | nl
fi
echo ""
echo -e "${CYAN}=== Episode count ===${NC}"
echo "Local topic folders: $(ls -d "$LECTURE_DIR"/*/ 2>/dev/null | wc -l)"
echo "YouTube uploads logged: $(wc -l < "$YOUTUBE_LOG" 2>/dev/null || echo 0)"
