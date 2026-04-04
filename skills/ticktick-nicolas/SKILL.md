---
name: ticktick-nicolas
description: Nicolas's TickTick organization guide. Use when trying to determine where to move an item from the Inbox. Documents task organization structure and decision rules for categorizing tasks.
---

# ticktick-nicolas - Nicolas's TickTick Organization Guide

Use this skill when trying to determine where to move an item from the Inbox. This documents Nicolas's task organization structure and decision rules for categorizing tasks.

## Project Overview

### Active Projects (Open)

| Project | ID | Purpose | Example Tasks |
|---------|-----|---------|---------------|
| **Inbox** | `inbox` | Catch-all for new items | X/Twitter saves, quick notes, uncategorized items |
| **✔Tâches** | `62c9f6d88f08338579c08dea` | Recurring & admin tasks | Bills, maintenance, health reminders, financial admin |
| **🛒Achats** | `62c4429c52500fe3a9c79c02` | Shopping lists & wishlists | Camping gear, hardware, tech, household items |
| **📚Lecture** | `639b3e518f08b7851bff5500` | Reading queue | Articles, books, podcasts, videos to consume |
| **🧠Apprendre** | `647be9b18f083a365aae8513` | Learning & certifications | Tech tools, courses, certifications (AWS, GCP, data engineering) |
| **☁Idées** | `662073ac8f08148ef475fe1a` | Product/business ideas | App ideas, startup concepts, service ideas |
| **🏠Domotique** | `653fd98f8f08df6fef3584c8` | Home automation | Home Assistant, sensors, MQTT, smart home integrations |
| **⏲Rappels** | `66a67b69aeea91314a706ae1` | One-time reminders | Birthdays, anniversaries, specific deadline reminders |
| **🎁Cadeaux** | `62d9b61fa464b76900b30f67` | Gift ideas | Gift suggestions for family/friends |
| **👨🏻‍🍳Cuisiner** | `663ff6988f08bbdbfc7aad93` | Cooking tasks | Weekly meal planning, recipes to try |
| **Sagesse 😇** | `677217707fb49164bf268923` | Personal development | Career reflections, life goals, wisdom notes |
| **⏳Plus tard** | `67df240c3805512ac186eb68` | Someday/maybe | Future considerations, low-priority items |
| **💆🏻Détente** | `691205f88f0897a8a2774241` | Relaxation/entertainment | Shows to watch, leisure activities |

### Active Side Projects

| Project | ID | Purpose |
|---------|-----|---------|
| **🛠ForgeStream** | `67dda0768f0817e96da9dfa3` | Supplier matching platform (Kanban board) |
| **⚡Gridkeeper** | `68c0c7c48f086e6e210b708d` | Energy/grid tool development |
| **🐣Cuckoo** | `6914c7878f08d18bdaafb97f` | Voice agent project |
| **📩email4ynab** | `67fd28f08f08068dadcaf68b` | Email-to-YNAB integration |
| **The Mobility House** | `6824c4578f0889ecdb56a4c2` | Work: EV charging, OpenADR |
| **💀Disaster** | `68e477988f086b6f77cde0c1` | Disaster recovery/backup project |
| **💁🏽‍♀Voice Agent** | `696d54618f08e09d93a14ebd` | Another voice agent variant |

### Yearly Projects (track annual goals)

| Project | ID | Status |
|---------|-----|--------|
| **💫Projets 2025** | `6768f27eb96c112eaab4dd60` | Active - outdoor activities, home projects, personal goals |

## Decision Rules: Where to Move Inbox Items

### 1. Recurring/Date-Driven Tasks → **✔Tâches**
- Bills, payments, financial deadlines
- Home maintenance (filters, gutters, generators)
- Health appointments, vaccinations
- Subscription renewals
- Administrative deadlines
- **Key indicator**: Has a recurring date or is administrative obligation

