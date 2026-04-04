---
name: tangerine-download
description: Download Tangerine transaction exports (checking, savings, credit cards) as monthly CSVs.
---

# Tangerine transaction download workflow

Use this skill to download monthly Tangerine transaction CSVs for any account type (checking, savings, credit cards) and organize them into date-named folders.

## Related skill

- Chrome CDP skill: `/home/nicolas/.pi/agent/git/github.com/pasky/chrome-cdp-skill/skills/chrome-cdp/SKILL.md`

## Key findings

### Direct URL API — good for bank accounts, limited for credit cards

The direct download API works for all account types but has an important limitation for credit cards:

```
https://secure.tangerine.ca/web/rest/v1/accounts/downloads?
  ac=<PREFIX><ACCOUNT_TOKEN>&
  fileType=CSV&
  language=fra&
  acctType=SAVINGS&     ← checking AND savings
  acctType=CREDITLINE   ← credit cards
  acctName=<NAME>&
  startDate=<YYYYMMDD>&
  endDate=<YYYYMMDD>
```

- **Bank accounts**: date ranges work correctly, monthly windows return proper data
- **Credit cards**: **ignores date range**, always returns latest ~30-48 transactions. Only useful for current/partial month.

### Credit card workflow: merge API + statements UI

For credit cards, a full year requires merging multiple sources:

1. **Statements UI** → "Excel" format = CSV (for older months)
2. **API download** → latest ~30 txns (for current/partial month)
3. **Deduplicate** by full line, **group by transaction date**, save monthly `YYYY-MM.csv`

### Getting account tokens

```javascript
fetch('https://secure.tangerine.ca/web/rest/pfm/v1/accounts', {credentials: 'include'})
  .then(r => r.json())
  .then(d => d.accounts.map(a => ({ nickname: a.nickname, number: a.number, displayName: a.display_name, type: a.type })))
```

## Credit card accounts

### MC 8499 (active)

- **Folder**: `/home/nicolas/Documents/Finances/Cartes de crédit/MasterCard Tangerine Nicolas 4402,4130,4326,8499/`
- **Token**: `31323334353637383930313233343536b7088e2f70631d8f9d067f3a817429c8bd54be100b54dbf5758c94cda18af14f`
- **acctType**: `CREDITLINE`
- **Statement files**: `../<YEAR>/YYYY-MM-DD.csv` (e.g. `2025/2026-01-21.csv`, `2025/2026-02-21.csv`)

### MC 1194 (active)

- **Token**: `313233343536373839303132333435363bba3e9f146d416bc1af24fe5e6f18170231e5fb2505044a2afe4194683ad738`

### Credit card: download statements via UI ("Excel" = CSV)

For months older than the API's ~30-tx window:

1. Navigate to `/app/transactions` in Tangerine browser tab
2. Click **"Opération de la carte de crédit"** 
3. Click **"Télécharger"** (top right)
4. Set date range: **"Personnalisé"**, adjust Du/Au
5. Change format dropdown from PDF → **Excel** (despite the name, this downloads a **CSV** with header `Date de l'opération,Transaction,Nom,Description,Montant`)
6. Click blue **Télécharger** button
7. File saves to browser Downloads

Then rename to `YYYY-MM-DD.csv` and save to the appropriate `../<YEAR>/` folder.

### Credit card: merge all sources into monthly files

```python
# 1. Collect all CSV files (statements + API downloads)
# 2. Read all data deduplicating by full line
# 3. Extract transaction month from first column (MM/DD/YYYY → YYYY-MM)
# 4. Group by month, write to 2026/YYYY-MM.csv
# 5. Report coverage: dates per month, gaps
```

## Folder structure

### Bank accounts
```
/home/nicolas/Documents/Finances/Banque/Tangerine/
├── Nicolas 166 8166/
│   ├── 2025-01.csv
│   └── ...
└── Dépenses variables 8227/
    └── ...
```

### Credit cards
```
Cartes de crédit/MasterCard Tangerine Nicolas 4402,4130,4326,8499/
├── 2025/
│   ├── 2025-01.pdf          ← statement PDF (archive)
│   ├── 2025-12-21.csv       ← "Excel" download = CSV (source data)
│   ├── 2026-01-21.csv       ← statement covering Dec-Jan
│   └── 2026-02-21.csv       ← statement covering Feb-Mar
├── 2026/
│   ├── 2026-01.csv          ← merged monthly file
│   ├── 2026-02.csv
│   └── ...
├── 2016/ ... 2024/          ← older year folders
└── download.js              ← legacy UI automation (old 4326 card)
```

## Naming conventions

### Files
- **Monthly merged**: `YYYY-MM.csv` (final organized file)
- **Statement source**: `YYYY-MM-DD.csv` (downloaded PDF→Excel with date stamp)
- **Header**: `Date de l'opération,Transaction,Nom,Description,Montant`

### Folder naming
- Bank: `<Nickname> <Last4Digits>` (e.g., `Nicolas 166 8166/`)
- Credit card: full descriptive name (e.g., `MasterCard Tangerine Nicolas 4402,4130,4326,8499/`)

## Known bank accounts (as of March 2025)

| Nickname | Last 4 | Type | acctType | Token suffix |
|----------|--------|------|----------|-------------|
| Nicolas 166 | 8166 | CHEQUING | SAVINGS | 106d44b9... |
| Dépenses variables | 8227 | CHEQUING | SAVINGS | 31759a07... |
| Épargne | 7270 | SAVINGS | SAVINGS | 0e7763c2... |
| Vacances | 9143 | SAVINGS | SAVINGS | 5e175190... |
| Nicolas | 2609 | SAVINGS | SAVINGS | 5b918996... |
| Étincelles | 0728 | SAVINGS | SAVINGS | 342d5f9c... |
| Maëva | 5130 | SAVINGS | SAVINGS | db5f9c72... |
| Coralie | 5161 | SAVINGS | SAVINGS | dd37afa0... |

## Notes

- Don't sleep more than 5s between operations
- Fetch + save (no UI) is fastest for bank accounts
- Credit card API returns 204 No Content for empty months, but ignores date range
- Credit card statements become available ~mid-next-month after billing cycle
- **Important**: "Excel" format in the statements UI actually downloads CSV, not XLSX
- Always deduplicate merged data by full line
- Dates in CSV are `MM/DD/YYYY` format, French labels
