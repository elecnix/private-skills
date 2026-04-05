#!/usr/bin/env python3
"""shift-srt.py — Add N seconds to every timestamp in an SRT file.
Usage: shift-srt.py <srt_file> <seconds_to_add>
"""
import sys

def srt2secs(t):
    h, m, rest = t.strip().split(':')
    s, ms = rest.replace(',', '.').split('.')
    return int(h)*3600 + int(m)*60 + float(s) + float('0.'+ms)

def secs2srt(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace('.', ',')

if __name__ == "__main__":
    path = sys.argv[1]
    offset = float(sys.argv[2])
    with open(path) as f:
        content = f.read()
    blocks = content.strip().split('\n\n')
    shifted = []
    for b in blocks:
        lines = b.strip().split('\n')
        if len(lines) < 3:
            continue
        times = lines[1].split(' --> ')
        s1 = srt2secs(times[0]) + offset
        s2 = srt2secs(times[1]) + offset
        lines[1] = f"{secs2srt(s1)} --> {secs2srt(s2)}"
        shifted.append('\n'.join(lines))
    with open(path, 'w') as f:
        f.write('\n\n'.join(shifted) + '\n')
    print(len(shifted))
