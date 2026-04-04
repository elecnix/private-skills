---
name: transcribe
description: Local audio transcription using faster-whisper and OpenAI summarization. Use when asked to transcribe audio files, generate transcripts, or summarize spoken audio locally.
---

# Transcribe - Local Audio Transcription

Transcribes audio files using [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2) with optional OpenAI summarization.

## Location

`/home/nicolas/Source/personal_utilities.py/transcribe`

## How to Run

```bash
cd /home/nicolas/Source/personal_utilities.py/transcribe
/home/nicolas/openai-whisper/.venv/bin/python3 transcribe.py <audio_file_or_directory>
```

## Features

- Processes single files, directories (recursive), or current directory
- Idempotent: skips files that already have a `.txt` transcript or `.summary.txt`
- Uses VAD (Voice Activity Detection) to skip silence
- Per-file timing and language detection in output

## Configuration (environment variables)

| Variable | Default | Description |
|---|---|---|
| `WHISPER_MODEL` | `turbo` | Model size: tiny, base, small, medium, large-v3, turbo |
| `WHISPER_COMPUTE_TYPE` | `int8` | Quantization: int8, float16, float32 |
| `WHISPER_CPU_THREADS` | `0` (auto) | CPU threads for CTranslate2 |
| `WHISPER_BEAM_SIZE` | `1` | Beam size (1 = greedy, faster) |
| `OPENAI_API_KEY` | — | Required for summarization only |

## Output

- `<filename>.txt` — Full transcription with timestamps
- `<filename>.summary.txt` — AI summary (requires OPENAI_API_KEY)

## Notes

- Instrumental music will produce mostly empty/noise transcripts since Whisper expects speech
- The venv has all dependencies pre-installed — no `uv sync` needed
- Works offline (except summarization which calls OpenAI API)
