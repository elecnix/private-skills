---
name: tangerine-download
description: Download Tangerine transaction exports via direct URL API, organized as monthly CSV files per account.
---

# Tangerine transaction download workflow

Use this skill to download monthly Tangerine transaction CSVs for any account type (checking, savings, credit cards) and organize them into date-named folders.

## Related skill

- Chrome CDP skill: `/home/nicolas/.pi/agent/git/github.com/pasky/chrome-cdp-skill/skills/chrome-cdp/SKILL.md`

## Key finding: direct URL works for ALL accounts

The direct download API works for **all account types** when using `acctType=SAVINGS`:

```
https://secure.tangerine.ca/web/rest/v1/accounts/downloads?
  ac=<PREFIX><ACCOUNT_TOKEN>&
  fileType=CSV&
  language=fra&
  acctType=SAVINGS&    ← Use SAVINGS for checking AND savings accounts!
  acctName=<DISPLAY_NAME>&
  startDate=<YYYYMMDD>&
  endDate=<YYYYMMDD>
```

- `ac` = `31323334353637383930313233343536` + 64-char hex token (checking/savings) or 96-char (credit cards)
- `acctType=SAVINGS` works for both CHEQUING and SAVINGS account types
- `acctType=CREDITLINE` for credit cards
- `acctName` = account nickname (e.g., "Nicolas 166") or display name (e.g., "5360 xxxx xxxx 8499")
- `startDate`/`endDate` = exclusive date range in `YYYYMMDD` format
- Response: 200 with CSV data if transactions exist, 204 No Content if empty

## Getting account tokens

Use the PFM API (requires browser cookies/session):

```javascript
fetch('https://secure.tangerine.ca/web/rest/pfm/v1/accounts', {credentials: 'include'})
  .then(r => r.json())
  .then(d => d.accounts.map(a => ({
    nickname: a.nickname,
    number: a.number,  // Full ac token
    displayName: a.display_name,
    type: a.type
  })))
```

The `number` field is the full `ac` parameter value.

## Downloading monthly files via browser fetch

Since the API requires authentication cookies, fetch from within the Tangerine browser tab:

```javascript
(async () => {
  const BASE = "https://secure.tangerine.ca/web/rest/v1/accounts/downloads";
  const params = new URLSearchParams({
    ac: "<FULL_ACCOUNT_TOKEN>",
    fileType: "CSV",
    language: "fra",
    acctType: "SAVINGS",  // or CREDITLINE for credit cards
    acctName: "<ACCOUNT_NAME>",
    startDate: "20250101",
    endDate: "20250201"    // Exclusive: Jan 1-31
  });
  const resp = await fetch(BASE + "?" + params, {credentials: "include"});
  const csvText = await resp.text();
  // csvText contains the CSV data
})();
```

### Batch download pattern

Fetch all months, store in window object, then extract:

```javascript
// 1. Fetch all months
const months = [
  ["20250101","20250201","2025-01"],
  ["20250201","20250301","2025-02"],
  // ... etc
];

const results = [];
for (const [start, end, label] of months) {
  const r = await fetch(url, {credentials: "include"});
  const t = await r.text();
  if (t.trim().split("\n").length > 1) {  // Has data beyond header
    results.push({file: label + ".csv", data: t});
  }
}
window.__downloadResults = results;

// 2. Extract each file via CDP eval and save via shell
```

## Folder structure

```
/home/nicolas/Documents/Finances/Banque/Tangerine/
├── Nicolas 166 8166/
│   ├── 2025-01.csv
│   ├── 2025-02.csv
│   └── ...
├── Dépenses variables 8227/
│   ├── 2025-01.csv
│   └── ...
├── Épargne 7270/
│   └── README.txt  (if no transactions)
└── ...
```

## Naming conventions

### Folder: `<Nickname> <Last4Digits>`
- `Nicolas 166 8166/`
- `Dépenses variables 8227/`
- `Épargne 7270/`
- `World Mastercard 8499/` (for credit cards)

### File: `YYYY-MM.csv`
- Period: Jan 1-31 → `2025-01.csv`
- Period: Feb 1-28 → `2025-02.csv`
- Date range is exclusive endDate: `startDate=20250101&endDate=20250201` = January

## Workflow summary

1. Get account list via PFM API
2. For each account, for each month:
   - Fetch CSV via direct URL from browser
   - If data exists (more than header), save to `<Folder>/<YYYY-MM>.csv`
3. Empty accounts get a README.txt explaining no transactions

## Date ranges for monthly downloads

```python
MONTHS = [
    ("20250101", "20250201", "2025-01"),  # January 2025
    ("20250201", "20250301", "2025-02"),  # February 2025
    ("20250301", "20250401", "2025-03"),  # March 2025
    # ... continue as needed
]
```

## Known accounts (as of March 2025)

| Nickname | Last 4 | Type | Token suffix |
|----------|--------|------|--------------|
| Nicolas 166 | 8166 | CHEQUING | 106d44b9... |
| Dépenses variables | 8227 | CHEQUING | 31759a07... |
| Épargne | 7270 | SAVINGS | 0e7763c2... |
| Vacances | 9143 | SAVINGS | 5e175190... |
| Nicolas | 2609 | SAVINGS | 5b918996... |
| Étincelles | 0728 | SAVINGS | 342d5f9c... |
| Maëva | 5130 | SAVINGS | db5f9c72... |
| Coralie | 5161 | SAVINGS | dd37afa0... |
| World MC Remises | 8499 | CREDIT_CARD | b7088e2f... |
| World MC Remises | 1194 | CREDIT_CARD | 3bba3e9f... |

## Notes

- Don't sleep more than 5s between operations
- Fetch + save approach is fastest (no UI interaction needed)
- The API returns 204 No Content for months with no transactions
- Credit cards use `acctType=CREDITLINE`, all others use `acctType=SAVINGS`
