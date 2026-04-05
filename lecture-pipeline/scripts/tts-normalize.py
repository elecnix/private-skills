#!/usr/bin/env python3
"""tts-normalize.py — Convert 03-podcast-script.md into clean plain text for edge-tts.

Usage: python3 tts-normalize.py <topic_folder>

Pipeline position: Synthesizer  →  Script Processor  →  TTS Producer

What it does:
  1. Extracts only the spoken portion of the script (skips metadata header,
     PRODUCTION NOTES block, and section markers including ### and ## headers).
  2. Strips ALL markdown formatting (bold, italic, links, code fences, headers).
  3. Expands patterns that TTS engines mispronounce:
     - O(n)   → "O of n"
     - O(n²)  → "O of n squared"
     - WebAssembly → "Web Assembly"
     - WASM   → "W A S M"
     - ReLU   → "R E L U"
     - C++    → "C plus plus"
     - →      → "becomes"
     - URLs are removed (listener can't hear a link)
     - Long sentences are split to reduce edge-tts timeout risk
  4. Collapses to single-line flow for edge-tts.

Output: {topic_folder}/audio/podcast-ready.txt

This file is what edge-tts receives. NEVER feed 03-podcast-script.md directly.
"""
import sys, os, re


def extract_spoken_portion(text: str) -> str:
    """Extract everything between the first ## section and PRODUCTION NOTES/end."""
    lines = text.split('\n')

    # Skip all metadata before the first ## header
    idx = 0
    in_metadata = True
    content_lines = []

    while idx < len(lines):
        line = lines[idx]

        if in_metadata:
            # Skip everything until we see the first ## section header (Hook or first section)
            if re.match(r'^##\s+\S', line) and not re.search(r'PRODUCTION|NOTES', line, re.IGNORECASE):
                in_metadata = False
            idx += 1
            continue

        # Stop at PRODUCTION NOTES
        if re.match(r'^##\s+PRODUCTION NOTES', line, re.IGNORECASE):
            break

        # Skip --- and blank lines as section separators
        if line.strip() in ('---', ''):
            idx += 1
            continue

        # Skip ALL markdown headers: ##, ###, ####, etc. (including ### Step Back)
        if re.match(r'^#{2,}\s', line):
            idx += 1
            continue

        content_lines.append(line)
        idx += 1

    return '\n'.join(content_lines)


def strip_markdown(text: str) -> str:
    """Remove all markdown syntax while keeping the text content."""
    # Code fences
    text = re.sub(r'```[a-z]*\n?', '', text)

    # Bold/italic — keep content only
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'\1', text)

    # Links: [text](url) → text only
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Bare URLs → completely removed
    text = re.sub(r'https?://\S+', '', text)

    # Images
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)

    # Remaining # headers (##, ###, #### etc.) that slipped through
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Blockquote markers
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)

    # Horizontal rules
    text = re.sub(r'^[*_-]{3,}\s*$', '', text, flags=re.MULTILINE)

    return text


def expand_for_speech(text: str) -> str:
    """Replace abbreviations and patterns that TTS engines mispronounce."""
    replacements = [
        # Big-O complexity
        (r'\bO\((\w+)\²\)', r'O of \1 squared'),
        (r'\bO\((\w+?)\)', r'O of \1'),
        # Programming languages
        (r'(?<![a-zA-Z])C\+\+(?![a-zA-Z])', 'C plus plus'),
        (r'(?<![a-zA-Z])C#(?![a-zA-Z])', 'C sharp'),
        # WebAssembly
        (r'\bWebAssembly\b', 'Web Assembly'),
        (r'\bWASM\b', 'W A S M'),
        # ReLU
        (r'\bReLU\b', 'R E L U'),
        # Arrows → "becomes"
        (r'→', 'becomes'),
        (r'->', 'becomes'),
        (r'=>', 'becomes'),
        # Common tech acronyms → space them out
    ]

    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)

    # Acronyms: replace with spaced letters
    for acronym in ['AI', 'LLM', 'API', 'CLI', 'SDK', 'GPU', 'CPU', 'RAM',
                    'OS', 'CSS', 'HTTP', 'URL', 'UI', 'UX', 'ML', 'NLP',
                    'MCP', 'VM', 'KV', 'SRT', 'MP3', 'MP4', 'PNG', 'JPG',
                    'JSON', 'CI', 'CD', 'DOM', 'TLS', 'DNS', 'SSH', 'FTP',
                    'IDE', 'OOP', 'AGI', 'HTML', 'LL', 'Re', 'GL', 'U']:
        # Use word boundaries but handle acronyms at sentence boundaries
        text = re.sub(r'\b' + acronym + r'(?=[.,;:\s\)])', ' '.join(acronym), text)

    return text


def split_long_sentences(text: str, max_words=30) -> str:
    """Split very long sentences to reduce edge-tts timeout risk."""
    sentences = re.split(r'(?<=[\.\!\?\n])\s+', text)
    result = []
    for sentence in sentences:
        words = sentence.split()
        if len(words) <= max_words:
            result.append(sentence)
        else:
            # Split at natural break points: commas, em-dashes, "and", "but"
            # Try splitting at comma or em-dash first
            for sep in [' — ', ', ', ' —', ',']:
                parts = sentence.split(sep)
                if len(parts) > 1:
                    # Check if any part is still too long
                    still_long = [p for p in parts if len(p.split()) > max_words]
                    if not still_long:
                        break
            # Join the split parts with periods to make separate "sentences"
            result.append(sep.join(parts))

    return ' '.join(result)


def main():
    if len(sys.argv) < 2:
        print("Usage: tts-normalize.py <topic_folder_or_script_path>")
        sys.exit(1)

    arg = sys.argv[1]

    if os.path.isdir(arg):
        input_path = os.path.join(arg, '03-podcast-script.md')
    else:
        input_path = arg

    if not os.path.isfile(input_path):
        print(f"Error: {input_path} not found")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Step 1: extract spoken portion (skip metadata, ### headers, etc.)
    text = extract_spoken_portion(text)

    # Step 2: strip markdown  
    text = strip_markdown(text)

    # Step 3: expand for speech
    text = expand_for_speech(text)

    # Step 4: split long sentences
    text = split_long_sentences(text)

    # Step 5: collapse to single line
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove double spaces
    text = re.sub(r' {2,}', ' ', text)

    # Safety check: reject if too short
    word_count = len(text.split())
    if word_count < 200:
        print(f"  WARNING: Only {word_count} words. Check script structure.")
        sys.exit(1)

    # Output
    if os.path.isdir(arg):
        output_path = os.path.join(arg, 'audio', 'podcast-ready.txt')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    else:
        output_path = os.path.splitext(input_path)[0] + '-clean.txt'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"  Normalized: {word_count} words")
    print(f"  Output: {output_path}")
    print(f"  Preview: {text[:200]}...")


if __name__ == "__main__":
    main()
