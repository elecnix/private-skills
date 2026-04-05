---
name: lecture
description: "Nicolas's reading/lectures management skill. Weekly triage system, content processing pipeline, and Craft knowledge base organization. Goal: maintain 'Lecture zero' — fully processed reading list every week."
---

# Lecture — Reading List & Knowledge Pipeline

## Source of Truth
The **TickTick Lecture list** is the single source of truth for Lecture items. Do NOT scan the filesystem (`~/Documents/Lecture/`) to discover reading items — those folders are the *output* of pipeline processing (research, scripts, audio, video). When asked to triage, review, or process the Lecture list, always query TickTick first (via `tickrs` CLI) and use those results.

### Using the `tickrs` skill
When interacting with TickTick, **load the `tickrs` skill** (`/home/nicolas/.agents/skills/tickrs/SKILL.md`) for full CLI reference, including project listing, task filtering, tag management, and JSON output formatting. Use it to discover the Lecture project ID, list tasks, and apply/remove `tis_started` / `tis_published` tags.

## Goal
Maintain **Lecture Zero**: every week, process all saved articles, tweets, videos, and newsletters. Transform them into either:
- **Audio content** (podcasts) for passive consumption during commutes/exercise
- **Craft knowledge base entries** for long-term reference
- **Discarded** if no longer relevant

## The Pipeline

```
Researcher → Synthesizer → Script Processor → [Visual Producer ↔ TTS Producer] → Video Composer → YouTube Publisher
```

### Production Scripts

All scripts are in `~/Source/private-skills/lecture-pipeline/scripts/`:

| Script | Purpose |
|--------|---------|
| `research-topic.sh` | Fetch articles from URLs into topic folder |
| `tts-normalize.py` | Strip markdown, expand abbreviations → clean TTS-ready text |
| `generate-audio.sh` | Generate audio + SRT from normalized text (edge-tts) |
| `generate-visuals.py` | Generate title/section/stat/quote cards + timeline.json |
| `compose-video.py` | Match SRT → visuals, compose 1080p video with ffmpeg |
| `generate-description.sh` | Generate YouTube description + tags |

### Quick-Start: Process a New Topic

```bash
# 1. Create topic folder and research
mkdir -p "$HOME/Documents/Lecture/That's Interesting Stuff/YYYY-MM-DD_topic-name"

# 2. Run researcher agent (manual: fetch sources, create 00-briefing.md + 01-research-notes.md)

# 3. Synthesizer creates script (manual: write 03-podcast-script.md)

# 4. Run audio generation
bash ~/Source/private-skills/lecture-pipeline/scripts/generate-audio.sh \
  "$HOME/Documents/Lecture/That's Interesting Stuff/YYYY-MM-DD_topic-name/"

# 5. Run visual generation (define cards + timeline in visual config)
python3 ~/Source/private-skills/lecture-pipeline/scripts/generate-visuals.py \
  "$HOME/Documents/Lecture/That's Interesting Stuff/YYYY-MM-DD_topic-name/" \
  --config visuals/config.json

# 6. Compose video (matches SRT to visuals, ffmpeg composes)
python3 ~/Source/private-skills/lecture-pipeline/scripts/compose-video.py \
  "$HOME/Documents/Lecture/That's Interesting Stuff/YYYY-MM-DD_topic-name/"
```

### TTS Configuration (proven settings)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Voice | `en-US-AndrewNeural` | Conversational, warm, relaxed |
| Rate | `-12%` | Slower delivery |
| Pitch | `-3Hz` | Slightly deeper |
| Volume | `-1dB` | Slightly softer/intimate |
| French | `fr-FR-HenriNeural` | With rate `-10%`, pitch `-2Hz` |

### Visual Card Layout

```
┌──────────────────────────────────────────────┐
│ THAT'S INTERESTING STUFF    (accent line)    │
│                                              │
│                                              │
│        [TOP HALF: Content Cards]             │
│        Title cards, quotes, stats,           │
│        section transitions, etc.             │
│                                              │
│                                              │
│ ──────────────────────────────────────────  │
│                                             ▲
│                                             │ CONTENT_H = 540
├─────────────────────────────────────────────┤
│                                             │
│     [BOTTOM HALF: Subtitles]                │ BOTTOM HALF (540-1080)
│     Burned-in, from edge-tts SRT            │ Burned-in subtitles
│     FontSize=14, DejaVu Sans                │ (14px, no outline needed)
│                                             │
└──────────────────────────────────────────────┘
```

