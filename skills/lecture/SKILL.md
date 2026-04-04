---
name: lecture
description: Nicolas's reading/lectures management skill. Weekly triage system, content processing pipeline, and Craft knowledge base organization. Goal: maintain "Lecture zero" — fully processed reading list every week.
---

# Lecture — Reading List & Knowledge Pipeline

## Goal
Maintain **Lecture Zero**: every week, process all saved articles, tweets, videos, and newsletters. Transform them into either:
- **Audio content** (podcasts) for passive consumption during commutes/exercise
- **Craft knowledge base entries** for long-term reference
- **Discarded** if no longer relevant

## The Two Pipelines

### Pipeline 1: Topic Deep-Dive Podcast
Focus on **one specific topic** (e.g., "Agent Memory Systems", "MCP Security", "Claude Code Workflows").

**Steps:**
1. **Gather** — collect all Lecture items related to the topic from the past 1-4 weeks
2. **Research** — expand with web searches, fetch full article text, download linked content
3. **Synthesize** — create a structured markdown outline with key insights, quotes, and references
4. **Script** — write a podcast script in conversational format, or a structured article
5. **Audio** — convert to audio via TTS (ElevenLabs, local models, etc.)
6. **Archive** — save everything to organized folder structure (see below)
7. **Craft** — create summary entries in Craft knowledge base with internal links

### Pipeline 2: Weekly News Roundup
Covers **multiple topics** from the week's saves — a broad roundup.

**Steps:**
1. **Collect** — grab all unread/uncategorized Lecture items from the past 7 days
2. **Cluster** — group by topic/theme (AI agents, finance, productivity, tools, etc.)
3. **Summarize** — create brief summaries for each item
4. **Script** — write a news roundup podcast script or structured digest
5. **Audio** — convert to audio
6. **Archives** — save organized by week/date
7. **Craft** — create weekly digest entry in Craft with topic tags

## Folder Structure

```
~/Lecture/
├── 2026-04-04_agent-memory-systems/
│   ├── 00-outline.md           # Podcast or article outline
│   ├── 01-script.md            # Podcast script
│   ├── 02-karpathy-darkwiki.md # Article/tweet summary (per source)
│   ├── 03-beads-memory.md
│   ├── 04-graphiti-knowledge.md
│   ├── downloads/              # Original PDFs, screenshots, media
│   │   ├── karpathy-darkwiki.pdf
│   │   └── ...
│   └── audio/                  # Generated audio output
│       └── podcast.mp3
├── 2026-04-11_weekly-roundup/
│   ├── 00-outline.md
│   ├── 01-script.md
│   ├── ai-agents/
│   │   └── ...
│   ├── tools/
│   │   └── ...
│   └── ...
└── ...
```

## Weekly Triage Routine (30 min max)

Every week (recommended: Monday morning):

