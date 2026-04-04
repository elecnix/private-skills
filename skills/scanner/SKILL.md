---
name: scanner
description: Scan documents using the Epson FF-680W network scanner (WiFi ADF). Triggers scan, runs OCR, auto-renames based on content, and asks user about additional pages and filing location.
---

# Epson FF-680W Scanner Skill

## Scanner details

- **Model:** Epson FF-680W ESC/I-2
- **IP:** 192.168.2.141
- **SANE device:** `epsonds:net:192.168.2.141`
- **Features:** ADF (Automatic Document Feeder), duplex capable

## Quick reference commands

### List available devices
```bash
scanimage -L
```

### Scan a single page (color, 300dpi, PDF)
```bash
scanimage -d 'epsonds:net:192.168.2.141' \
  --source="ADF Front" \
  --mode=Color \
  --resolution=300 \
  --format=pdf \
  -o /tmp/scan_page.pdf
```

### Scan options
| Option | Values | Default |
|--------|--------|---------|
| `--source` | ADF Front, ADF Duplex | ADF Front |
| `--mode` | Lineart, Gray, Color | Color |
| `--resolution` | 50, 75, 100, 150, 200, 240, 300, 360, 400, 600 dpi | 50 |
| `--format` | pnm, tiff, png, jpeg, pdf | pnm |

### Merge multiple PDFs
```bash
pdftk page1.pdf page2.pdf cat output combined.pdf
```

### Convert PDF page to image for OCR/visual inspection
```bash
pdftoppm -png -r 150 -f 1 -l 1 /tmp/scan_page.pdf /tmp/scan_preview
```

### Run OCR on PDF to extract text
```bash
pdftotext /tmp/scan_page.pdf - 2>/dev/null
```

### Extract first page for visual inspection
```bash
pdftoppm -png -r 150 -f 1 -l 1 <combined.pdf> /tmp/inspect
```

## Workflow

### 1. Scan first page
```bash
mkdir -p /tmp/scans
scanimage -d 'epsonds:net:192.168.2.141' \
  --source="ADF Front" \
  --mode=Color \
  --resolution=300 \
  --format=pdf \
  -o /tmp/scans/page1.pdf
```

### 2. Extract text via OCR and read visually
```bash
# Text extraction
pdftotext /tmp/scans/page1.pdf -

# Visual inspection (render first page as image)
pdftoppm -png -r 150 -f 1 -l 1 /tmp/scans/page1.pdf /tmp/scans/preview
```
Then `read` the image at `/tmp/scans/preview-1.png` to visually identify the document.

### 3. Detect person on document
Scan the document visually and via OCR to identify whose document it is.

**Family members:**
| Person | Keywords to look for |
|--------|---------------------|
| Nicolas | MARCHILDON NICOLAS, Nicolas Marchildon, Nicolas |
| Andréanne | ANDRÉANNE (last name may differ), Andréanne |
| Maëva | MARCHILDON MAËVA, Maëva Marchildon, Maëva |
| Coralie | MARCHILDON CORALIE, Coralie Marchildon, Coralie |

**Default:** Nicolas (if no other person detected)

**Detection priority:**
1. Look for "Nom:" or "Patient:" or "Employé:" fields
2. Look for name in address block
3. Look for name anywhere in OCR text

### 4. Generate filename from content
Based on OCR text and visual inspection, generate a filename following the pattern:
```
YYYY-MM-DD Description Type.pdf
```
Examples:
- `2026-03-05 Facture Urgence Dentaire Montréal.pdf`
- `2024-11-15 Reçu Hydro-Québec.pdf`
- `2025-01-20 Attestation médicale Dr Martin.pdf`

**Naming rules:**
- ISO date first (YYYY-MM-DD)
- Space separator
- Capital first letter of each word
- Accents preserved (Montréal, Québec, etc.)
- No underscores, use spaces
- French: "Facture", "Reçu", "Attestation", "Ordonnance"

### 5. Ask about additional pages
After scanning the first page, ask the user:
> "Il y a une autre page dans le feeder ? (oui/non)"

If **oui**, ask where to file:
> "Où voulez-vous classer ce document ? (chemin du dossier)"

If **non**, proceed to filing with the auto-generated name.

### 6. Confirm person and file location
Before moving the file, confirm with the user:
> "Document pour [PERSON]. Je le mets dans [DESTINATION]. C'est correct ?"

If the person was misidentified, the user will correct it.

### 7. Scan additional pages (if any)
```bash
scanimage -d 'epsonds:net:192.168.2.141' \
  --source="ADF Front" \
  --mode=Color \
  --resolution=300 \
  --format=pdf \
  -o /tmp/scans/page2.pdf
```

### 8. Merge all pages
```bash
pdftk /tmp/scans/page*.pdf cat output /tmp/scans/combined.pdf
```

### 9. Move to final location
```bash
mkdir -p "<destination_folder>"
mv /tmp/scans/combined.pdf "<destination_folder>/<filename>.pdf"
```

### 10. Cleanup
```bash
rm -rf /tmp/scans/
```

## Person-based filing paths

**Replace `[PERSON]` with detected person's name folder:**

| Person | Folder name |
|--------|-------------|
| Nicolas | `Nicolas` |
| Andréanne | `Andréanne` |
| Maëva | `Maëva` |
| Coralie | `Coralie` |

## Default filing locations by person

| Document type | Path |
|--------------|------|
| Dental | `~/Documents/Santé/[PERSON]/Dentiste/` |
| Medical | `~/Documents/Santé/[PERSON]/` |
| Health general | `~/Documents/Santé/[PERSON]/` |
| Insurance | `~/Documents/Assurance/` |
| Receipts | `~/Documents/Reçus/` |
| Relevé 27 (government payments) | `~/Documents/Finances/Déclaration de revenus/YYYY/[PERSON]/` |
| T4 (employment income) | `~/Documents/Finances/Déclaration de revenus/YYYY/[PERSON]/` |
| Relevés (tax slips: RL-1, RL-2, etc.) | `~/Documents/Finances/Déclaration de revenus/YYYY/[PERSON]/` |
| General | `~/Documents/[PERSON]/` |

**Example routing:**
- Document for Nicolas → `~/Documents/Santé/Nicolas/Dentiste/`
- Document for Maëva → `~/Documents/Santé/Maëva/`
- T4 for Andréanne → `~/Documents/Finances/Déclaration de revenus/2025/Andréanne/`

## Error handling

- If scanner not found, check WiFi connection and try `scanimage -L`
- If PDF merge fails, ensure `pdftk` is installed: `sudo apt install pdftk-java`
- If OCR yields no text, rely on visual inspection via `pdftoppm` + `read`