### 2. Things to Buy → **🛒Achats**
- Hardware/quincaille items
- Camping/outdoor gear
- Electronics/tech purchases
- Household items
- Gift ideas (if for self)
- **Key indicator**: Is a physical item to purchase

### 3. Articles/Links to Read Later → **📚Lecture**
- Twitter/X posts saved for reading
- Blog posts, articles
- Podcasts to listen to
- YouTube videos to watch
- Books to read
- **Key indicator**: Is content to consume, not act on immediately
- Even technical/research articles go here if the goal is just to read them, not to learn a specific skill

### 4. Learning Topics → **🧠Apprendre**
- Actively teaching yourself languages, frameworks, services
- Certifications to study for
- Courses, tutorials with the goal of hands-on skill building
- Tools to evaluate with the intent of using them
- **Key indicator**: About active skill acquisition (not just reading an article about something)

### 5. Project Ideas → **☁Idées**
- App/service concepts
- Business ideas
- Features for existing projects
- Tools or patterns you want to reproduce/implement (e.g., "reproduce this with pi")
- Research topics with product potential
- **Key indicator**: An actionable concept you'd like to build or experiment with, not just contemplate
- **Important**: Idées IS actionable — it's for things you'd actually like to implement, just not urgently

### 6. Home Automation → **🏠Domotique**
- Home Assistant configurations
- Smart device integrations
- Sensor setups
- MQTT/IoT projects
- **Key indicator**: Related to smart home systems

### 7. Work-Related → **The Mobility House** (or current work project)
- OpenADR/EV charging topics
- Work tasks and research
- **Key indicator**: Related to employer or work domain

### 8. Personal Development → **Sagesse 😇**
- Career reflections
- Life goals
- Quotes/wisdom to remember
- Self-improvement notes
- **Key indicator**: About personal growth, not project tasks

### 9. Entertainment/Leisure → **💆🏻Détente**
- TV shows/movies to watch
- Relaxation activities
- Entertainment recommendations
- **Key indicator**: For relaxation, not productivity

### 10. Gift Ideas → **🎁Cadeaux**
- Gift suggestions for others
- **Key indicator**: Item is intended as a gift for someone else

### 11. Cooking/Food → **👨🏻‍🍳Cuisiner**
- Recipes to try
- Meal planning
- Food-related tasks
- **Key indicator**: Related to cooking or meal preparation

### 12. Urgent but Unclear → **⏲Rappels**
- Set a reminder date to revisit
- One-time date-specific reminders
- **Key indicator**: Needs to be reminded at a specific time but doesn't fit elsewhere

## Tags Used

- `camping` - Outdoor/camping activities
- `windsurf` - Windsurfing equipment/activities
- `quincaillerie` - Hardware store items
- `costco` - Costco shopping
- `dollarama` - Dollarama shopping
- `amazon` - Amazon purchases
- `brassage` - Beer brewing
- `pleinair` - Outdoor activities
- `vélo` - Cycling related
- `wishlist` - Desired items
- `cadeau` - Gift ideas
- `vacances` - Vacation related
- `livre` - Books
- `addison` - Addison Electronics
- `ikea` - IKEA items
- `piscine` - Pool related

## Handling X/Twitter Posts from Inbox

Many inbox items are X/Twitter posts saved via automation. They typically have a generic title like "Post de <name> sur X" and just a URL in the body. When processing these:

### Automated Processing with Subagent

An automated subagent `ticktick-inbox-processor` is available to process these items in bulk. It:
- Fetches tweet content via FxEmbed API
- Visits linked URLs (using `web_fetch` with Jina Reader fallback) to extract context
- Creates descriptive titles and comprehensive summaries
- Preserves any personal notes
- Leaves items in Inbox for categorization

**To use:** Run the subagent with specific task IDs or batches. See the agent definition at `~/.pi/agents/ticktick-inbox-processor.md`.

### Manual Rewrite (if needed)