1. **List** all items in 📚Lecture TickTick project: `tickrs task list --json --project-id "639b3e518f08b7851bff5500"`
2. **Flag** items older than 14 days → delete them (they've lost relevance unless marked important)
3. **Cluster** remaining items by topic
4. **Execute** one pipeline:
   - If there's enough content on one topic → **Topic Deep-Dive**
   - If scattered topics → **Weekly Roundup**
5. **Process** each item through the pipeline
6. **Create** Craft knowledge base entries with internal links
7. **Delete** processed TickTick tasks (Lecture Zero achieved)
8. **Log** what was covered this week in a tracking document

## Craft Knowledge Base Organization

Structure the Craft knowledge base to mirror Lecture topics:

```
📚 Resources/
├── 🤖 AI Agents/
│   ├── Agent Memory & Knowledge/
│   │   ├── Beads (Steve Yegge)          # Internal Craft link
│   │   ├── Graphiti temporal knowledge   # Internal Craft link
│   │   ├── LLM Consortium LlamaIndex     # Internal Craft link
│   │   └── ...
│   ├── Agent Frameworks/
│   │   ├── LangGraph                     # Internal Craft link
│   │   ├── CrewAI                        # Internal Craft link
│   │   └── ...
│   ├── MCP (Model Context Protocol)/
│   │   ├── MCP Servers                   # Internal Craft link
│   │   ├── MCP Security                  # Internal Craft link
│   │   └── ...
│   └── ...
├── 💡 Productivity/
│   ├── Habit Building/
│   │   ├── Atomic Habits summary         # Internal Craft link
│   │   ├── Compound Effect summary       # Internal Craft link
│   │   └── Tiny Experiments summary      # Internal Craft link
│   └── ...
```

### Craft Entry Format
Each entry in Craft is a sub-page under its topic, containing:
- **Title:** Descriptive (not "Post de X sur Y")
- **First line:** Tweet/article summary or key quote
- **Body:** Full content summary, key insights, context
- **Last line:** Original URL/source link
- **Optional:** Related internal links to other Craft pages

## Content Types & Processing Rules

### Productivity Game Summaries (TOP 5, SUMMARY, BONUS)
- **Always** process these — they're high-value, evergreen
- Create a Craft entry in `Resources → Productivity → [Topic]`
- **Priority** for podcast generation — these are excellent audio content
- Format: book summary + key takeaways + personal reflection

### Technical Tweets (AI, agents, tools)
- **Cluster** by topic — individual tweets get merged into topic documents
- Create Craft entries under relevant topic (AI Agents, MCP, etc.)
- **Podcast candidate** — merge related tweets into a cohesive segment

### YouTube Videos
- If short (<10 min): summarize and create Craft entry
- If long or technical: **highest priority** for Topic Deep-Dive podcast
- Video title → Craft page title, summary → body, URL → last line

### Newsletter Forwards & Emails
- Extract key insights, create Craft entry
- Delete the forwarded email content after processing
- Archive to folder if reference needed

### Articles & Blog Posts
- Fetch full text, create summary in Craft
- Download PDF if available
- **High podcast candidate** for Topic Deep-Dive

## TickTick Integration

### What Goes Into 📚Lecture
- Things to consume (read, watch, listen)
- Articles, videos, book summaries, newsletters
- Simple tweet saves with no build/intent notes
- **NOT** things to implement (those go to ☁Idées or a project)

### What Gets Deleted From Lecture
- Older than 14 days and not marked important
- Already processed into Craft entries (after Craft links are verified)
- Duplicates of already-processed items

### Task Content Format After Processing
When a Lecture item is processed:
```
[original content preserved]

---
PROCESSED: YYYY-MM-DD
→ Craft: [Page Title](https://docs.craft.do/doc/...)
→ Podcast: ~/Lecture/YYYY-MM-DD_topic/audio/podcast.mp3
→ Archived: ~/Lecture/YYYY-MM-DD_topic/
```

## Sub-Agent Pipeline Architecture

For podcast generation, use a chain of specialized sub-agents:

### Agent 1: Researcher
- Gathers all source material for a topic
- Fetches full article text, downloads PDFs, saves tweets
- Organizes content into folder structure by date/topic

### Agent 2: Synthesizer
- Reads all gathered material
- Creates structured outline with key themes, insights, quotes
- Identifies gaps that need more research

### Agent 3: Script Writer
- Takes the outline and writes a podcast script or structured article
- Conversational tone for podcasts, structured format for articles
- Includes references and timestamps

### Agent 4: TTS Producer
- Converts script to audio
- Uses ElevenLabs, local TTS, or other engine
- Saves audio to folder structure

### Agent 5: Craft Publisher
- Creates Craft knowledge base entries
- Links to other relevant Craft pages
- Verifies links and formatting

## Weekly Schedule

Suggested weekly rhythm:
- **Monday**: 30-min triage — process Lecture list, pick pipeline
- **Tuesday-Thursday**: Run pipeline (sub-agents, or manual if automated)
- **Friday**: Review Craft entries, verify links, celebrate Lecture Zero
- **Weekend**: Listen to generated podcast during activities

## Success Metrics

- **Lecture Zero**: Achieve weekly (all Lecture items processed or deleted)
- **Podcast Output**: At least 1 podcast/week (topic or roundup)
- **Craft Growth**: Knowledge base grows with organized, searchable entries
- **Retention**: Topics covered in podcasts are retained (spaced repetition in future roundups)
- **Time**: Under 2 hours/week total (30 min triage + 90 min pipeline automation)