## Pipeline Agents

All 10 agents use `qwen/qwen3.6-plus:free`. Config files in `~/Source/private-skills/lecture-pipeline/`, registered as `lecture-{name}` in the pi agent manager.

| Agent | Registered As | Purpose |
|-------|--------------|---------| 
| **researcher** | `lecture-researcher` | Fetch content, search web, organize sources |
| **synthesizer** | `lecture-synthesizer` | Research → outline + conversational script |
| **visual-researcher** | `lecture-visual-researcher` | Find diagrams, screenshots, logos from web |
| **stock-images** | `lecture-stock-images` | Search Unsplash per section, download 1920×1080 |
| **visual-producer** | `lecture-visual-producer` | Title/section/stat/quote cards (Python Pillow) |
| **visual-editor** | `lecture-visual-editor` | Composite visuals into final cards + timeline.json |
| **script-processor** | `lecture-script-processor` | Markdown → clean TTS-ready text |
| **video-composer** | `lecture-video-composer` | SRT → visual timing → ffmpeg compose |
| **youtube-publisher** | `lecture-youtube-publisher` | Upload to `@that-is-interesting-stuff`, schedule Premiere |
| **publisher** | `lecture-publisher` | Craft knowledge base entries |

## Orchestrator

The orchestrator **must be launched async** (`async=True`) by default. This keeps the parent agent free to:
- Manage **multiple orchestrators** in parallel (different topics, newsletters)
- **Respond to the user** during pipeline execution
- Perform other tasks while the pipeline runs in the background

The orchestrator itself **must delegate to subagents** (CHAIN + PARALLEL) to run the pipeline. Never execute phases sequentially when parallelism is available — always fan out independent work via `subagent` calls. The full pipeline is a chain where Phase 4 and Phase 7 use PARALLEL fan-out.

### Dependency Graph

```
Phase 1: Researcher         (sequential — must finish first)
    │
Phase 2: Synthesizer         (sequential — needs Researcher output)
    │
Phase 3: Script Processor    (sequential — normalizes 03-podcast-script.md → audio/podcast-ready.txt)
    │
Phase 4: 4-way PARALLEL (all triggered after Script Processor completes)
    ├── lecture-visual-researcher  (finds web images/diagrams)
    ├── lecture-stock-images       (finds Unsplash photos)
    ├── lecture-visual-producer    (generates text cards: headers, stats, quotes)
    └── lecture-tts-producer       (edge-tts audio/podcast-ready.txt → mp3 + srt)
         │
Phase 5: lecture-visual-editor     (needs Phase 4 visuals done: composites cards + writes timeline.json)
    │
Phase 6: lecture-video-composer    (convergence: needs timeline.json + podcast.srt + podcast.mp3)
    │
Phase 7: 2-way PARALLEL
    ├── lecture-youtube-publisher  (uploads video + captions)
    └── lecture-publisher          (creates Craft knowledge base entries)
```

The critical parallelism win: Phase 4 has **zero internal dependencies** between its four agents. The Script Processor must run first (Phase 3) to produce `audio/podcast-ready.txt`, then all Phase 4 agents can run simultaneously.

### TickTick Tag Tracking

When a topic originates from a **TickTick Lecture item**, the orchestrator must keep the source task in sync:

| Tag | When to apply |
|-----|---------------|
| `tis_started` | When Phase 1 kicks off — the item is now being used as source for production |
| `tis_published` | After Phase 6 completes — video is uploaded and scheduled as a YouTube Premiere |

Add/remove tags via the `tickrs` CLI. Example at kickoff (Phase 1):
```bash
tickrs task modify "<task-id or name>" --add-tag tis_started
```

And after YouTube upload completes (Phase 6):
```bash
tickrs task modify "<task-id or name>" --add-tag tis_published
tickrs task modify "<task-id or name>" --remove-tag tis_started  # optional cleanup
```

### Running the Full Pipeline — Async (Recommended)

The orchestrator **should be launched async** so the parent agent remains free to manage other orchestrators, respond to the user, or perform other tasks while the pipeline runs in the background.

#### How It Works

1. **Launch the orchestrator async** with `subagent(async=true, ...)` — returns immediately with a run ID
2. **Poll status** with `subagent_status` to check progress / current phase
3. **Report to user** when done, or proactively notify on errors
4. **Run multiple orchestrators in parallel** — launch topic A and topic B simultaneously