If you need to process items manually:

1. **Fetch the tweet** using the FxEmbed API (no auth required):
   ```bash
   curl -sL "https://api.fxtwitter.com/USER/status/TWEET_ID" | jq -r '.tweet.text'
   ```
   - Full response: `curl -sL "https://api.fxtwitter.com/USER/status/TWEET_ID"`
   - See the `fxembed` skill for all available fields (author, media, quote tweets, polls, etc.)
   - Fallback: Jina Reader API (`https://r.jina.ai/https://x.com/...`) requires `JINA_API_KEY`

2. **Update the title** to describe the actual content (not "Post de X sur Y")

3. **Rewrite the body** with:
   - The tweet text or article summary as the first line(s)
   - The direct tweet URL as the last line
   - Include any additional URLs from the article
   - Preserve any personal notes at the end

4. **Then categorize** using the decision rules above (usually → **📚Lecture** for articles/content, or the relevant project if actionable)

### Example transformation

**Before:**
- Title: `Post de Tommy D. Rossi sur X`
- Body: `https://x.com/__morse/status/2032741777053032863?s=51`

**After:**
- Title: `Playwriter.dev: Chrome CDP extension with Playwright API for agents`
- Body: Tweet text + `https://x.com/__morse/status/2032741777053032863`

## Workflow for Actionable Inbox Items

### Critical Rules

1. **NEVER replace content — ALWAYS append.** Every tickrs task has original links, notes, or URLs. When updating a task, you MUST preserve all existing content. Read the current content first, then append your enrichment after a `---` separator. If you replace content and lose a link or note, that data is gone.

2. **Use `NeedHumanInput` tag when unsure.** If you cannot confidently determine where an item belongs, add the `NeedHumanInput` tag and leave it in Inbox. Never guess on ambiguous items — they will be reviewed later. Do NOT remove the tag once added.

3. **Always enrich before moving.** Steps for every item:
   - a. Fetch the existing task content (read-only)
   - b. Fetch any linked URLs/tweets to understand the actual content
   - c. Write a descriptive note: summary of the content, what it's about, why the user might have saved it, proposed priority, proposed due date if relevant
   - d. **Append** to existing content using `---` separator
   - e. Update the title to be descriptive (not "Post de X sur Y")
   - f. Move to the appropriate project

4. **Be cautious.** Inbox items represent hours of the user's attention. Losing a link, a note, or miscategorizing something is worse than leaving it in Inbox. When in doubt, leave it.

### Enrichment Format

When updating content, always use this pattern:

```
[EXISTING CONTENT — always preserved verbatim]

---
[Your summary: what this is, why it matters]
Proposed priority: high/medium/low
Proposed due: date if applicable
Category rationale: why this goes to [project name]
```

### Example

**Before:**
- Title: `Post de Karpathy sur X`
- Content: `https://x.com/karpathy/status/123456?s=51`

**After (correct):**
- Title: `Karpathy — agent memory architectures`
- Content:
```
https://x.com/karpathy/status/123456?s=51

---
Karpathy discusses new approaches to agent memory, comparing vector
DB retrieval vs state-passing architectures. Relevant to pi session
management — could inform how we handle context persistence.
Proposed priority: medium
Category rationale: Goes to Idées as a pattern we could implement
```

### Decision Process

1. Gather information (tweets, links, files)
2. Ask clarifying questions if the intent is unclear
3. Propose a plan if action is needed beyond categorization
4. WAIT FOR CONFIRMATION for any mutation
5. Execute on approval
6. Create follow-up tasks if they emerge naturally
7. If blocked, document blockers clearly in the task

## Family Calendars (Google Calendar via `gog`)

Multiple shared calendars exist under your Google account. For school/kids events, use the appropriate calendar:

