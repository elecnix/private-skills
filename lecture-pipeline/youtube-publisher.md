---
name: lecture-youtube-publisher
description: Upload generated podcast videos and subtitles to YouTube. Handles OAuth2, auto-generated descriptions, premiere scheduling, video publishing, and caption uploads.
tools: bash
thinking: low
model: qwen/qwen3.6-plus:free
skills: aeyes, cibc-download, cloudflare, craft, docker-nas, elecnix-skills, find-skills, fxembed, github, gog, grill-me, manuvie-download, oauth, portless, portless-marchildon, private-skills, rogersbank-download, scanner, tangerine-download, tickrs, ticktick-nicolas, transcribe, unsplash
---

# YouTube Publisher Agent

Uploads generated podcast videos and synchronized subtitles to the "That's Interesting Stuff" channel at https://www.youtube.com/@that-is-interesting-stuff

## Pipeline Integration

Run `generate-description.sh` FIRST, then use this publisher. The description generator produces:

- `output/youtube-description.txt` — Full YouTube-ready description
- `output/youtube-metadata.json` — Machine-readable metadata (title, description, tags, source_url, duration)

```bash
# Step 1: Generate description with references
bash ~/Source/private-skills/lecture-pipeline/scripts/generate-description.sh \
  "$TOPIC_DIR" "https://youtu.be/pzUn9wTCgcw"

# Step 2: Upload to YouTube (this publisher)
# Reads metadata from output/youtube-metadata.json automatically
```

## Credentials & Setup

### One-time setup (already done)
- **Google Cloud Project:** home-assistant-729120 (YouTube Data API v3 enabled)
- **OAuth Client:** `YOUR_CLIENT_ID.apps.googleusercontent.com` (see client_secret JSON file)
- **Client Secret File:** `~/Téléchargements/client_secret_YOUR_CLIENT_ID.apps.googleusercontent.com.json`
- **Saved Credentials:** `/home/nicolas/.config/youtube-credentials.json`

### Required OAuth scopes
```
https://www.googleapis.com/auth/youtube.upload    # Upload videos
https://www.googleapis.com/auth/youtube            # Channel management
https://www.googleapis.com/auth/youtube.force-ssl  # Required for captions + metadata patch
```

### Caption uploads require re-auth
If token is missing `youtube.force-ssl`, re-authenticate:

```python
import urllib.parse
CLIENT_ID = "YOUR_CLIENT_ID.apps.googleusercontent.com"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.force-ssl"]
params = {"response_type": "code", "client_id": CLIENT_ID, "redirect_uri": "urn:ietf:wg:oauth:2.0:oob", "scope": " ".join(SCOPES), "access_type": "offline", "prompt": "consent"}
url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
print(url)
```

After authorizing, exchange the code:
```bash
curl -s -X POST "https://oauth2.googleapis.com/token" \
  -d "code=$AUTH_CODE" \
  -d "client_id=YOUR_CLIENT_ID.apps.googleusercontent.com" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=urn:ietf:wg:oauth:2.0:oob" \
  -d "grant_type=authorization_code"
```

Save the response to `/home/nicolas/.config/youtube-credentials.json`.

## Schedule: Première at 20h00 ET (next available slot)

When scheduling a video for publication, compute the next available **20h00 ET** slot that is at least **2 hours from now**:

```bash
# Compute next 20h00 ET slot (at least 2h from now)
python3 -c "
from datetime import datetime, timedelta, timezone
import pytz

et = pytz.timezone('America/Toronto')
now_et = datetime.now(et)
target = now_et.replace(hour=20, minute=0, second=0, microsecond=0)

if target <= now_et + timedelta(hours=2):
    target += timedelta(days=1)

# Ensure no conflicts with existing scheduled videos (check previous runs)
# Add 1 day if today already has a premiere
print(target.isoformat())
"
```

### Publishing modes

**Mode 1: Premiere at next 20h00 ET slot** (default — recommended)
- Compute next 20h00 ET slot ≥2h from now
- Upload with `privacyStatus: private` + `publishAt` set to the slot time
- Creates a scheduled publish (auto-goes public at the scheduled time)
- Update video title, description, tags immediately after upload

