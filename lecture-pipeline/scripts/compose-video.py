#!/usr/bin/env python3
"""compose-video.py — Compose podcast video from audio + SRT + visual cards.

Usage: python3 compose-video.py <topic_folder>

Uses a symlink to avoid ffmpeg path issues with spaces/apostrophes.
All ffmpeg paths are relative to the symlink dir.
"""
import sys, os, json, re, subprocess, tempfile, shutil

def srt_to_secs(ts):
    p = ts.split(':')
    s, ms = p[2].split(',')
    return int(p[0])*3600 + int(p[1])*60 + int(s) + int(ms)/1000

def parse_srt(path):
    with open(path) as f:
        lines = f.readlines()
    subs = []
    i = 0
    while i < len(lines) - 2:
        try:
            if ' --> ' not in lines[i+1]:
                i += 1
                continue
            start = srt_to_secs(lines[i+1].strip().split(' --> ')[0])
            subs.append({'start': start, 'text': lines[i+2].strip()})
            i += 4
        except:
            i += 1
    return subs

def match_sections(timeline, subs):
    """Match section keywords to SRT and compute timings.
    Returns the timeline with 'start', 'end', 'dur' computed."""
    print("=== Matching Sections to SRT ===")
    total = subs[-1]['start'] + 10 if subs else 600

    for idx, sec in enumerate(timeline['sections']):
        found = None
        match_text = ''
        kws = sec.get('keyword', sec.get('id', '')).split('|')
        for pat in kws:
            for s in subs:
                if re.search(pat, s['text'], re.IGNORECASE):
                    found = s['start']
                    match_text = s['text'][:60]
                    break
            if found: break

        sec['start'] = found if found is not None else (0 if idx == 0 else None)
        if match_text:
            print(f"  {sec['id']}: {found:.1f}s — '{match_text}'...")
        else:
            print(f"  {sec['id']}: NOT MATCHED (keywords: {sec.get('keyword', '')})")

    # Calculate durations
    for idx, sec in enumerate(timeline['sections']):
        if sec['start'] is None:
            sec['start'] = 0
        nxt = timeline['sections'][idx+1]['start'] if idx+1 < len(timeline['sections']) else total
        if nxt is None: nxt = total
        sec['end'] = nxt
        sec['dur'] = nxt - sec['start']
        print(f"    → {sec['start']:.1f}s — {sec['end']:.1f}s ({sec['dur']:.1f}s)")

    return timeline

def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    d = os.path.realpath(d)
    if not os.path.isdir(d):
        print(f"Error: not found: {d}"); sys.exit(1)

    print(f"=== Video Composition: {d} ===")

    srt_path = os.path.join(d, "audio", "podcast.srt")
    subs = parse_srt(srt_path)
    print(f"  Parsed {len(subs)} SRT entries")

    with open(os.path.join(d, "visuals", "timeline.json")) as f:
        timeline = json.load(f)

    timeline = match_sections(timeline, subs)

    with open(os.path.join(d, "visuals", "synced-timeline.json"), 'w') as f:
        json.dump(timeline, f, indent=2)

    # Symlink to clean path to avoid ffmpeg path issues with spaces/apostrophes
    workdir = tempfile.mkdtemp(prefix='lecture_')
    link = os.path.join(workdir, 't')
    os.symlink(d, link)

    # Build concat file with RELATIVE paths (from inside the symlink dir)
    concat = os.path.join(link, "video-list.txt")
    with open(concat, 'w') as f:
        for sec in timeline['sections']:
            visuals = sec.get('visuals', [sec.get('visual', '')])
            if isinstance(visuals, str): visuals = [visuals]
            valid = [v for v in visuals if v]
            n = len(valid)
            dur = sec['dur'] / n if n > 0 else sec['dur']
            for vi, v in enumerate(valid):
                rel = os.path.relpath(v, d) if os.path.isabs(v) else v
                f.write("file '{}'\n".format(rel))
                f.write("duration {:.1f}\n".format(dur))
                if vi == n - 1:
                    f.write("file '{}'\n".format(rel))
                    f.write("duration 0.5\n")

    os.makedirs(os.path.join(link, "output"), exist_ok=True)

    # Run ffmpeg from symlink dir with all relative paths
    filter_str = "fps=2,subtitles='audio/podcast.srt':force_style='FontSize=14'"
    cmd = ["ffmpeg","-y","-f","concat","-safe","0","-i","video-list.txt",
           "-i","audio/podcast.mp3","-vf",filter_str,
           "-c:v","libx264","-preset","fast","-tune","stillimage","-crf","18",
           "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",
           "output/video-podcast.mp4"]

    print("=== Composing Video ===")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=link)

    lines = result.stderr.strip().split('\n')
    for line in lines[-6:]:
        print(f"  {line}")

    ok = result.returncode == 0 and os.path.exists(os.path.join(link, "output", "video-podcast.mp4"))

    if ok:
        src = os.path.join(link, "output", "video-podcast.mp4")
        out = os.path.join(d, "output", "video-podcast.mp4")
        os.makedirs(os.path.join(d, "output"), exist_ok=True)
        # src and out may be the same file if d and link resolve to the same path
        if os.path.realpath(src) != os.path.realpath(out):
            shutil.copy2(src, out)
        sz = os.path.getsize(out) / (1024*1024)
        r2 = subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration",
                             "-of","default=noprint_wrappers=1:nokey=1", out],
                            capture_output=True, text=True)
        dur = float(r2.stdout.strip()) if r2.stdout else 0
        print(f"\n  ✓ Success! {sz:.1f}MB, {int(dur/60)}:{int(dur%60):02d}")
        print(f"  {out}")
    else:
        print(f"\n  ✗ Failed (exit {result.returncode})")
        if result.stderr:
            print(f"  {result.stderr[-500:]}")

    shutil.rmtree(workdir, ignore_errors=True)
    if not ok: sys.exit(1)

if __name__ == "__main__":
    main()
