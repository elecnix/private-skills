#!/bin/bash
# research-topic.sh — Fetch articles and sources for a research topic
# Usage: research-topic.sh <topic_folder> <url1> [url2] [url3] ...
#
# Each URL is fetched via Jina Reader and saved to sources/NN-name.md
# If only a topic name (no URLs), it searches brave_search and fetches top results.

set -euo pipefail

TOPICDIR="${1:?Usage: research-topic.sh <topic_folder> <url1> [url2] ...}"
shift

# Create topic folder structure
mkdir -p "$TOPICDIR"/{sources,audio,output,visuals}

if [ $# -eq 0 ]; then
    echo "Warning: No URLs provided. Run with at least one URL to research."
    echo "Example: research-topic.sh ~/Documents/Lecture/That's\ Interesting\ Stuff/2026-04-04_topic/ https://example.com/article"
    exit 1
fi

echo "=== Research Topic: $TOPICDIR ==="

counter=0
success=0
for url in "$@"; do
    counter=$((counter + 1))
    # Create a short name from the URL
    name=$(echo "$url" | sed 's|https\?://||; s|www\.||; s|/|_|g; s|[^a-zA-Z0-9_-]||g' | cut -c1-40)
    outfile="$TOPICDIR/sources/$(printf '%02d' $counter)-$name.md"

    echo "  Fetching [$counter]: $name..."
    curl -sL "https://r.jina.ai/$url" > "$outfile" 2>/dev/null

    words=$(wc -w < "$outfile")
    if [ "$words" -gt 20 ]; then
        success=$((success + 1))
        echo "    -> $words words written to $(basename "$outfile")"
    else
        echo "    -> WARNING: Only $words words fetched, source may have paywall or bot protection"
    fi
done

echo ""
echo "Research complete: $success/$counter sources fetched"
echo "Saved to: $TOPICDIR/sources/"