**Mode 2: Upload as unlisted** (for review before publishing)
- Upload with `privacyStatus: unlisted`, no `publishAt`
- Manually set to public later when ready

### Première avec chat en direct (true Premiere)

L'API YouTube permet de créer une vraie **Première** (page publique avec compte à rebours + chat en direct) via les `liveBroadcast` resources. **However**, the channel must have **live streaming enabled** first.

To check:
```bash
# If you get 'liveStreamingNotEnabled', enable it manually in YouTube Studio:
# https://www.youtube.com/features
# Then wait 24h for activation
```

Once live streaming is enabled, create a Premiere via API:
```bash
# Step 1: Upload video as private (done above)
# Step 2: Create liveBroadcast with the video
PREMIERE_BROADCAST=$(cat <<EOF
{
  "snippet": {"title": "$TITLE", "description": "$DESC", "scheduledStartTime": "$SCHEDULE_TIME"},
  "status": {"privacyStatus": "public"},
  "contentDetails": {
    "enableAutoStart": true, "enableAutoStop": true,
    "monitorStream": {"enableMonitorStream": false},
    "enableEmbed": true, "enableLowLatency": false
  }
}
EOF
)

BROADCAST_ID=$(curl -s -X POST \
  "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=snippet,status,contentDetails" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PREMIERE_BROADCAST" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")

# Step 3: Bind the uploaded video to the broadcast
curl -s -X POST \
  "https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id=$BROADCAST_ID&part=id,contentDetails" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"id\": \"$BROADCAST_ID\", \"contentDetails\": {\"boundStreamId\": null, \"boundStreamType\": \"managed\"}}"

# Step 4: Transition to testing → live at scheduled time
# (or manually from YouTube Studio)
```

## Upload Process

### Full Upload Flow

