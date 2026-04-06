#!/usr/bin/env python3
import sys, re, os
from datetime import datetime, timedelta

def shift_timestamp(ts, offset_secs):
    # SRT format: 00:00:00,000
    fmt = "%H:%M:%S,%f"
    # Replace , with . for datetime parsing
    ts_dot = ts.replace(',', '.')
    t = datetime.strptime(ts_dot, "%H:%M:%S.%f")
    t_shifted = t + timedelta(seconds=offset_secs)
    return t_shifted.strftime("%H:%M:%S,") + "{:03d}".format(t_shifted.microsecond // 1000)

def main():
    if len(sys.argv) < 3:
        print("Usage: shift-srt.py <file.srt> <offset_secs>")
        sys.exit(1)
    
    path = sys.argv[1]
    offset = float(sys.argv[2])
    
    if not os.path.exists(path):
        print(f"Error: {path} not found")
        sys.exit(1)
        
    with open(path, 'r') as f:
        content = f.read()
    
    # Use regex to find timestamps: 00:00:15,123 --> 00:00:18,456
    pattern = r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})'
    
    def repl(match):
        start = shift_timestamp(match.group(1), offset)
        end = shift_timestamp(match.group(2), offset)
        return f"{start} --> {end}"
        
    new_content = re.sub(pattern, repl, content)
    
    with open(path, 'w') as f:
        f.write(new_content)
        
if __name__ == "__main__":
    main()
