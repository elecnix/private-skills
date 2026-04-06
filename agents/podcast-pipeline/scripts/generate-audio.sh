#!/bin/bash
# generate-audio.sh — Convert script to audio + subtitles using edge-tts
# Usage: generate-audio.sh <topic_folder> [--voice VOICE] [--rate RATE%] [--pitch HZ]
#
# Pipeline: Synthesizer → script-processor (tts-normalize.py) → generate-audio.sh (edge-tts)
# Default: uses audio/podcast-ready.txt if normalized file exists; falls back to stripping
# 03-podcast-script.md inline (degraded experience).

set -euo pipefail

TOPICDIR="${1:?Usage: generate-audio.sh <topic_folder> [options]}"
shift

VOICE="en-US-AndrewNeural"
RATE="-12%"
PITCH="-3Hz"
VOLUME="-1%"

# Parse optional flags
while [[ $# -gt 0 ]]; do
    case $1 in
        --voice) VOICE="$2"; shift 2 ;;
        --rate) RATE="$2"; shift 2 ;;
        --pitch) PITCH="$2"; shift 2 ;;
        --volume) VOLUME="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; shift ;;
    esac
done

mkdir -p "$TOPICDIR/audio"

echo "=== Generating Audio ==="
echo "  Voice: $VOICE (rate=$RATE, pitch=$PITCH, volume=$VOLUME)"

# Prefer the normalized file from tts-normalize.py (produced by lecture-script-processor)
NORMALIZED="$TOPICDIR/audio/podcast-ready.txt"
if [ -f "$NORMALIZED" ]; then
    echo "  Using normalized script (tts-normalize.py)"
    INPUT_FILE="$NORMALIZED"
else
    SCRIPT="$TOPICDIR/03-podcast-script.md"
    if [ ! -f "$SCRIPT" ]; then
        echo "  ERROR: No script found. Need audio/podcast-ready.txt or 03-podcast-script.md"
        exit 1
    fi
    echo "  WARNING: No normalized file — stripping markdown inline (degraded)"
    # Strip markdown: skip h1/h2 headers and [section] tags, flatten to prose
    sed -e 's/^#.*//' -e '/^\[.*\]$/d' -e '/^---/d' "$SCRIPT" | \
        sed 's/[*_'"'"'~`]//g' | \
        sed 's/  */ /g' | tr '\n' ' ' | \
        sed 's/^ //; s/ $//' > /tmp/_lecture_script_clean.txt
    INPUT_FILE=/tmp/_lecture_script_clean.txt
fi

word_count=$(wc -w < "$INPUT_FILE")
echo "  Script: $word_count words"

if [ "$word_count" -lt 100 ]; then
    echo "  ERROR: Script too short ($word_count words). Normalization may have failed."
    exit 1
fi

echo "  Generating..."
edge-tts -f "$INPUT_FILE" \
    -v "$VOICE" \
    --rate="$RATE" \
    --pitch="$PITCH" \
    --volume="$VOLUME" \
    --write-media "$TOPICDIR/audio/podcast.mp3" \
    --write-subtitles "$TOPICDIR/audio/podcast.srt" 2>&1

# ─── Post-processing ───
if [ ! -f "$TOPICDIR/audio/podcast.mp3" ]; then
    echo "  ERROR: Audio generation failed"
    exit 1
fi

# Prepend 1 second of silence so players don't clip the first word
SILENCE="$TOPICDIR/audio/_silence.mp3"
if [ ! -f "$SILENCE" ]; then
    ffmpeg -y -f lavfi -i "aevalsrc=0::s=24000:d=1" \
        -c:a libmp3lame -b:a 192k "$SILENCE" 2>/dev/null
fi

ORIG="$TOPICDIR/audio/_orig-podcast.mp3"
mv "$TOPICDIR/audio/podcast.mp3" "$ORIG"
ffmpeg -y -i "$SILENCE" -i "$ORIG" \
    -filter_complex "[0:a][1:a]concat=n=2:v=0:a=1" \
    -c:a libmp3lame -b:a 192k "$TOPICDIR/audio/podcast.mp3" 2>/dev/null
rm -f "$ORIG"

# Shift SRT timestamps forward by 1 second to match the silence
python3 /home/nicolas/Source/private-skills/agents/podcast-pipeline/scripts/shift-srt.py \
    "$TOPICDIR/audio/podcast.srt" 1.0

# Final report
size=$(du -h "$TOPICDIR/audio/podcast.mp3" | cut -f1)
duration=$(ffprobe -v quiet -show_entries format=duration \
    -of default=noprint_wrappers=1:nokey=1 "$TOPICDIR/audio/podcast.mp3")
mins=$(echo "$duration" | awk '{printf "%d:%02d", $1/60, $1%60}')
srt_entries=$(grep -c ' --> ' "$TOPICDIR/audio/podcast.srt")

echo ""
echo "  Audio: $size, duration $mins (includes 1s leading silence)"
echo "  SRT: $srt_entries subtitle entries (shifted +1s)"
