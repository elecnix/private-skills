---
name: cibc-download
description: Download CIBC credit card transactions via authenticated Chrome session. Uses the Download Transactions form with "All available" radio + CSV format to export all transactions at once. Saves as YYYY-MM.csv monthly + YYYY.csv annual files.
metadata:
  version: "1.0"
  author: nicolas
---

# CIBC Transaction Download

Download credit card transactions from CIBC Online Banking via Chrome CDP using the built-in CSV export feature.

## Prerequisites

1. Chrome browser with remote debugging enabled
2. User logged in to CIBC Online Banking:
   - Login: `https://rbaccess.rogersbank.com/?product=ROGERSBRAND&locale=fr_CA`
   - Dashboard: `https://www.cibconline.cibc.com/ebm-resources/.../#/accounts/default`
3. Chrome CDP skill available
4. Target folders:
   - `/home/nicolas/Documents/Finances/Cartes de crédit/Mastercard CIBC Costco 7567/`
   - `/home/nicolas/Documents/Finances/Cartes de crédit/Mastercard CIBC Visa 4346/`
   - `/home/nicolas/Documents/Finances/Cartes de crédit/Visa RBC/`

## Download Page

```
https://www.cibconline.cibc.com/ebm-resources/public/banking/cibc/client/web/index.html#/accounts/download
```

**Left sidebar** → "Download Transactions" (highlighted in red when active)

## Download Mechanism (what actually works)

The CIBC form uses a standard **POST submission** that triggers a browser file download.
The key is enabling Chrome's download behavior via CDP *before* submitting.

### Step-by-step working method

```bash
#!/bin/bash
CDP="skills/chrome-cdp/scripts/cdp.mjs"
TARGET="625825C8"  # Update: cdp.mjs list | grep -i cibc
DL="/home/nicolas/Téléchargements"
BASE="/home/nicolas/Documents/Finances/Cartes de crédit"
FOLDER="$1"  # e.g. "$BASE/Mastercard CIBC Costco 7567"

# 1. Enable Chrome download behavior (MUST do before form submit)
$CDP evalraw $TARGET "Browser.setDownloadBehavior" \
  '{"behavior":"allow","downloadPath":"'"$DL"'","eventsEnabled":true}'

# 2. Remove previous download
rm -f "$DL/cibc.csv" 2>/dev/null

# 3. Select account from dropdown (index 0)
VALUE="b6442896b74cf1f9dc050f767dfe9e0c4d5b39e0ce4e69e57c8b6700d9fe9719"  # Costco 7567
$CDP eval $TARGET "
  var sels = document.querySelectorAll('select');
  sels[0].value = '$VALUE';
  sels[0].dispatchEvent(new Event('change',{bubbles:true}));
" 
sleep 3

# 4. Select "All available" radio (index 1)
$CDP eval $TARGET "
  var radios = document.querySelectorAll('input[type=radio][name=criteria]');
  radios[2].checked = true;
  radios[2].dispatchEvent(new Event('change',{bubbles:true}));
"
sleep 3

# 5. Set format to CSV (last select, value = "CSV")
$CDP eval $TARGET "
  var sels = document.querySelectorAll('select');
  sels[sels.length-1].value = 'CSV';
  sels[sels.length-1].dispatchEvent(new Event('change',{bubbles:true}));
"
sleep 2

# 6. Record newest file before
before=$(find "$DL" -maxdepth 1 -name "*.csv" -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1)

# 7. Click the submit button
$CDP click $TARGET 'button[type="submit"]'
sleep 8

# 8. Check for new file
after=$(find "$DL" -maxdepth 1 -name "*.csv" -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1)
if [ "$after" != "$before" ] && [ -n "$after" ]; then
  newest=$(echo "$after" | cut -d' ' -f2-)
  echo "Downloaded: $newest ($(wc -l < "$newest") lines)"
  
  # Split into YYYY-MM.csv + YYYY.csv
  awk -F',' '{ym=substr($1,1,7); print >> ("/tmp/cibc_" ym ".tmp")}' "$newest"
  for f in /tmp/cibc_????-??.tmp; do
    [ -f "$f" ] || continue
    ym=$(basename "$f" | sed 's/^cibc_//;s/\.tmp$//')
    tac "$f" > "$FOLDER/${ym}.csv"   # reverse to oldest→newest
    rm "$f"
  done
  
  # Build annual from monthly
  for yr in 2024 2025 2026; do
    find "$FOLDER" -maxdepth 1 -name "${yr}-??.csv" -print0 | sort -z | \
      while IFS= read -r -d '' mf; do cat "$mf"; done > "$FOLDER/${yr}.csv"
    [ -s "$FOLDER/${yr}.csv" ] || rm -f "$FOLDER/${yr}.csv"
  done
fi
```

### Account dropdown mapping

| Dropdown option (index) | Value | Card | Target folder |
|-------------------------|-------|------|---------------|
| 1 `Other (00301-55-46699) $8.74` | `921fde65...` | USD account (?) | `Visa RBC/` |
| 2 `Other (00301-92-33733) USD 0.00` | `4bddc6bb...` | CAD account | `Mastercard CIBC Visa 4346/` |
| 3 `CIBC MasterCard (5268 0900 5634 7567) $0.00` | `b6442896b7...` | Costco Mastercard | `Mastercard CIBC Costco 7567/` |

## Card Mapping

| Dropdown text | Card number | Folder |
|---------------|-------------|--------|
| `CIBC MasterCard (5268 0900 5634 7567)` | 5268…7567 | `Mastercard CIBC Costco 7567/` |
| `Other (00301-55-46699) $8.74` | — | `Mastercard CIBC Visa 4346/` |
| `Other (00301-92-33733) USD 0.00` | — | `Visa RBC/` |

## CSV Format

CIBC exports **no headers** (raw data only):

```csv
2026-02-13,PAIEMENT PREAUTORISE - ME RCI,,30.00,5268********7567
2026-01-02,"FLO SERVICES QUEBEC, QC",30.00,,5268********7567
```

Columns: `Date, Description, Withdrawal, Deposit, CardNumber`
- Withdrawal populated = charge (positive amount)
- Deposit populated = credit/payment

## File Structure

```
Mastercard CIBC Costco 7567/
├── 2024-10.csv          (3 transactions)
├── 2024-11.csv          (1)
├── 2024-12.csv          (5)
├── 2024.csv             (9 - annual aggregate)
├── 2025-01.csv          (9)
├── 2025-02.csv          (2)
├── …                    …
├── 2025.csv             (18)
├── 2026-01.csv          (1)
└── 2026-02.csv          (1)

Visa RBC/
└── 2025-03.csv          (3 transactions)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No file after submit | Run `evalraw Browser.setDownloadBehavior` before clicking submit |
| "Please select financial management software" | Set `sels[sels.length-1].value = 'CSV'` (not "Spreadsheet (CSV)") |
| "invalid date range" | From date must be earlier than To date when using date range mode |
| Session expired | Re-login at `https://rbaccess.rogersbank.com/` |
| Download produces different filename | CIBC may vary: `cibc.csv`, `transactions.csv`, etc. — check `$DL` |
| "All available" radio not working | Use index 2 (not 1) for the radio group `input[name=criteria]` |

## Related Skills

- **rogersbank-download**: Similar approach but uses date range selector per month
- **tangerine-download**: Direct API download from Tangerine Bank
- **manuvie-download**: REST API download from Manulife Bank
