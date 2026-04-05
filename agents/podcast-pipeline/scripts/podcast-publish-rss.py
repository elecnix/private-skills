#!/usr/bin/env python3
"""
podcast-publish-rss.py - Self-hosted podcast RSS feed generator & publisher

Scans the Lecture topic folders, copies MP3s to the web directory,
and generates a fully iTunes/Apple Podcasts-compatible RSS feed.

Usage:
    podcast-publish-rss.py --regenerate    Regenerate feed from all episodes
    podcast-publish-rss.py <topic_folder>  Add one episode & regenerate
"""
import os
import sys
import json
import subprocess
import shutil
import re
from datetime import datetime, timezone

# ─── Configuration ───
LECTURE_ROOT = "/home/nicolas/Documents/Lecture/That's Interesting Stuff"
PODCAST_BASE = "/home/nicolas/Documents/Site Web/synology/nicolas.marchildon.net/interesting/podcast"
EPISODES_DIR = os.path.join(PODCAST_BASE, "episodes")
IMAGES_DIR = os.path.join(PODCAST_BASE, "images")
CONFIG_FILE = "/home/nicolas/Source/private-skills/lecture-pipeline/podcast-config.json"

with open(CONFIG_FILE) as f:
    CFG = json.load(f)


def ensure_dirs():
    os.makedirs(EPISODES_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    # Copy cover art if not present
    cover_src = os.path.join(LECTURE_ROOT, "assets", "cover-nano-v1.png")
    cover_dst = os.path.join(IMAGES_DIR, "cover.png")
    if os.path.exists(cover_src) and not os.path.exists(cover_dst):
        shutil.copy2(cover_src, cover_dst)
        print(f"  ✅ Copied cover art → {os.path.basename(cover_dst)}")


def get_audio_info(mp3_path):
    """Get duration (seconds) and file size from MP3."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration,size",
             "-of", "json", mp3_path],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        fmt = data.get("format", {})
        duration = float(fmt.get("duration", 0))
        size = int(fmt.get("size", 0))
        return duration, size
    except:
        return 0, 0


def secs_to_hhmmss(secs):
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def xml_esc(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;").replace("'", "&apos;"))


def load_ticktick_sources(folder_path):
    """Load TickTick source tasks from podcast-episode.json if it exists."""
    ep_path = os.path.join(folder_path, "podcast-episode.json")
    if os.path.exists(ep_path):
        with open(ep_path) as f:
            data = json.load(f)
            return data.get("ticktick_sources", [])
    return []


def discover_episodes():
    """Scan lecture topic folders and extract episode metadata."""
    episodes = []

    for entry in sorted(os.listdir(LECTURE_ROOT)):
        folder_path = os.path.join(LECTURE_ROOT, entry)
        if not os.path.isdir(folder_path):
            continue

        audio_path = os.path.join(folder_path, "audio", "podcast.mp3")
        if not os.path.exists(audio_path):
            continue

        duration, size = get_audio_info(audio_path)
        if duration == 0:
            print(f"  ⚠️  Skipping {entry}: could not read audio metadata")
            continue

        # Extract title from youtube-metadata.json if available
        title = ""
        meta_path = os.path.join(folder_path, "output", "youtube-metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
                title = meta.get("title", "")

        # Fallback: derive title from folder name
        if not title:
            # "2026-04-05_autonomous-ai-agents" → "Autonomous AI Agents"
            parts = entry.split("_", 1)
            if len(parts) > 1:
                title = parts[1].replace("-", " ").title()
            else:
                title = entry.replace("-", " ").title()

        # Slug for URL
        slug = title.lower().replace(" ", "-").replace("'", "")
        # Only keep alphanumeric and dashes
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        slug = re.sub(r'-+', '-', slug)

        # Description from 00-briefing.md overview
        desc = ""
        brief_path = os.path.join(folder_path, "00-briefing.md")
        if os.path.exists(brief_path):
            with open(brief_path) as f:
                content = f.read()
                m = re.search(r'## Overview\n(.+?)(?:\n##|\Z)', content, re.DOTALL)
                if m:
                    desc = m.group(1).strip().replace('\n', ' ')[:250]

        # Date from folder name
        date_str = entry[:10]  # "2026-04-05"

        # Parse date for publish time
        pub_date = datetime.strptime(date_str, "%Y-%m-%d")

        episodes.append({
            "id": slug,
            "title": title,
            "description": desc or CFG["short_description"],
            "date": date_str,
            "pub_date": pub_date,
            "duration": duration,
            "size": size,
            "slug": slug,
            "folder": folder_path,
            "audio_src": audio_path,
            "ticktick_sources": load_ticktick_sources(folder_path),
        })

    # Sort by date descending (newest first) for RSS item order
    episodes.sort(key=lambda e: e["date"], reverse=True)
    return episodes


def copy_episode(ep):
    """Copy episode MP3 to the podcast episodes directory."""
    dest = os.path.join(EPISODES_DIR, f"{ep['slug']}.mp3")
    if not os.path.exists(dest) or os.path.getsize(dest) != ep["size"]:
        shutil.copy2(ep["audio_src"], dest)
        print(f"  ✅ Copied {ep['title'][:50]} → {ep['slug']}.mp3 ({ep['size'] // 1024}KB)")
        return True
    else:
        print(f"  ⏳ Exists: {ep['slug']}.mp3")
        return False


def generate_rss(episodes):
    """Generate a fully iTunes-compatible Podcast RSS 2.0 feed."""
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    feed_url = CFG["rss_feed_url"]
    podcast_url = CFG["website"]
    cover_url = CFG["cover_art_url"]

    items_xml = ""

    # Reverse order for RSS (newest first) - already sorted desc
    for idx, ep in enumerate(episodes):
        pub_rss = ep["pub_date"].strftime("%a, %d %b %Y 20:00:00 -0400")
        enclosure_url = f"{podcast_url}podcast/episodes/{ep['slug']}.mp3"
        duration_str = secs_to_hhmmss(ep["duration"])
        episode_num = len(episodes) - idx  # 1=oldest, N=newest

        items_xml += f"""    <item>
      <title>{xml_esc(ep['title'])}</title>
      <link>{xml_esc(podcast_url)}</link>
      <description>{xml_esc(ep['description'])}</description>
      <enclosure url="{xml_esc(enclosure_url)}" length="{ep['size']}" type="audio/mpeg" />
      <guid isPermaLink="false">{ep['slug']}</guid>
      <pubDate>{pub_rss}</pubDate>
      <itunes:duration>{duration_str}</itunes:duration>
      <itunes:explicit>{str(CFG['explicit']).lower()}</itunes:explicit>
      <itunes:episode>{episode_num}</itunes:episode>
      <itunes:season>1</itunes:season>
      <itunes:episodeType>full</itunes:episodeType>
    </item>

"""

    cat2 = ""
    if CFG.get("category_2"):
        cat2 = f'\n    <itunes:category text="{xml_esc(CFG["category_2"])}"/>'

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<!--
  {cfg['show_title']} Podcast RSS Feed
  Self-hosted at {xml_esc(feed_url)}
  Generated: {now}
-->
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:atom="http://www.w3.org/2005/Atom"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{xml_esc(cfg['show_title'])}</title>
    <link>{xml_esc(podcast_url)}</link>
    <atom:link href="{xml_esc(feed_url)}" rel="self" type="application/rss+xml"/>
    <description>{xml_esc(cfg['short_description'])}</description>
    <content:encoded><![CDATA[{cfg['long_description']}]]></content:encoded>
    <language>{cfg['language']}</language>
    <copyright>{xml_esc(cfg['copyright'])}</copyright>
    <lastBuildDate>{now}</lastBuildDate>
    <generator>lecture-pipeline / podcast-publish-rss.py</generator>

    <!-- iTunes / Apple Podcasts metadata -->
    <itunes:author>{xml_esc(cfg['owner_name'])}</itunes:author>
    <itunes:summary>{xml_esc(cfg['long_description'])}</itunes:summary>
    <itunes:type>{cfg['episode_type']}</itunes:type>
    <itunes:explicit>{str(cfg['explicit']).lower()}</itunes:explicit>
    <itunes:category text="{xml_esc(cfg['category_1'])}"/>{cat2}
    <itunes:image href="{xml_esc(cover_url)}"/>
    <image>
      <title>{xml_esc(cfg['show_title'])}</title>
      <url>{xml_esc(cover_url)}</url>
      <link>{xml_esc(podcast_url)}</link>
    </image>

    <itunes:owner>
      <itunes:name>{xml_esc(cfg['owner_name'])}</itunes:name>
      <itunes:email>{xml_esc(cfg['owner_email'])}</itunes:email>
    </itunes:owner>

{items_xml}
  </channel>
</rss>
"""
    return feed


def regenerate():
    """Regenerate the full feed from all discovered episodes."""
    print("=== Podcast Feed Regeneration ===\n")
    ensure_dirs()

    episodes = discover_episodes()

    if not episodes:
        print("⚠️  No episodes with valid audio found.")
        return

    print(f"📡 Found {len(episodes)} episodes:\n")

    copied_count = 0
    for ep in episodes:
        if copy_episode(ep):
            copied_count += 1

    # Generate the feed
    feed_xml = generate_rss(episodes)
    feed_path = os.path.join(PODCAST_BASE, "feed.xml")
    with open(feed_path, "w", encoding="utf-8") as f:
        f.write(feed_xml)

    # Save episode database (JSONL for dedup tracking)
    db_path = os.path.join(LECTURE_ROOT, "podcast-episodes.jsonl")
    with open(db_path, "w") as f:
        for ep in episodes:
            rec = {
                "id": ep["id"],
                "title": ep["title"],
                "slug": ep["slug"],
                "date": ep["date"],
                "duration": round(ep["duration"], 1),
                "size": ep["size"],
                "folder": ep["folder"],
                "status": "published",
                "source_ticktick": ep["ticktick_sources"],
            }
            f.write(json.dumps(rec) + "\n")
    print(f"  📄 Database saved: {db_path}")

    # Validate
    try:
        import xml.etree.ElementTree as ET
        ET.parse(feed_path)
        print(f"\n✅ Feed valid: {cfg['rss_feed_url']}")
    except Exception as e:
        print(f"\n❌ XML validation error: {e}")

    print(f"📁 Podcast dir: {PODCAST_BASE}/")
    print(f"\n📋 Submit feed URL to:")
    print(f"   • Spotify for Creators: https://creators.spotify.com/ → RSS feed import")
    print(f"   • Apple Podcasts: https://podcastsconnect.apple.com/")
    print(f"   • Amazon Music: https://podcasters.amazon.dev/")

    return episodes


if __name__ == "__main__":
    if "--regenerate" in sys.argv or "--regen" in sys.argv:
        regenerate()
    else:
        print("Usage: podcast-publish-rss.py --regenerate")
        print("  Scans Lecture folders for audio/podcast.mp3")
        print("  Copies MP3s to web-serving episodes directory")
        print("  Generates iTunes-compatible RSS feed at feed.xml")