#### Launch Pattern

Pass the topic folder as the task:

```python
# Topic folder (created by Researcher or manually):
TOPIC = "/home/nicolas/Documents/Lecture/That's Interesting Stuff/2026-04-05_some-topic"
```

Launch async — returns immediately with a run ID:

```python
# This returns INSTANTLY — the orchestrator runs in background
result = subagent(
    agent="worker",
    async=True,
    share=False,
    artifacts=False,
    task=f"""Run the full lecture pipeline for: {TOPIC}

This is a 7-phase pipeline:
Phase 1: Research (lecture-researcher)
Phase 2: Synthesize script (lecture-synthesizer)  
Phase 3: TTS normalization (lecture-script-processor)
Phase 4: 4-way parallel — visual researcher, stock images, visual producer, TTS producer
Phase 5: Visual editor composite
Phase 6: Video compose
Phase 7: 2-way parallel — YouTube upload + Craft publishing

Execute phases 1→2→3 sequentially, then fan-out Phase 4 as PARALLEL, then Phase 5, then Phase 6, then fan-out Phase 7 as PARALLEL.
Use subagent() calls for each phase. Report final status with file paths when done."""
)
run_id = result["runId"]  # e.g. "abc12345-..."
print(f"Orchestrator launched! Run ID: {run_id}")
print(f"Topic: {TOPIC}")
# ... parent agent is now FREE to do other things
```

#### Monitor Progress

```python
# Check status at any time
status = subagent_status(id=run_id)
# Returns: State (running|complete), Step (N/M), Last Update
```

#### Parallel Orchestrators

You can fire off **multiple topic pipelines simultaneously**:

```python
# Launch orchestrator for topic A
orch_a = subagent(agent="worker", async=True, task="Run full pipeline for: /path/to/topic-a")

# Immediately launch topic B — no waiting
orch_b = subagent(agent="worker", async=True, task="Run full pipeline for: /path/to/topic-b")

# While both run, respond to user, triage Lecture list, manage TickTick, etc.

# Check both later
subagent_status(id=orch_a["runId"])
subagent_status(id=orch_b["runId"])
```

#### When Done — Notify User

When `subagent_status` shows complete, read the output artifact and inform the user with results (video location, Craft entry, any errors by phase).

### Running the Full Pipeline — Sync (Fallback)

For simple single-topic runs where blocking is acceptable, use a synchronous chain:

```python
subagent(chain=[
  # Phase 1: Research sources
  {"agent": "lecture-researcher",
   "task": f"Process topic folder: {TOPIC}"},

  # Phase 2: Write podcast script (reads Phase 1 output)
  {"agent": "lecture-synthesizer",
   "task": f"Read {previous} output files in {TOPIC}/, create 02-outline.md and 03-podcast-script.md"},

  # Phase 3: Normalize script for TTS
  {"agent": "lecture-script-processor",
   "task": f"Run tts-normalize.py on {TOPIC}/03-podcast-script.md. Produces audio/podcast-ready.txt."},

  # Phase 4: 4-way parallel — visuals (3 agents) + audio (1 agent)
  {"parallel": [
    {"agent": "lecture-visual-researcher",
     "task": f"Read {TOPIC}/03-podcast-script.md, find relevant images. Folder: {TOPIC}"},
    {"agent": "lecture-stock-images",
     "task": f"Read {TOPIC}/03-podcast-script.md, search Unsplash per section. Folder: {TOPIC}"},
    {"agent": "lecture-visual-producer",
     "task": f"Read {TOPIC}/03-podcast-script.md, generate text cards + timeline config. Folder: {TOPIC}"},
    {"agent": "lecture-tts-producer",
     "task": f"Convert {TOPIC}/audio/podcast-ready.txt to audio. Folder: {TOPIC}"},
  ]},
  # Phase 5: Composite visuals (needs Phase 4 visual agents done)
  {"agent": "lecture-visual-editor",
   "task": f"Composite visuals from {TOPIC}/visuals/stock/ and {TOPIC}/visuals/assets/ into final cards. Write timeline.json."},

  # Phase 6: Compose video (needs SRT + mp3 from Phase 4 + timeline from Phase 5)
  {"agent": "lecture-video-composer",
   "task": f"Compose video in {TOPIC}. Match srt to visuals, run ffmpeg."},

  # Phase 7: 2-way parallel publishing
```