```bash
#!/bin/bash
set -euo pipefail
TOPIC_DIR="$1"
SOURCE_URL="${2:-}"
SCHEDULED="${3:-true}"  # true = schedule for next 20h00 ET slot

VIDEO="$TOPIC_DIR/output/video-podcast.mp4"
SRT="$TOPIC_DIR/audio/podcast.srt"
META="$TOPIC_DIR/output/youtube-metadata.json"

# Compute next 20h00 ET slot (≥2h from now)
SCHEDULE_TIME=$(python3 << 'PY'
from datetime import datetime, timedelta
import pytz, json
et = pytz.timezone('America/Toronto')
now_et = datetime.now(et)
target = now_et.replace(hour=20, minute=0, second=0, microsecond=0)
if target <= now_et + timedelta(hours=2):
    target += timedelta(days=1)
# Convert to ISO 8601 UTC
print(target.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
PY
)

# Read metadata from generated files
if [ -f "$META" ]; then
  TITLE=$(python3 -c "import json; print(json.load(open('$META')).get('title',''))")
  DESCRIPTION=$(python3 -c "import json; print(json.load(open('$META'))['description'])")
  TAGS=$(python3 -c "import json; print(','.join(json.load(open('$META')).get('tags',[])))")
else
  # Fallback: extract from TickTick or use defaults
  TITLE="That's Interesting Stuff — New Episode"
  DESCRIPTION="New episode of the That's Interesting Stuff podcast."
  TAGS="that is interesting stuff,podcast,education"
fi

# Refresh token
TOKEN=$(python3 << 'PYTOKEN'
import json, urllib.request, urllib.parse
with open('/home/nicolas/.config/youtube-credentials.json') as f:
    d = json.load(f)
data = urllib.parse.urlencode({
    'client_id': d['client_id'], 'client_secret': d['client_secret'],
    'refresh_token': d['refresh_token'], 'grant_type': 'refresh_token'
}).encode()
req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data, method='POST')
with urllib.request.urlopen(req, timeout=30) as resp:
    tokens = json.loads(resp.read().decode())
    d['token'] = tokens['access_token']
    with open('/home/nicolas/.config/youtube-credentials.json', 'w') as f2:
        json.dump(d, f2, indent=2)
    print(tokens['access_token'])
PYTOKEN
)

if [ ${#TOKEN} -lt 100 ]; then
  echo "ERROR: Invalid token. Re-auth required."; exit 1
fi

if [ "$SCHEDULED" = "true" ]; then
  PRIVACY="unlisted"
  PUBLISH_JSON=',"publishAt":"'"$SCHEDULE_TIME"'"'
else
  PRIVACY="private"
  PUBLISH_JSON=""
fi

TITLE_ESC=$(echo "$TITLE" | sed 's/"/\\"/g')
DESCRIPTION_ESC=$(echo "$DESCRIPTION" | sed 's/"/\\"/g' | tr '\n' ' ' | sed 's/  */ /g')
TAGS_JSON=$(echo "$TAGS" | tr ',' '\n' | sed 's/.*/ "&"/' | tr '\n' ',' | sed 's/,$//')

METADATA="{\"snippet\":{\"title\":\"$TITLE_ESC\",\"description\":\"$DESCRIPTION_ESC\",\"tags\":[$TAGS_JSON],\"categoryId\":\"27\"},\"status\":{\"privacyStatus\":\"$PRIVACY\",\"selfDeclaredMadeForKids\":false$PUBLISH_JSON}}"

BOUNDARY="===YTUpload$(date +%s)=="

{
  printf -- '--%s\r\n' "$BOUNDARY"
  printf 'Content-Type: application/json; charset=UTF-8\r\n\r\n'
  printf '%s\r\n' "$METADATA"
  printf -- '--%s\r\n' "$BOUNDARY"
  printf 'Content-Type: video/mp4\r\n\r\n'
  cat "$VIDEO"
  printf -- '\r\n--%s--\r\n' "$BOUNDARY"
} > /tmp/yt-multipart-body

RESPONSE=$(curl -s -X POST \
  "https://www.googleapis.com/upload/youtube/v3/videos?part=snippet,status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: multipart/related; boundary=$BOUNDARY" \
  -H "Expect:" \
  --data-binary @/tmp/yt-multipart-body \
  --max-time 600 2>&1)

VIDEO_ID=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))")

if [ -z "$VIDEO_ID" ]; then
  echo "❌ Video upload failed: $RESPONSE"; exit 1
fi

echo "✅ Video: https://www.youtube.com/watch?v=$VIDEO_ID"
echo "✅ Scheduled: $SCHEDULE_TIME (ET)"

# Upload captions (SRT)
if [ -f "$SRT" ]; then
  # Check if auto-captions already exist
  CAP_CHECK=$(curl -s "https://www.googleapis.com/youtube/v3/captions?part=snippet&videoId=$VIDEO_ID" \
    -H "Authorization: Bearer $TOKEN")

  ASR_COUNT=$(echo "$CAP_CHECK" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len([i for i in d.get('items',[]) if i.get('snippet',{}).get('trackKind')=='asr']))")

  if [ "$ASR_COUNT" -gt 0 ]; then
    echo "ℹ️ Auto-captions already exist (ASR track). Skipping manual SRT upload."
  else
    # Try to upload SRT as captions
    BOUNDARY_CAP="===YTCaptions$(date +%s)=="
    python3 << PYCAP
import json, urllib.request

srt_path = "$SRT"
with open(srt_path, 'rb') as f:
    srt_data = f.read()

boundary = "BoundaryYT$(date +%s)"
crlf = b'\r\n'
metadata = json.dumps({"snippet":{"videoId":"$VIDEO_ID","language":"en","name":"English","isDraft":False}})

body = (
    f'--{boundary}'.encode() + crlf +
    b'Content-Type: application/json; charset="UTF-8"' + crlf + crlf +
    metadata.encode('utf-8') + crlf +
    f'--{boundary}'.encode() + crlf +
    b'Content-Type: text/plain; charset="UTF-8"' + crlf + crlf +
    srt_data + crlf +
    f'--{boundary}--'.encode() + crlf
)

url = f'https://www.googleapis.com/upload/youtube/v3/captions?part=snippet'
req = urllib.request.Request(url, data=body, headers={
    'Authorization': 'Bearer $TOKEN',
    'Content-Type': f'multipart/related; boundary="{boundary}"',
    'Content-Length': str(len(body)),
}, method='POST')

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        print(f"✅ Captions uploaded")
except urllib.error.HTTPError as e:
    if e.code == 400 and 'invalidMetadata' in str(e.read()):
        print("⚠️ Caption upload failed — manual upload via YouTube Studio needed")
    else:
        print(f"⚠️ Caption upload failed (HTTP {e.code})")
PYCAP
  fi
  rm -f /tmp/yt-multipart-body
fi

echo "✅ Pipeline complete"
echo "📺 Video: https://www.youtube.com/watch?v=$VIDEO_ID"
echo "🎬 Studio: https://studio.youtube.com/video/$VIDEO_ID"
```

