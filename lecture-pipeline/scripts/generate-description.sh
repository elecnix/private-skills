#!/usr/bin/env bash
# generate-description.sh — Create a rich YouTube description from podcast pipeline artifacts.
#
# Usage: generate-description.sh <topic_dir> [source_url]
#
# Outputs:
#   output/youtube-description.txt  — Full description text
#   output/youtube-metadata.json    — Title, description, tags, source_url (machine-readable)
#
# Pipeline integration: run AFTER audio/visuals, BEFORE uploading to YouTube.
# The youtube-publisher agent should read output/youtube-metadata.json for:
#   - description text
#   - tags array
#   - source_url (for the final description + TickTick task update)

set -euo pipefail

TOPIC_DIR="${1:?Usage: generate-description.sh <topic_dir> [source_url]}"
SOURCE_URL="${2:-}"
SCRIPT="$TOPIC_DIR/03-podcast-script.md"
NOTES="$TOPIC_DIR/01-research-notes.md"
SRT="$TOPIC_DIR/sources/source.en.srt"
OUTDIR="$TOPIC_DIR/output"
mkdir -p "$OUTDIR"

python3 - "$TOPIC_DIR" "$SOURCE_URL" "$SCRIPT" "$NOTES" "$SRT" "$OUTDIR" << 'PYEOF'
import sys, os, re, json, textwrap

topic_dir   = sys.argv[1]
source_url  = sys.argv[2].strip() if len(sys.argv) > 2 and sys.argv[2].strip() else ""
script_path = sys.argv[3]
notes_path  = sys.argv[4]
srt_path    = sys.argv[5]
out_dir     = sys.argv[6]

# ── Read sources ──────────────────────────────────────────────────────────
with open(script_path) as f: script = f.read()
with open(notes_path)  as f: notes  = f.read()

# Parse transcript from SRT (for word count / duration)
word_count = 0
duration_secs = 0
if os.path.exists(srt_path):
    with open(srt_path) as f: srt = f.read()
    words = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> .*?\n', '', srt).split()
    word_count = len(words)
    # Extract last timestamp for duration
    ts = re.findall(r'(\d{2}):(\d{2}):(\d{2}),\d{3} -->', srt)
    if ts:
        h, m, s = map(int, ts[-1])
        duration_secs = h * 3600 + m * 60 + s

# Parse podcast sections (Hook + Sections 1-4 + Closing)
sections = re.split(r'\n## (.+)\n', script)
titles = sections[1::2]
bodies = sections[2::2]

# ── Build extended summary paragraphs from first 2-3 sections ─────────────
summary_raw = []
for body in bodies[:3]:
    paras = [p.strip() for p in body.strip().split('\n\n') if p.strip()]
    summary_raw.extend(paras[:2])

# Clean and cap summary
summary = []
for p in summary_raw:
    p = re.sub(r'\*', '', p)          # remove emphasis markers
    p = re.sub(r'\s+', ' ', p)        # normalize whitespace
    summary.append(p)

extended_summary = '\n\n'.join(summary[:3])

# ── Build table-of-contents from section titles ──────────────────────────
toc_items = []
for t in titles:
    # Clean the title: remove subtitle prefix like "Section 1: "
    clean = re.sub(r'^Section \d+:\s*', '', t).strip()
    if clean and clean not in ('Hook', 'Closing'):
        toc_items.append(f"• {clean}")

# ── Extract quotes from notes ─────────────────────────────────────────────
quotes = re.findall(r'^- "(.+)"$', notes, re.MULTILINE)
quote_refs = [f"\"{q}\"" for q in quotes[:3]]  # max 3

# ── Build references section ─────────────────────────────────────────────
ref_lines = []

# Source URL if provided
if source_url:
    ref_lines.append(f"📺 Source video: {source_url}")

# Known references from this video's topic (Linear article, tools mentioned)
known_refs = {
    "jira-linear": [
        ("Linear's blog post", "https://linear.app/blog/issue-tracking-is-dead"),
        ("Linear", "https://linear.app"),
        ("Jira (Atlassian)", "https://www.atlassian.com/software/jira"),
        ("Vercel", "https://vercel.com"),
        ("Anthropic", "https://anthropic.com"),
        ("OpenAI", "https://openai.com"),
    ],
}

# Auto-detect topic from notes/script content and pick ref set
for key, refs in known_refs.items():
    for name, url in refs:
        if name.lower() in (notes + script).lower():
            ref_lines.append(f"• {name}: {url}")

# Also grab any URLs from notes (research links)
if os.path.exists(srt_path.replace('/sources/', '/').replace('source.en.srt', '')):
    urls_in_notes = re.findall(r'(https?://[^\s,\)]+)', notes)
    for url in urls_in_notes:
        if not any(url in r for r in ref_lines):
            ref_lines.append(f"• {url}")

# ── Assemble final description ────────────────────────────────────────────
parts = []

# Summary (capped at ~1200 chars)
parts.append(extended_summary[:1200])
parts.append("")

# Table of contents
parts.append("📋 What's in this episode:")
parts.append("")
parts.extend(toc_items)
parts.append("")

# Quotes (optional — only if there are notable ones)
if quote_refs:
    parts.append("💬 Key quotes:")
    parts.extend(quote_refs)
    parts.append("")

# References
parts.append("📚 References & Resources:")
parts.extend(ref_lines)
parts.append("")

# Channel boilerplate
duration_str = f"{duration_secs // 60}:{duration_secs % 60:02d}" if duration_secs else ""
parts.append(f"🎙️ That's Interesting Stuff — AI-generated podcast exploring ideas from curated articles, books, and videos.")
if duration_str:
    parts.append(f"⏱️ Episode length: ~{duration_str}")
parts.append(f"🔔 Subscribe for weekly deep dives into technology, productivity, and the ideas shaping our world.")
parts.append("")
parts.append("#ThatIsInterestingStuff #AI #Podcast")

description = '\n'.join(parts)

# ── Derive tags from content ─────────────────────────────────────────────
base_tags = ["that is interesting stuff", "podcast", "education"]
content_lower = (notes + script).lower()

tag_map = {
    "AI": re.search(r'\bai\b|agents?|artificial intelligence|ai ', content_lower),
    "software development": re.search(r'jira|linear|code |dev |software|engineer|issue.*track', content_lower),
    "productivity": re.search(r'producti|habit|focus|time.*manage', content_lower),
}

auto_tags = [name for name, match in tag_map.items() if match]

# ── Write outputs ─────────────────────────────────────────────────────────
meta = {
    "title": "",  # filled by caller (from TickTick or outline)
    "description": description,
    "extended_summary": extended_summary[:500],
    "toc": toc_items,
    "tags": list(dict.fromkeys(base_tags + auto_tags)),  # dedupe
    "source_url": source_url,
    "word_count": word_count,
    "duration_secs": duration_secs,
    "duration_str": duration_str,
}

with open(os.path.join(out_dir, 'youtube-description.txt'), 'w') as f:
    f.write(description)

with open(os.path.join(out_dir, 'youtube-metadata.json'), 'w') as f:
    json.dump(meta, f, indent=2)

# Print description to stdout for human review
print(description)
print(f"\n--- metadata ---")
print(f"Words: {word_count} | Duration: {duration_str}")
print(f"Tags: {meta['tags']}")
PYEOF
