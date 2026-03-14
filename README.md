# Private Skills

Personal [Agent Skills](https://agentskills.io) for use with [Pi](https://github.com/badlogic/pi-coding-agent).

## Skills

| Skill | Description |
|-------|-------------|
| [tangerine-download](skills/tangerine-download/) | Download Tangerine bank transaction exports and organize them into finance folders |

## Usage

Add this repo's `skills/` directory to your Pi settings:

```json
{
  "skills": ["~/Source/private-skills/skills"]
}
```

Or use it from the CLI:

```bash
pi --skill ~/Source/private-skills/skills/tangerine-download
```

## License

Private — not for redistribution.