| Calendar | ID | Purpose |
|----------|-----|--------|
| Primary (yours) | `primary` or `nicolas.marchildon@gmail.com` | Your personal events |
| Coralie | `qsmu8och5nchs2tmnm8ru32los@group.calendar.google.com` | Coralie's school/events (owner) |
| Maëva | `d7s4ij1tl8hd44nsaclumpka74@group.calendar.google.com` | Maëva's school/events |
| Collège Reine-Marie | `3465d6684c7c75da18e7d5590135bd861cb3fc99cb@group.calendar.google.com` | School schedules (owner) |
| Alain-Gmail | `armarchildon@gmail.com` | Alain's calendar (reader) |
| Andréanne (rondrouge) | `rondrouge@gmail.com` | Andréanne's calendar (writer) |
| Esther | `esther.gaudreau@gmail.com` | Esther's calendar (reader) |

When dealing with school calendars for the kids, create events on their personal calendar (Coralie or Maëva), not the primary calendar.

## Calendar Item Categorization

When a TickTick item relates to **calendar events** (exams, appointments, schedules):

- **Extract all dates/times** from linked documents or content
- **Check the relevant Google Calendar** via `gog calendar events` before adding duplicates
- **Create events** on the appropriate family calendar (not primary)
- **Color code suggestions**: Red (`--event-color 4`) for exams/deadlines, Green (`7`) for récupération/backup, Orange (`6`) for optional/reprises
- **Remove study blocks unless requested** — Only add exam/specific time events, not generic study sessions
- **Update the TickTick task** with a summary of what was done (dates created, calendar used)

Move the TickTick task to **⏲Rappels** after calendar events are created, since the action item becomes "check on these dates." If the task was purely "add to calendar" and that's done, mark complete or delete the TickTick task.

## Cross-Referencing TickTick ↔ Craft

A very common pattern: when a TickTick action item relates to content tracked in Craft, **link them bidirectionally.**

### How to find the right Craft document

1. Search Craft folders for relevant docs (use `craft documents-list` with folder IDs, or search for keywords)
2. Look for sub-pages within parent docs (e.g., Tesla Y "Gervais" doc has a "Pneus" sub-page with maintenance logs)
3. The Craft URL format for linking: `https://docs.craft.do/doc/<DOC_ID>#block=<BLOCK_ID>`

### Link format in TickTick task content

```
📄 Log Craft: [Document name — Section](https://docs.craft.do/doc/DOC_ID#block=BLOCK_ID)
```

### Known vehicle / asset tracking in Craft

| Asset | Nickname | Craft Doc ID | Sub-pages | Folder |
|-------|----------|-------------|-----------|--------|
| Tesla Model Y | **Gervais** | F56A09C0-5570-46D1-A342-48A1E0F23827 | Immatriculation, Assurance, Financement, Pneus, Recharge, Commande, Prise de possession | Tesla |

The Pneus page (D4B7629C-204D-4CC8-B0E8-827EF8FA6F18) contains a tire change journal with odometer readings and tire specs.

## Recurring & Seasonal Tasks

When a TickTick item is inherently **recurring** (tire changes, seasonal maintenance, annual renewals):

1. **Move to ✔Tâches** (not Inbox) — that's the project for recurring/admin tasks
2. **Always set `--all-day true`** so TickTick shows it as "on this day" rather than a midnight notification:
   ```bash
   tickrs task update <ID> --date "saturday" --all-day true
   ```
   Without `--all-day true`, the task appears at 00:00 which feels like a "reminder at midnight" instead of "do this on this date."
3. **Set up recurrence** using tickrs if supported, or add a note in the content about recurrence pattern
4. **Suggest the recurrence cadence** — spring/fall for tires, annual for most renewals, etc.
5. If the user confirms, note the recurrence pattern in the task content:
   ```
   🔄 Récurrence: printemps (~avril 1) et automne (~octobre 15)
   ```

## Weather-Aware Due Dates

For outdoor/weather-dependent tasks (tire changes, outdoor projects):

