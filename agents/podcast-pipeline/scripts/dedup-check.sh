#!/bin/bash
# dedup-check.sh — Precise duplication checking for the podcast pipeline.
#
# Usage:
#   dedup-check.sh --list        (Prints all published topic slugs)
#   dedup-check.sh --score <str> (Returns novelty score 0-10)

LECTURE_DIR="/home/nicolas/Documents/Podcast/Interesting/Episodes"

if [[ "${1:-}" == "--list" ]]; then
    ls -1 "$LECTURE_DIR" | grep -v ".jsonl" | sed 's/\///'
    exit 0
fi

if [[ "${1:-}" == "--score" ]]; then
    QUERY="${2:-}"
    # Score 0 (Duplicate) to 10 (Novel)
    # We grep the query terms against the dir names first (fast)
    match_count=0
    for word in $QUERY; do
        if [[ ${#word} -gt 3 ]]; then
            if ls "$LECTURE_DIR" | grep -qi "$word"; then
                match_count=$((match_count + 1))
            fi
        fi
    done
    
    # Calculate score
    if [[ $match_count -eq 0 ]]; then
        echo "score: 10"
    elif [[ $match_count -eq 1 ]]; then
        echo "score: 7"
    elif [[ $match_count -eq 2 ]]; then
        echo "score: 4"
    else
        echo "score: 0"
    fi
    exit 0
fi

# Default: Human readable report
echo "=== Published Episodes ==="
ls -1 "$LECTURE_DIR" | grep -v ".jsonl"
