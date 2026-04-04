---
name: rogersbank-download
description: Download Rogers Bank credit card transactions via authenticated Chrome session. Checks existing files, re-downloads only the latest month (catches backdated) plus any new ones. Saves as YYYY-MM.csv + annual CSV.
metadata:
  version: "2.0"
  author: nicolas
---

# Rogers Bank Transaction Download

Download transactions from Rogers Bank via Chrome CDP and the built-in CSV export.

## Prerequisites

1. Chrome browser with remote debugging enabled
2. User logged in at `https://selfserve.rogersbank.com/home`
   (Login: `https://rbaccess.rogersbank.com/?product=ROGERSBRAND&locale=fr_CA`)
3. Chrome CDP skill available
4. Target folder:
   `/home/nicolas/Documents/Finances/Cartes de crédit/MasterCard Rogers Fido 5899/`
   (Card changed 5899 → 5047; folder name preserved.)

## Download Mechanism

**URL:** `https://selfserve.rogersbank.com/transactions`

| Element | Selector | Notes |
|---------|----------|-------|
| Open modal | `click [aria-label="Download transactions"]` | EN; for FR use `[aria-label="Télécharger les opérations"]` |
| Month selector | `document.getElementById("month-select")` | Standard `<select>` element |
| Download button | `document.querySelectorAll("button")[4]` | Or find by innerText "Download" / "Télécharger" |

Underlying API:
```
GET /corebank/v1/account/000002611/customer/000331803/activity?cycleStartDate=YYYY-MM
```
The browser fetches JSON and generates CSV client-side.

## Bash Download Script

**Why bash (not Node.js)?** Node.js `execSync` + `evalJS` with embedded
quotes/escapes fails randomly due to CSP on Rogers Bank. Direct CDP CLI
calls chained with `&&` in bash are reliable.

**Logic:** Find the latest month that exists both in downloaded files AND
in the dropdown, then re-download only that month (catches backdated txns)
plus any newer ones that appeared.