## Critical Upload Requirements

1. **Line endings `\r\n`** in multipart body — plain `\n` causes silent failures
2. **`Content-Type: multipart/related; boundary=...`** — exact header string
3. **`--data-binary @file`** — NOT `-d` or `--data`
4. **`-H "Expect:"`** — prevents `Expect: 100-continue` which confuses YouTube
5. **Timeouts:** 600s for video, 120s for captions
6. **Privacy: `unlisted`** by default, then `public` via scheduled `publishAt`
7. **COPPA: `selfDeclaredMadeForKids: false`** — always required (legally required under COPPA)

## Description Format (auto-generated by generate-description.sh)

The `generate-description.sh` script produces descriptions in this format:

```
[Extended summary paragraph 1 — the hook and opening]

[Extended summary paragraph 2 — the core topic]

📋 What's in this episode:
• [Section title 1]
• [Section title 2]
• [Section title 3]

📚 References & Resources:
• [Named reference with URL]
• [Tool/article mentioned in the video]

🎙️ That's Interesting Stuff — AI-generated podcast exploring ideas...
🔔 Subscribe for weekly deep dives...

#ThatIsInterestingStuff #[Topic] #[Hashtag]
```

This includes:
- **Extended summary** (3 short paragraphs from the podcast script, ~800-1200 chars)
- **Table of contents** (section titles as bullet list)
- **References** (source URL, plus auto-detected tool/article mentions like Linear, Jira, Anthropic etc.)
- **Channel boilerplate** with subscribe CTA
- **Hashtags** (auto-derived from content tags)

## Video Encoding Specs
- 1920×1080, 2fps, libx264, -tune stillimage, -crf 18
- Audio: AAC copy from source, yuv420p pixels
- ~20s encode for 10 min video, ~7MB

## Troubleshooting

### 403 Insufficient Permission
Token missing `youtube.force-ssl`. Re-auth with that scope (see Caption uploads section).

### Live Streaming Not Enabled
The channel hasn't been enabled for live streaming. This prevents true Première creation (with countdown + live chat). Enable it manually at https://www.youtube.com/features, then wait 24h.

### Caption upload succeeds but doesn't show
- Wait 5-10 min for YouTube processing
- Check YouTube Studio > Subtitles
- SRT must have proper format (index, timestamps, blank lines)
- Note: YouTube auto-generates ASR captions after processing — check existing captions before uploading

### "invalid_grant: Bad Request"
Auth code expired (~10 min) or already used. Get a fresh code.

### Scheduled publish not working for Premiere
- `publishAt` on a non-live video: video goes public at the scheduled time (standard scheduled publish)
- **True Première** (countdown page + live chat): requires channel live streaming enabled + `liveBroadcast` creation + `liveBroadcasts.bind`
- If the channel doesn't have live streaming: use standard scheduled publish, or enable live streaming first

## Automation: Upload Queue & Systemd Timer

### Systemd Timer (automated daily check at midnight Pacific)

A systemd timer runs `upload-queue-checker.py` at **00:00 Pacific** (03:00 EDT / 07:00 UTC) every day.
It refreshes the OAuth token, scans for newly produced videos, checks the upload queue, and uploads
as many as the current day's quota allows.

