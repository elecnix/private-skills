---
name: craft
description: Access and manage Craft.do documents, pages, blocks, and collections via MCP or REST API. Use when creating, reading, updating, or organizing Craft documents from the command line. Requires the Craft CLI or a Craft MCP URL.
license: MIT
metadata:
  author: elecnix
  version: "1.2"
  mcporter: "https://github.com/steipete/mcporter"
---

# Craft CLI & MCP Integration

## REST API (for file uploads)

**API Docs:** https://connect.craft.do/api-docs/space  
**Full reference:** `/home/nicolas/Téléchargements/instructions_to_agent.md`

### Uploading files (PDF, PNG, JPG)

The REST API supports uploading files via `POST /upload`. **Note:** The API currently returns a generic `[File](url)` block — filename metadata is not preserved.

**Direct upload:**
```bash
curl -X POST "https://connect.craft.do/links/{LINK_ID}/api/v1/upload?pageId=DOC_ID&position=end" \
  -H "Content-Type: application/pdf" \
  --data-binary "@/path/to/file.pdf"
```

**For documents with personal/sensitive data**, reference the local file path instead:
```markdown
📄 **2026-03-05 Facture Urgence Dentaire Montréal.pdf** — ~/Documents/Santé/Nicolas/Dentiste/
```

> ⚠️ **NE JAMAIS** utiliser des services publics d'hébergement (0x0.st, transfer.sh, etc.) pour des documents personnels ou sensibles (factures médicales, relevés, etc.)

Interact with Craft.do documents via MCP (Model Context Protocol).

## Step 1: Check if Craft CLI is already installed and authenticated

Before generating anything, check if the user already has a working `craft` CLI:

```bash
# Check if craft binary exists
which craft 2>/dev/null || ls ~/.local/bin/craft 2>/dev/null

# Test if it's authenticated by running a simple command
craft folders-list 2>&1 | head -5
```

If `craft` exists and `folders-list` returns data (not an auth error), **skip to Step 3** — the CLI is already set up and ready to use.

## Step 2: Get the Craft MCP URL and generate CLI

Only if the CLI is not installed or not authenticated:

1. Open Craft and navigate to: **Settings → Documents → MCP**
   - Or visit directly: https://www.craft.do/settings/documents/mcp
2. Find the MCP server URL (it looks like: `https://mcp.craft.do/links/XXXXX/mcp`)
3. Copy this URL — it contains a unique token for authentication

> **Note:** Each user has their own personal MCP URL. Do not share or commit this URL.

### Generate the CLI Binary

Use [MCPorter](https://github.com/steipete/mcporter) to compile a standalone binary:

```bash
npx mcporter generate-cli \
  --name craft \
  --compile \
  --server <CRAFT_MCP_URL>
```

Replace `<CRAFT_MCP_URL>` with the user's actual Craft MCP URL.

This produces a native `craft` binary — no runtime dependencies, no Node.js needed. The binary starts instantly.

### Fallback: TypeScript (if Bun unavailable)

If Bun is not installed, generate TypeScript instead:

```bash
npx mcporter generate-cli \
  --name craft \
  --server <CRAFT_MCP_URL>
```

Then run with:
```bash
# Install deps once
npm init -y && npm install commander mcporter

# Run
npx tsx craft.ts --help
```

## Step 3: Use the Craft CLI

The CLI provides subcommands for all Craft MCP tools:

```bash
# List all available commands
./craft --help

# List all folders
./craft folders-list

# List documents in a folder
./craft documents-list --folder-ids <FOLDER_ID>

# Get content of a document/block
./craft blocks-get --id <BLOCK_ID>

# Delete documents
./craft documents-delete --document-ids <DOC_ID>
```

### Output formats

Add `-o json` or `-o raw` for machine-readable output:
```bash
./craft folders-list -o json
```

## Step 3b: Fetching Content from a Craft URL

When you have a Craft URL (e.g., from a user sharing a document), you can extract the block ID and fetch its content.

### Craft URL Structure

A Craft URL follows this pattern:
```
https://docs.craft.do/editor/d/SPACE_ID/DOC_ID/b/BLOCK_ID/Title?params
```

| Component | Example | Description |
|-----------|---------|-------------|
| `SPACE_ID` | `54188a37-75f4-a51f-a51d-3e369c84604f` | Your Craft space |
| `DOC_ID` | `49b93297-9824-4371-9b58-d5ee346d5320` | The parent document |
| `BLOCK_ID` | `4744244A-1952-4885-8EF8-18827612475A` | **The page block** — use this to fetch |
| `Title` | `Displaying-unmatched-transactions` | Display only, not needed |
| `?s=...` | `TLaYNDrvEs3q...` | Share session token (not needed) |

### Extract the Block ID

The block ID is the UUID after `/b/` and before the title:
```
.../b/4744244A-1952-4885-8EF8-18827612475A/Title
```

### Fetch Content

```bash
# Extract block ID and fetch in one step
BLOCK_ID=$(echo "https://docs.craft.do/editor/d/.../b/BLOCK_ID/Title" | grep -oP '(?<=/b/)[A-Fa-f0-9-]+')
craft blocks-get --id "$BLOCK_ID" -o markdown
```

### Output Formats

```bash
-o markdown    # Rendered markdown (best for reading)
-o json        # Raw JSON with all block metadata
-o raw         # Raw output
```

### Example

```bash
# From a real URL
craft blocks-get --id 4744244A-1952-4885-8EF8-18827612475A -o markdown
```

Returns the page title and all content blocks as markdown.

---

## Step 4: Write operations via mcporter call

**The generated CLI has limitations with complex arguments** (e.g., `documents_create` expects objects but CLI passes strings). For write operations, use `mcporter call` directly with the MCP URL:

```bash
# Get the MCP URL from the config
cat ~/.codeium/windsurf/mcp_config.json | jq '.mcpServers["Craft (write)"].serverUrl'

# Create a document
mcporter call 'https://mcp.craft.do/links/XXXXX/mcp.documents_create' \
  documents='[{"title":"My New Document"}]'

# Add markdown content to a document
mcporter call 'https://mcp.craft.do/links/XXXXX/mcp.markdown_add' \
  pageId='<DOCUMENT_ID>' \
  position=end \
  markdown='# Hello World

This is my content.'

# Move a document to a folder
mcporter call 'https://mcp.craft.do/links/XXXXX/mcp.documents_move' \
  documentIds='["<DOC_ID>"]' \
  destination='{"folderId":"<FOLDER_ID>"}'
```

> **Tip:** The Craft CLI is excellent for read operations. For mutations, prefer `mcporter call` with the MCP URL.

## Step 5: Install Globally (Optional)

```bash
# Move to a directory in PATH
sudo mv craft /usr/local/bin/

# Or create a symlink
ln -s $(pwd)/craft ~/.local/bin/craft
```

Now use `craft` from anywhere:
```bash
craft folders-list
craft documents-list --location unsorted
```

## Troubleshooting

### Bun not found
Install Bun first:
```bash
curl -fsSL https://bun.sh/install | bash
```
Then retry the `--compile` command.

### Authentication errors
- Ensure the MCP URL is current and not expired
- Regenerate the URL in Craft settings if needed

### CLI write operations fail
Use `mcporter call` with the full MCP URL instead (see Step 4).

## References

- [MCPorter](https://github.com/steipete/mcporter) — MCP CLI generator
- [Craft MCP Documentation](https://www.craft.do/fr/imagine/guide/mcp/mcp) — Official Craft MCP guide
