#!/usr/bin/env python3
import sys, os, re

def normalize_text(text):
    # Remove markdown headers
    text = re.sub(r'^#+ .*$', '', text, flags=re.MULTILINE)
    # Remove section tags like [Intro], [Section 1]
    text = re.sub(r'^\[.*\]$', '', text, flags=re.MULTILINE)
    # Remove metadata lines at the bottom (after ---)
    if '---' in text:
        text = text.split('---')[0]
    # Remove bold/italic markers
    text = text.replace('**', '').replace('*', '').replace('__', '').replace('_', '')
    # Convert single digits to words for better TTS flow
    digit_map = {'0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
                 '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'}
    def replace_digit(match):
        return digit_map[match.group(0)]
    # Only replace isolated digits
    text = re.sub(r'(?<!\d)[0-9](?!\d)', replace_digit, text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def main():
    if len(sys.argv) < 2:
        print("Usage: tts-normalize.py <input.md> [output.txt]")
        print("   or: tts-normalize.py <topic_dir>")
        sys.exit(1)
    
    arg1 = sys.argv[1]
    
    if os.path.isdir(arg1):
        in_path = os.path.join(arg1, "03-podcast-script.md")
        out_path = os.path.join(arg1, "audio", "podcast-ready.txt")
    else:
        in_path = arg1
        out_path = sys.argv[2] if len(sys.argv) > 2 else in_path + ".clean"
    
    if not os.path.exists(in_path):
        print(f"Error: {in_path} not found")
        sys.exit(1)
        
    with open(in_path, 'r') as f:
        content = f.read()
    
    clean_text = normalize_text(content)
    
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        f.write(clean_text)
    
    print(f"Normalized {in_path} -> {out_path}")

if __name__ == "__main__":
    main()
