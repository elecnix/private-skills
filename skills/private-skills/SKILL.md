---
name: private-skills
description: Guide for creating, organizing, and managing private skills stored in ~/.agents/skills/. Use when setting up new skills, organizing skill collections, backing up skills, or troubleshooting skill discovery issues.
license: MIT
compatibility: Works with any agent that supports the Agent Skills standard (pi-coding-agent, Claude Code, GitHub Copilot).
metadata:
  version: "1.0"
  author: nicolas
---

# Private Skills Management

A guide to creating, organizing, and maintaining private skills stored locally.

## What Are Private Skills?

Private skills are custom skills stored in your local directory rather than published to a public repository. They're perfect for:

- Personal workflows and automations
- Proprietary or sensitive integrations
- Rapid prototyping before sharing publicly
- Skills tailored to your specific environment

## Directory Structure

```
skill-name/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
└── assets/           # Optional: templates, resources
```

Skills are stored in:
- `~/.agents/skills/` (primary location)
- `~/.pi/agent/skills/`

## Creating a New Private Skill

> ⚠️ **Important:** Create skills in your source repo, not directly in `~/.agents/skills/`. Use symlinks to activate.

### 1. Create the Directory (in source repo)

```bash
# Skills live in ~/Source/private-skills/skills/
mkdir -p ~/Source/private-skills/skills/my-private-skill
```

### 2. Write the SKILL.md

```bash
# Edit in the source repo
cat > ~/Source/private-skills/skills/my-private-skill/SKILL.md << 'EOF'
---
name: my-private-skill
description: A brief description of what it does and when to use it.
---

# My Private Skill

Detailed instructions...
EOF
```

### 3. Symlink to Activate

```bash
ln -s ~/Source/private-skills/skills/my-private-skill ~/.agents/skills/my-private-skill
```

```markdown
---
name: my-private-skill
description: A brief description of what this skill does and when to use it.
---

# My Private Skill

Detailed instructions for the skill...
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier (lowercase, numbers, hyphens only) |
| `description` | Yes | What it does AND when to use it (1-1024 chars) |
| `license` | No | License name or reference |
| `compatibility` | No | Environment requirements |
| `metadata` | No | Arbitrary key-value pairs |
| `allowed-tools` | No | Pre-approved tools (experimental) |

### Skill Content Structure

Organize your SKILL.md with these sections:

1. **Header**: Clear title and purpose
2. **Prerequisites**: What the user/system needs
3. **Usage**: How to invoke the skill
4. **Commands**: Step-by-step instructions
5. **Examples**: Concrete usage examples
6. **Troubleshooting**: Common issues and solutions

## Symlinking Skills for Local Development

When developing skills from a git repository, use symlinks to avoid copying files and enable easy updates.

### Symlink This Skill

```bash
mkdir -p ~/.agents/skills
ln -s ~/Source/private-skills/skills/private-skills ~/.agents/skills/private-skills
```

This creates: `~/.agents/skills/private-skills` → `~/Source/private-skills/skills/private-skills`

### Symlink a New Private Skill

```bash
# Create in source repo first, then symlink
ln -s ~/Source/private-skills/skills/my-new-skill ~/.agents/skills/my-new-skill
```

### Verify Symlinks

```bash
# Check symlink exists
ls -la ~/.agents/skills/

# Verify it points to correct location
readlink ~/.agents/skills/private-skills
```

### Remove a Symlink

```bash
rm ~/.agents/skills/private-skills
```

> Note: Use `rm`, not `rm -rf`. The `-rf` flag would delete the target directory if the symlink has trailing slashes or is misinterpreted.

### Workflow: Develop → Deploy

1. **Develop**: Edit files in your repo (e.g., `~/Source/my-skill/skills/my-skill/`)
2. **Symlink**: `ln -s ~/Source/my-skill/skills/my-skill ~/.agents/skills/my-skill`
3. **Test**: Changes are immediately visible (no copy needed)
4. **Commit**: Push from your repo as usual

## Organizing Skills

### Discovery

Skills in `~/.agents/skills/` are automatically discovered.

### Organization Tips

- **Group by domain**: `email/`, `devops/`, `personal/`
- **Use clear names**: `github-pr-review` not `gh-pr`
- **Add reference files**: For complex documentation

### Standard Repo Structure

The default location for private skills is `~/Source/private-skills/`:

```
~/Source/private-skills/
├── skills/
│   ├── skill-one/
│   │   └── SKILL.md
│   └── skill-two/
│       └── SKILL.md
└── README.md
```

Symlink skills to activate:

```bash
ln -s ~/Source/private-skills/skills/skill-one ~/.agents/skills/skill-one
ln -s ~/Source/private-skills/skills/skill-two ~/.agents/skills/skill-two
```

## Progressive Disclosure

Structure skills for efficient context use:

1. **Metadata** (~100 tokens): `name` and `description` loaded at startup
2. **Instructions** (<5000 tokens): Full `SKILL.md` loaded on activation
3. **Resources**: Files in `scripts/`, `references/`, `assets/` loaded on demand

Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files.

## File References

When referencing other files, use relative paths:

```markdown
See [the reference guide](references/REFERENCE.md) for details.

Run the extraction script:
scripts/extract.py
```

## Updating Skills

Edit the `SKILL.md` file directly. For breaking changes, update the version in metadata:

```markdown
---
name: my-private-skill
description: ...
metadata:
  version: "2.0"
---
```

## Sharing Private Skills

### Export

Zip from source repo:

```bash
cd ~/Source/private-skills
zip -r my-private-skill.zip skills/my-private-skill/
```

### Import

```bash
# Extract to source repo, then symlink
unzip my-private-skill.zip -d ~/Source/private-skills/skills/
ln -s ~/Source/private-skills/skills/my-private-skill ~/.agents/skills/my-private-skill
```

### Sync Across Machines

Use a private git repository:

```bash
cd ~/Source/private-skills
git add .
git commit -m "Update skills"
git push backup main
```

## Best Practices

### Keep Skills Focused

- One skill = one purpose
- Split complex workflows into multiple skills that call each other

### Write Clear Instructions

- Use code blocks for commands
- Include expected outputs
- Add inline examples

### Maintain Documentation

- Update SKILL.md when commands change
- Keep under 500 lines
- Use reference files for detailed docs

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Skill not found | Check it's in `~/.agents/skills/` |
| Commands fail | Verify paths and prerequisites |
| Outdated instructions | Update from backup or edit manually |

## Quick Reference

```bash
# 1. Create in source repo
mkdir -p ~/Source/private-skills/skills/my-skill
cat > ~/Source/private-skills/skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: What this skill does
---

# My Skill
EOF

# 2. Symlink to activate
ln -s ~/Source/private-skills/skills/my-skill ~/.agents/skills/my-skill

# List all skills (shows symlinks)
ls -la ~/.agents/skills/

# Verify symlink points to source
readlink ~/.agents/skills/my-skill

# Remove symlink (use rm, not rm -rf)
rm ~/.agents/skills/my-skill
```
