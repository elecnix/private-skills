---
name: podcast-production
description: Set up and run a complete podcast production pipeline with automated research, writing, production, and distribution. Includes automation for episode proposals, audio generation, and RSS publishing.
metadata:
  version: "1.0"
  author: nicolas
---

# Podcast Production

## Description
Set up and run a complete podcast production pipeline with automated research, writing, production, and distribution.

## Getting Started
1. **Initialize the Pipeline**
   ```bash
   mkdir -p agents/podcast-pipeline/scripts
   ```

2. **Key Commands**
   - `episode-proposal.sh`: Generate new episode ideas
   - `generate-audio.sh`: Produce audio from written content
   - `dedup-check.sh`: Prevent duplicate episodes

3. **Example Workflow**
   ```bash
   # Step 1: Plan the next episode (proposes exactly ONE)
   pi subagent agent=podcast-program-director task="Plan the next podcast episode."

   # Step 2: Handoff - When user says "Approved", call Program Director again
   pi subagent agent=podcast-program-director task="Approved: [TITLE]. Kick off production."

   # Step 3: Monitor (if needed)
   pi subagent-status
   ```

4. **Distribution**
   - Use `podcast-publish-rss.py` to update RSS feeds
   - `podcast-distributor.md` handles platform-specific uploads

> Pro tip: Always run `dedup-check.sh` before finalizing episodes to maintain content uniqueness.