```bash
#!/bin/bash
set -e

CDP="/home/nicolas/.pi/agent/git/github.com/pasky/chrome-cdp-skill/skills/chrome-cdp/scripts/cdp.mjs"
TARGET="DBB717AE" # Update: cdp.mjs list | grep -i roger
DL="/home/nicolas/Téléchargements"
BASE="/home/nicolas/Documents/Finances/Cartes de crédit/MasterCard Rogers Fido 5899"

# ── Step 1: find latest existing YYYY-MM.csv ──
latest=$(find "$BASE" -maxdepth 2 -name '????-??.csv' | grep -oP '\d{4}-\d{2}' | sort | tail -1)
echo "Latest existing file: $latest"

# ── Step 2: open modal, get dropdown options ──
$CDP click $TARGET '[aria-label="Download transactions"]' 2>/dev/null || \
$CDP click $TARGET '[aria-label="Télécharger les opérations"]' 2>/dev/null || true
sleep 3

opts=$($CDP eval $TARGET 'var s=document.getElementById("month-select");if(!s)return"none";var r=[];for(var i=0;i<s.options.length;i++)r.push(s.options[i].value+"||"+s.options[i].text);r.join(",")')
if [ "$opts" = "none" ] || [ -z "$opts" ]; then
  echo "Modal not open. Re-try clicking download button."; exit 1
fi
echo "Available: $(echo "$opts" | tr ',' '\n' | grep -v '^-Select-\|^$' | wc -l) periods"

# ── Step 3: find what to download ──
# Dropdown is sorted newest-first. Find first option where YYYY-MM matches
# a file we already have → that's the latest overlap → re-download it + newer.
declare -A val2text
declare -a ym_list
IFS=',' read -ra PAIRS <<< "$opts"
for pair in "${PAIRS[@]}"; do
  v="${pair%%||*}"
  t="${pair#*||}"
  [ -z "$v" ] && continue
  # Parse "Mar 2026" → 2026-03, or "mars 2026" → 2026-03
  ym=$(echo "$t" | sed -nE 's/^([A-Za-zàûé]+)\.? +([0-9]{4})$/\1 \2/p')
  [ -z "$ym" ] && continue
  mo=$(echo "$ym" | awk '{
    n=tolower($1); gsub(/\./,"",n)
    m["jan"]=1;m["janv"]=1;m["feb"]=2;m["févr"]=2;
    m["mar"]=3;m["mars"]=3;m["apr"]=4;m["avr"]=4;
    m["may"]=5;m["mai"]=5;m["jun"]=6;m["juin"]=6;
    m["jul"]=7;m["juil"]=7;m["aug"]=8;m["août"]=8;
    m["sep"]=9;m["sept"]=9;m["oct"]=10;m["nov"]=11;
    m["dec"]=12;m["déc"]=12;
    if(m[n]) printf "%s-%02d\n",$2,m[n]
  }')
  [ -z "$ym" ] && continue
  val2text["$v"]="$t"
  ym_list+=("$ym")
  val2ym["$v"]="$ym"
done

# Find latest overlap
re_download_ym=""
re_download_val=""
for ym in "${ym_list[@]}"; do
  if find "$BASE" -maxdepth 2 -name "${ym}.csv" -print -quit 2>/dev/null | grep -q .; then
    re_download_ym="$ym"
    # find the val
    for v in "${!val2ym[@]}"; do
      [ "${val2ym[$v]}" = "$ym" ] && re_download_val="$v" && break
    done
    break
  fi
done

if [ -n "$re_download_ym" ]; then
  echo "Latest overlap: $re_download_ym (re-downloading to catch backdated txns)"
  # Collect this month + any that come BEFORE it (newer months in dropdown)
  to_download=()
  found=0
  for ym in "${ym_list[@]}"; do
    [ "$ym" = "$re_download_ym" ] && found=1
    if [ $found -eq 1 ]; then
      for v in "${!val2ym[@]}"; do
        [ "${val2ym[$v]}" = "$ym" ] && to_download+=("$v||$(echo "$ym" | tr - _)") && break
      done
    fi
  done
else
  echo "No overlap, downloading all available"
  for v in "${!val2ym[@]}"; do
    to_download+=("$v||${val2ym[$v]}")
  done
fi

echo "Will download ${#to_download[@]} month(s)"

# ── Step 4: download each ──
for entry in "${to_download[@]}"; do
  val="${entry%%||*}"
  label="${entry#*||}"
  year="${label:0:4}"
  echo -e "\n=== $label ==="

  # Select month in dropdown
  $CDP eval $TARGET "(function(){var s=document.getElementById('month-select');s.value='$val';s.dispatchEvent(new Event('change',{bubbles:true}));return'selected'})()"
  sleep 2

  # Record newest file before
  before=$(find "$DL" -maxdepth 1 -name 'transactions*.csv' -printf '%T@\n' 2>/dev/null | sort -rn | head -1)
  sleep 0.5

  # Click download
  $CDP eval $TARGET '(function(){document.querySelectorAll("button")[4].click()})()'
  sleep 10

  # Check for new file
  after=$(find "$DL" -maxdepth 1 -name 'transactions*.csv' -printf '%T@\n' 2>/dev/null | sort -rn | head -1)
  if [ "$after" = "$before" ]; then
    echo "  No new download"
    continue
  fi

  # Copy to target
  newest=$(find "$DL" -maxdepth 1 -name "transactions*.csv" -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2)
  dir="$BASE/$year"
  mkdir -p "$dir"
  cp "$newest" "$dir/${label}.csv"
  lines=$(wc -l < "$dir/${label}.csv")
  echo "  ✅ Saved ${label}.csv ($lines lines)"

  # Rebuild annual from scratch
  if ls "$dir"/????-??.csv 1>/dev/null 2>&1; then
    header=$(head -1 "$dir"/????-??.csv | head -1)
    { echo "$header"; cat "$dir"/????-??.csv | grep -v "^Date," | sort -u; } > "$dir/$year.csv"
  fi
done

echo -e "\n=== Done ==="
```

## File Structure

```
/home/nicolas/Documents/Finances/Cartes de crédit/MasterCard Rogers Fido 5899/
├── 2021/  ...
├── 2025/
│   ├── 2025-03.csv
│   ├── 2025-04.csv
│   ├── …
│   ├── 2025-12.csv
│   └── 2025.csv          (aggregated annual)
└── 2026/
    ├── 2026-01.csv
    ├── 2026-02.csv
    ├── 2026-03.csv
    └── 2026.csv          (aggregated annual)
```

## Rogers CSV Format

```csv
Date,Posted Date,Reference Number,Activity Type,Activity Status,Card Number,Merchant Category Description,Merchant Name,Merchant City,Merchant State or Province,Merchant Country Code,Merchant Postal Code,Amount,Rewards,Name on Card
2026-03-16,2026-03-17,"55134426075800175303737",TRANS,APPROVED,************5047,Wholesale Club,COSTCO WHOLESALE 1446,ANJOU,QC,CAN,H1J0A6,$525.68,,M. NICOLAS MARCHILDON
```

- Positive amounts = purchases (charges)
- Negative amounts = payments/credits
- Cashback appears as negative purchase amount

## Card Info

| Field | Value |
|-------|-------|
| Account ID | 000002611 |
| Customer ID | 000331803 |
| Card | *****5047 (was 5899) |
| Holder | M. NICOLAS MARCHILDON |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Session expired | Re-login at `https://rbaccess.rogersbank.com/` |
| Modal auto-closes | Wait 3s after click before eval |
| eval "Error: Uncaught" | Use single-line eval with no embedded double-quotes |
| Button index changed | Re-check with `document.querySelectorAll("button")` |
| Month language is French | Use `[aria-label="Télécharger les opérations"]` + FR month mapping |

## Related Skills

- Chrome CDP: `/home/nicolas/.pi/agent/git/github.com/pasky/chrome-cdp-skill/skills/chrome-cdp/SKILL.md`