- **Check the forecast** for the week around the proposed date using:
  ```bash
  curl -s "https://api.open-meteo.com/v1/forecast?latitude=45.5&longitude=-73.5&daily=temperature_2m_max&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&timezone=America/Toronto"
  ```
- **Propose the best date** based on weather conditions (e.g., +10°C minimum for tire changes)
- **Communicate the rationale** — show the forecast window so the user can adjust manually in TickTick if needed

## Processing Philosophy

### General principles
- **"I will no longer forget this" → Mark complete immediately.** When the underlying action (calendar, reminder) is truly done, mark the TickTick task complete. Don't leave completed items lingering.
- **Start with easy wins first.** When a task has multiple parts (create doc, download files, transcribe, update task), do the straightforward ones first, then tackle the complex or blocked ones.
- **Text that already exists doesn't need transcription.** If a meditation/prayer has a PDF source or published text, extract it directly rather than using Whisper audio transcription.
- **Create follow-up tasks when they naturally emerge.** If processing an item surfaces a related need (e.g., "Google Mini needs resetting" during a playlist task), create that task proactively.
- **"Grill mode" works well for ambiguous items.** When an inbox item is unclear, ask pointed questions to surface the real goal, what's blocking it, and what the user actually wants.
- **Mark items complete boldly.** Once the core action is done and documented, close the item. The user trusts the system.

### Things / assets have nicknames
- The Tesla Model Y is called **"Gervais"** — use this when searching Craft docs or when referencing the car in conversations.

### Recurring maintenance → make it recur
- Tasks that are inherently seasonal or recurring (tire changes, filter swaps, annual renewals) should be moved to **✔Tâches** and set up with recurrence, not left as one-off items in Inbox.

### Weather matters for outdoor tasks
- For Quebec outdoor tasks (tire changes, deck work, etc.), check the forecast before confirming a due date. +10°C is the typical threshold for tire swap season.

### Link everything
- When a TickTick action relates to a Craft document (maintenance logs, reference pages, specs), add the Craft link into the TickTick task content. This is a very common pattern — the task is the action, Craft is the reference/log.
- Conversely, when you add an entry to a Craft log, mention the TickTick task ID so it can be found back.

## Summary Format for TickTick Updates

When you've processed an item and updated its content, use this pattern:

```
[original content preserved]

---
FAIT — YYYY-MM-DD

✅ [What was accomplished]
   - Bullet details
   - Links if relevant

✅ [Additional action taken]
   - E.g., new task created with ID

❌ BLOQUE — [What couldn't be done]
   - Specific reason (tool too old, auth expired, etc.)
   - Exact steps to unblock

❓ Open questions:
   - Things that need user input later
```

This keeps the task as a permanent record of what was done, what's pending, and how to continue.

## TickTick Content Encoding

When updating task content via `tickrs task update -c`, the content is stored as-is. However, when reading back with `--json`, single quotes/apostrophes may appear as `\u0027` in JSON output. Use `tickrs task show <id>` (without `--json`) to view clean text. When writing back, use a heredoc or avoid problematic characters.

## Special Notes

1. **Inbox is large** (~744 items) - mostly X/Twitter posts saved via automation
2. **Content with "Implémenter", "Try", "Test"** in notes usually belongs to a specific active project (email4ynab, Gridkeeper, etc.)
3. **French and English mixed** - Nicolas works in both languages
4. **Craft.do links** indicate reference material, often belongs to ✔Tâches
5. **Time zone**: America/Toronto (Montreal, Quebec)
6. **gog CLI** is available for Google Workspace (calendar, drive, gmail, contacts, sheets) — use it alongside tickrs for calendar-based tasks
7. **Auth note**: `gog` tokens can be revoked; if `invalid_grant` appears, re-set credentials with `gog auth credentials set <path>` then `gog auth add <email> --services calendar` (credentials file is at `~/.gmail_imap_mcp_credentials/client_secret.json`)
