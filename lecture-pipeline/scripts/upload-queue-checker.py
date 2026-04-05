#!/usr/bin/env python3
"""upload-queue-checker.py — Check YouTube API quota and process the upload queue.

Usage:
    python3 upload-queue-checker.py [--dry-run] [--upload-max N] [--quota-only]

This script is designed to be called by a systemd timer at midnight Pacific.
It:
  1. Refreshes the YouTube OAuth token
  2. Checks remaining daily quota
  3. Reads the upload queue from the JSONL ledger
  4. Uploads videos (as many as quota allows)
  5. Removes successfully uploaded items from the queue
  6. Prints a summary (for systemd journal / user notification)

Queue file format: ~/Source/private-skills/lecture-pipeline/upload-queue.jsonl
Each line is a JSON object:
  {
    "date": "2025-04-05",
    "slug": "courtesy-to-be-disliked",
    "folder": "/home/nicolas/Documents/Lecture/That's Interesting Stuff/2025-04-05_courage-to-be-disliked",
    "title": "The Courage to Be Disliked",
    "description_file": ".../output/youtube-description.txt",
    "srt_file": ".../audio/podcast.srt",
    "video_file": ".../output/video-podcast.mp4",
    "tags": ["podcast","education","psychology"],
    "status": "queued"        # queued | uploaded | failed
    "video_id": "abc123",     # set after upload
    "youtube_url": "...",     # set after upload
    "attempts": 0,
    "last_error": ""
  }

Upload cost: 1,600 quota units per video.insert call.
Default daily quota: 10,000 units (≈6 videos/day).
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

# ────── Config ──────
QUEUE_FILE = os.path.expanduser(
    "~/Source/private-skills/lecture-pipeline/upload-queue.jsonl"
)
CREDENTIALS_FILE = os.path.expanduser("~/.config/youtube-credentials.json")
LEDGER_FILE = os.path.expanduser(
    "~/Documents/Lecture/episode-ledger.jsonl"
)
LECTURE_DIR = os.path.expanduser(
    "~/Documents/Lecture/That's Interesting Stuff"
)
QUOTA_PER_UPLOAD = 1600
DEFAULT_DAILY_QUOTA = 10000

# ────── Token refresh ──────
def refresh_token() -> str:
    """Return a fresh access_token, updating the credentials file."""
    with open(CREDENTIALS_FILE) as f:
        creds = json.load(f)
    data = urllib.parse.urlencode({
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        tokens = json.loads(resp.read().decode())
    creds["access_token"] = tokens["access_token"]
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds, f, indent=2)
    return tokens["access_token"]


def get_quota_info(token: str) -> dict:
    """Estimate remaining quota from the channels.list call.

    YouTube Data API doesn't expose remaining quota directly,
    but we can verify the token works and the channel is accessible.
    Return channel info.
    """
    url = "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    items = data.get("items", [])
    if not items:
        return {"error": "No channel found"}
    ch = items[0]
    return {
        "title": ch["snippet"]["title"],
        "channel_id": ch["id"],
        "subscriber_count": int(ch.get("statistics", {}).get("subscriberCount", 0)),
        "video_count": int(ch.get("statistics", {}).get("videoCount", 0)),
        "view_count": int(ch.get("statistics", {}).get("viewCount", 0)),
    }


# ────── Queue file helpers ──────
def read_queue() -> list[dict]:
    if not os.path.exists(QUEUE_FILE):
        return []
    items = []
    with open(QUEUE_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def write_queue(items: list[dict]):
    with open(QUEUE_FILE, "w") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def discover_pending() -> list[dict]:
    """Scan the Lecture folder for produced videos NOT yet in the queue."""
    existing_queue = read_queue()
    queued_slugs = {item["slug"] for item in existing_queue}

    pending = []
    if not os.path.isdir(LECTURE_DIR):
        return pending

    for entry in sorted(os.listdir(LECTURE_DIR)):
        folder = os.path.join(LECTURE_DIR, entry)
        if not os.path.isdir(folder):
            continue
        video_file = os.path.join(folder, "output", "video-podcast.mp4")
        if not os.path.isfile(video_file):
            continue

        slug = entry.split("_", 1)[1] if "_" in entry else entry
        if slug in queued_slugs:
            # Already in queue — check if completed
            for item in existing_queue:
                if item["slug"] == slug and item.get("status") == "uploaded":
                    break
            else:
                pass  # still queued
            continue  # skip

        # New video to queue
        srt = os.path.join(folder, "audio", "podcast.srt")
        desc_json = os.path.join(folder, "output", "youtube-metadata.json")

        date_str = entry[:10] if len(entry) >= 10 else ""

        meta = {}
        if os.path.isfile(desc_json):
            with open(desc_json) as f2:
                meta = json.load(f2)

        # Try to read ticktick_sources.json for ticktick_ids
        ticktick_ids = []
        ticktick_count = 0
        sources = []
        src_file = os.path.join(folder, "ticktick_sources.json")
        if os.path.isfile(src_file):
            try:
                src_data = json.load(open(src_file))
                ticktick_ids = [i["id"] for i in src_data.get("items", [])]
                ticktick_count = len(ticktick_ids)
                # Extract up to 5 source URLs
                import re
                seen = set()
                for item in src_data.get("items", []):
                    for m in re.finditer(r'https?://\S+', item.get("content", "")):
                        url = m.group(0).rstrip('.,;:!?)')
                        clean = re.sub(r'[?&](utm_|ref|fbclid|source=).*', '', url)
                        if clean not in seen and len(clean) < 200:
                            seen.add(clean)
                            sources.append(clean)
                            if len(sources) >= 5:
                                break
                    if len(sources) >= 5:
                        break
            except Exception:
                pass

        pending.append({
            "date": date_str.replace("-", ""),
            "slug": slug,
            "folder": folder,
            "topic_folder": topic_folder,
            "title": meta.get("title", src_data.get("title", slug.replace("-", " ").title())) if os.path.isfile(src_file) else meta.get("title", slug.replace("-", " ").title()),
            "description_file": os.path.join(folder, "output", "youtube-description.txt"),
            "srt_file": srt if os.path.isfile(srt) else "",
            "video_file": video_file,
            "tags": meta.get("tags", ["podcast", "education"]),
            "ticktick_ids": ticktick_ids,
            "ticktick_count": ticktick_count,
            "sources": sources,
            "sources_count": len(sources),
            "status": "queued",
            "video_id": "",
            "youtube_url": "",
            "attempts": 0,
            "last_error": "",
        })
    return pending


# ────── Upload ──────
def compute_schedule_slot() -> str:
    """Next 20:00 ET slot at least 2 hours from now, ISO 8601 UTC."""
    import pytz
    et = pytz.timezone("America/Toronto")
    now_et = datetime.datetime.now(et)
    target = now_et.replace(hour=20, minute=0, second=0, microsecond=0)
    if target <= now_et + datetime.timedelta(hours=2):
        target += datetime.timedelta(days=1)
    return target.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def upload_video(token: str, item: dict, dry_run: bool = False) -> tuple[bool, str]:
    """Upload a single video. Returns (success, video_id_or_error)."""
    video_file = item["video_file"]
    if not os.path.isfile(video_file):
        return False, f"Video file missing: {video_file}"

    video_size = os.path.getsize(video_file)
    if dry_run:
        return True, f"dry-run-ok ({video_size / 1024 / 1024:.1f}MB)"

    schedule_time = compute_schedule_slot()

    # Build metadata JSON
    desc_file = item.get("description_file", "")
    if desc_file and os.path.isfile(desc_file):
        with open(desc_file) as f:
            description = f.read()
    else:
        description = item.get("title", "")

    snippet = {
        "title": item["title"],
        "description": description,
        "tags": item["tags"],
        "categoryId": "27",
    }
    status = {
        "privacyStatus": "private",
        "publishAt": schedule_time,
        "selfDeclaredMadeForKids": False,
    }
    metadata_json = json.dumps({"snippet": snippet, "status": status}, ensure_ascii=False)

    # Multipart upload via curl (more reliable than urllib for large files)
    meta_path = "/tmp/yt-upload-meta.json"
    with open(meta_path, "w") as f:
        f.write(metadata_json)

    boundary = f"YTUP{os.getpid()}"
    # Build body file
    body_path = f"/tmp/yt-upload-body-{os.getpid()}"
    with open(body_path, "wb") as f:
        f.write(f"--{boundary}\r\n".encode())
        f.write(b"Content-Type: application/json; charset=UTF-8\r\n\r\n")
        f.write(metadata_json.encode("utf-8"))
        f.write(f"\r\n--{boundary}\r\n".encode())
        f.write(b"Content-Type: video/mp4\r\n\r\n")
        with open(video_file, "rb") as vf:
            f.write(vf.read())
        f.write(f"\r\n--{boundary}--\r\n".encode())

    cmd = [
        "curl", "-s", "-w", "\n%{http_code}",
        "-X", "POST",
        "https://www.googleapis.com/upload/youtube/v3/videos?part=snippet,status",
        "-H", f"Authorization: Bearer {token}",
        "-H", f"Content-Type: multipart/related; boundary={boundary}",
        "-H", "Expect:",
        "--data-binary", f"@{body_path}",
        "--max-time", "3600",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3700)
        http_code = result.stdout.strip().split("\n")[-1]
        response_body = "\n".join(result.stdout.strip().split("\n")[:-1])
        resp = json.loads(response_body)
        if http_code.startswith("2"):
            video_id = resp.get("id", "")
            return True, video_id
        else:
            error_msg = resp.get("error", {}).get("message", response_body[:200])
            return False, f"HTTP {http_code}: {error_msg}"
    except subprocess.TimeoutExpired:
        return False, "Upload timed out after 3600s"
    except Exception as e:
        return False, str(e)
    finally:
        # Cleanup temp files
        for p in [meta_path, body_path]:
            try:
                os.remove(p)
            except OSError:
                pass


# ────── Ledger sync ──────
def update_ledger(item: dict):
    """After successful YouTube upload, update the episode ledger entry.
    
    Finds the entry by topic_folder, sets status="published" and adds youtube_url."""
    entries = []
    if os.path.isfile(LEDGER_FILE):
        with open(LEDGER_FILE) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue  # skip malformed lines

    slug = item.get("slug", "")
    topic_folder = item.get("folder", "").split("/")[-1]  # e.g. "2026-04-05_topic-name"
    
    found = False
    for entry in entries:
        if entry.get("topic_folder") == topic_folder or entry.get("slug") == slug:
            entry["status"] = "published"
            entry["youtube_video_id"] = item.get("video_id", "")
            entry["youtube_url"] = item.get("youtube_url", "")
            found = True
            break

    if not found:
        print(f"  ⚠️  No ledger entry found for {topic_folder} — skipping ledger update")

    with open(LEDGER_FILE, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ────── Main ──────
def main():
    parser = argparse.ArgumentParser(description="YouTube upload queue manager")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually upload")
    parser.add_argument("--quota-only", action="store_true", help="Only check quota")
    parser.add_argument("--upload-max", type=int, default=0,
                        help="Max videos to upload (0 = auto-calc from quota)")
    parser.add_argument("--check-queue-only", action="store_true",
                        help="Just scan for new videos, don't upload")
    args = parser.parse_args()

    print("=" * 60)
    print("🎬 YouTube Upload Queue Checker")
    print("=" * 60)

    # 1. Refresh token
    print("\n🔑 Refreshing YouTube OAuth token...")
    try:
        token = refresh_token()
    except Exception as e:
        print(f"❌ Token refresh failed: {e}")
        sys.exit(1)

    # 2. Check channel / verify auth
    print("📡 Checking channel...")
    try:
        ch = get_quota_info(token)
        print(f"   Channel: {ch['title']}")
        print(f"   Subscribers: {ch['subscriber_count']}")
        print(f"   Video count: {ch['video_count']}")
        print(f"   Total views: {ch['view_count']}")
    except Exception as e:
        print(f"❌ Channel check failed: {e}")
        sys.exit(1)

    if args.quota_only:
        print(f"\n⚠️  Remaining quota cannot be queried via API directly.")
        print(f"   Default daily budget: {DEFAULT_DAILY_QUOTA} units")
        print(f"   Cost per upload: {QUOTA_PER_UPLOAD} units")
        print(f"   Max uploads per day: ~{DEFAULT_DAILY_QUOTA // QUOTA_PER_UPLOAD}")
        print(f"   Quota resets at 00:00 Pacific (07:00 UTC / 03:00 EDT)")
        return

    # 3. Scan for new videos
    print("\n📂 Scanning for produced videos...")
    new_videos = discover_pending()
    queue = read_queue()
    existing_pending = [q for q in queue if q.get("status") in ("queued", "failed")]

    # Merge new videos into queue
    for v in new_videos:
        queue.append(v)

    write_queue(queue)

    all_pending = [q for q in read_queue() if q.get("status") in ("queued", "failed")]

    print(f"   Already in queue: {len(existing_pending)}")
    print(f"   New videos found: {len(new_videos)}")
    print(f"   Total pending: {len(all_pending)}")

    # Show pending list
    if all_pending:
        print(f"\n📋 Upload Queue:")
        for i, item in enumerate(all_pending, 1):
            size_mb = os.path.getsize(item["video_file"]) / 1024 / 1024 if os.path.isfile(item.get("video_file", "")) else 0
            attempts = item.get("attempts", 0)
            err = item.get("last_error", "")
            status_emoji = "🔄" if attempts == 0 else "❌"
            print(f"   {i}. {item['title']} ({size_mb:.0f}MB) [{status_emoji} {attempts} attempts]")
            if err:
                print(f"      Last error: {err[:100]}")

    if args.check_queue_only:
        return

    if not all_pending:
        print("\n✅ No videos pending upload.")
        return

    # 4. Upload videos
    print(f"\n🚀 Starting uploads...")
    uploaded_count = 0
    failed_count = 0

    for item in all_pending:
        size_mb = os.path.getsize(item["video_file"]) / 1024 / 1024 if os.path.isfile(item.get("video_file", "")) else 0
        print(f"\n▶ Uploading: {item['title']} ({size_mb:.0f}MB) [attempt {item.get('attempts', 0) + 1}]")

        success, result = upload_video(token, item, dry_run=args.dry_run)
        item["attempts"] = item.get("attempts", 0) + 1

        if success:
            video_id = result
            uploaded_count += 1
            item["status"] = "uploaded"
            item["video_id"] = video_id
            item["youtube_url"] = f"https://www.youtube.com/watch?v={video_id}"
            print(f"   ✅ Uploaded: https://www.youtube.com/watch?v={video_id}")
            update_ledger(item)

            # Upload SRT if available
            if item.get("srt_file") and os.path.isfile(item["srt_file"]):
                print(f"   📝 Note: SRT captions available for caption upload if needed")
        else:
            failed_count += 1
            item["status"] = "failed"
            item["last_error"] = result
            print(f"   ❌ Failed: {result[:150]}")

            if "uploadLimitExceeded" in result or "quotaExceeded" in result:
                print(f"\n⚠️  Daily upload quota exhausted. Resuming tomorrow at 03:00 EDT.")
                break

        write_queue(read_queue())  # Persist after each upload

    # 5. Summary
    print(f"\n{'=' * 60}")
    print(f"📊 Upload Summary")
    print(f"{'=' * 60}")
    print(f"   Uploaded: {uploaded_count}")
    print(f"   Failed: {failed_count}")
    remaining = [q for q in read_queue() if q.get("status") in ("queued", "failed")]
    print(f"   Still pending: {len(remaining)}")
    if remaining:
        print(f"   Remaining queue:")
        for item in remaining:
            print(f"      - {item['title']} ({item['last_error'][:60] if item.get('last_error') else 'waiting'})")


if __name__ == "__main__":
    main()