**Total wall-clock time** = Phase 1 + Phase 2 + Phase 3 + max(Phase 4 agents) + Phase 5 + Phase 6 + max(Phase 7 agents).

Because Phase 4's 4 agents run simultaneously, the slowest one determines the bottleneck (usually `lecture-visual-researcher` or `edge-tts` in `lecture-tts-producer`). Without parallelism, those 4 steps would run sequentially and multiply the wait.

When launched **async**, the parent agent incurs zero wait time for agent spawning — it returns immediately after queueing. The actual pipeline duration is the same, but the orchestrator runs in the background.

### Running a Single Topic (Manual Steps)

If you don't want the full chain, each step can be triggered independently via subagent (sync or async):

```python
# Start at any phase — agents read from the topic folder:
subagent(task="Process /home/nicolas/Documents/Lecture/.../YYYY-MM-DD_topic/", agent="lecture-researcher")

# Async kickoff — returns immediately:
subagent(async=True, task="Process /home/nicolas/Documents/Lecture/.../YYYY-MM-DD_topic/", agent="lecture-researcher")

# Once audio/podcast-ready.txt exists (after Phase 3), launch visuals + audio in parallel:
subagent(parallel=[
  {"agent": "lecture-visual-researcher", "task": "Folder: <path>"},
  {"agent": "lecture-stock-images",      "task": "Folder: <path>"},
  {"agent": "lecture-visual-producer",   "task": "Folder: <path>"},
  {"agent": "lecture-tts-producer",      "task": "Folder: <path>"},
])
```

### Scripts as Shortcuts

The production scripts in `~/Source/private-skills/lecture-pipeline/scripts/` can be called directly to skip agent overhead:

```bash
# Audio only (no agent needed)
bash ~/Source/private-skills/lecture-pipeline/scripts/generate-description.sh <topic_folder>

# Visual cards only
python3 ~/Source/private-skills/lecture-pipeline/scripts/generate-visuals.py <topic_folder> --config <config.json>

# Video compose only
python3 ~/Source/private-skills/lecture-pipeline/scripts/compose-video.py <topic_folder>
```

These scripts are deterministic and idempotent — run them after the agents have produced their input files.

## The Two Pipelines

### Pipeline 1: Topic Deep-Dive Podcast
Focus on **one specific topic**. 6-10 minutes.

1. Gather all content on the topic → `sources/`
2. Create `00-briefing.md` (overview, themes, gaps)
3. Create `01-research-notes.md` (per-source summaries)
4. Create `02-outline.md` (hook → sections → closing)
5. Create `03-podcast-script.md` (conversational, audio-friendly)
6. Visuals + Audio in parallel
7. Video compose (SRT timestamps → visuals)
8. Upload to YouTube, schedule as Premiere → mark TickTick item with `tis_published` tag
9. Craft knowledge entry

### Pipeline 2: Weekly News Roundup
Covers **multiple topics** from the week's saves.

1. Collect all unread Lecture items from past 7 days
2. Cluster by topic/theme
3. Synthesize digest script
4. Same visual/audio/video steps (reuse existing card templates)
5. Upload as weekly roundup

## Video Format Specs

| Spec | Value |
|------|-------|
| Resolution | 1920×1080 |
| FPS | 2 (static visuals) |
| Audio | edge-tts en-US-AndrewNeural, mono, 24kHz |
| Subtitles | Burned-in, 14px, bottom half |
| Encode | x264, crf 18, tune stillimage, fast preset |
| File size | ~5-7MB for 7 minutes |
| Encode time | ~20 seconds |

## Content Type Processing

### Productivity Game summaries (TOP 5, SUMMARY, BONUS)
- Always process — high-value, evergreen
- Create Craft entry in `Resources → Sagesse → Productivity`
- Priority for podcast generation

### Technical tweets/articles (AI, tools, agents)
- Cluster by topic → merge into cohesive narrative
- Create Craft entries under relevant Engineering topic
- High podcast candidate if 3+ related saves exist

### YouTube Videos
- Short (<10 min): summarize, Craft entry
- Long: Topic Deep-Dive podcast material

### Finance/Personal
- Move to ✔Tâches for action, not Lecture

## Success Metrics

- **Lecture Zero** — all Lecture items processed or deleted each week
- **Video Output** — at least 1 video/week
- **Encodes under 30 seconds** per 7-10 min video
- **Time** — under 30 min manual work per video (rest is agent-generated)