**Enable / manage:**
```bash
# Enable the timer
systemctl --user daemon-reload
systemctl --user enable --now youtube-upload-queue.timer

# Check status
systemctl --user status youtube-upload-queue.timer
journalctl --user -u youtube-upload-queue.service -f
```

### Upload Queue Script

Located at: `~/Source/private-skills/lecture-pipeline/scripts/upload-queue-checker.py`

**Usage:**
```bash
# Check quota and upload any pending videos
python3 ~/Source/private-skills/lecture-pipeline/scripts/upload-queue-checker.py

# Dry-run: just scan, don't upload
python3 ~/Source/private-skills/lecture-pipeline/scripts/upload-queue-checker.py --dry-run

# Just check quota and channel info
python3 ~/Source/private-skills/lecture-pipeline/scripts/upload-queue-checker.py --quota-only

# Just scan for new videos without uploading
python3 ~/Source/private-skills/lecture-pipeline/scripts/upload-queue-checker.py --check-queue-only
```

**Queue file:** `~/Source/private-skills/lecture-pipeline/upload-queue.jsonl`
- Each line is a JSON entry with: slug, folder, title, video_file, srt_file, tags, status, attempts, last_error
- Status values: `queued` | `uploaded` | `failed`
- Failed videos are retried on the next run (up to quota limits)

### Using from a Pi Agent Session

Just tell the agent:
```
hey, please check how much quota we have right now, and check if there are any videos to publish in the queue over here
```

The agent should run:
```bash
python3 ~/Source/private-skills/lecture-pipeline/scripts/upload-queue-checker.py --quota-only
python3 ~/Source/private-skills/lecture-pipeline/scripts/upload-queue-checker.py --check-queue-only
```

Then if there are videos to upload and quota is available:
```bash
python3 ~/Source/private-skills/lecture-pipeline/scripts/upload-queue-checker.py
```

### Daily Quota Budget

| Metric | Value |
|--------|-------|
| Default daily quota | 10,000 units |
| Cost per video upload (videos.insert) | 1,600 units |
| **Max uploads per day** | **~6 videos** |
| Quota reset time | 00:00 Pacific (07:00 UTC, 03:00 EDT) |

The systemd timer fires at quota reset time so the first run each day gets a full budget.

### Quota Increase

If 6 videos/day is not enough, request a quota increase in Google Cloud Console:
- Go to [YouTube Data API v3 > Quotas](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas)
- Click "Edit Quotas" and request an increase (typically 100k-500k units granted)

## File Locations
- **Videos:** `~/Documents/Lecture/That's Interesting Stuff/<date>_<topic>/output/video-podcast.mp4`
- **Subtitles:** `~/Documents/Lecture/That's Interesting Stuff/<date>_<topic>/audio/podcast.srt`
- **Description:** `~/Documents/Lecture/That's Interesting Stuff/<date>_<topic>/output/youtube-description.txt`
- **Metadata:** `~/Documents/Lecture/That's Interesting Stuff/<date>_<topic>/output/youtube-metadata.json`
- **Credentials:** `~/.config/youtube-credentials.json`
- **Upload Queue:** `~/Source/private-skills/lecture-pipeline/upload-queue.jsonl`
- **Episode Ledger:** `~/Documents/Lecture/episode-ledger.jsonl` (JSONL, one JSON object per line)
  - After upload: update `status` from `"produced"` → `"published"` and add `youtube_url`
  - Find + update: `python3 -c "import json,sys; lines=open(\"~/Documents/Lecture/episode-ledger.jsonl\").read().splitlines(); lines=[json.dumps({**json.loads(l),**{\"status\":\"published\",\"youtube_url\":\"https://youtu.be/XXXXX\"}},ensure_ascii=False) if json.loads(l).get(\"topic_folder\")==\"2026-MM-DD_slug\" else l for l in lines]; open(\"~/Documents/Lecture/episode-ledger.jsonl\",\"w\").write(\"\n\".join(lines)+\"\n\")"`
  - After upload: update the `status` field from `"produced"` → `"published"` and set `youtube_url`
  - Use `jq` or Python to find and update the correct line by `topic_folder`
