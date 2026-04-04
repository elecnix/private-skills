---
name: manuvie-download
description: Download Manulife Bank transactions via authenticated browser session and save as CSV files organized by account → year → monthly + annual files. Works with Manulife One accounts and sub-accounts.
metadata:
  version: "2.0"
  author: nicolas
---

# Manulife Bank Transaction Download

Download transactions from Manulife Bank online banking using Chrome CDP session and API endpoints.

## Prerequisites

1. Chrome browser with remote debugging enabled
2. User logged in at `https://online.manulifebank.ca/accounts`
3. Chrome CDP skill available
4. Node.js 22+

## API Endpoints

```
GET https://online.manulifebank.ca/api/v2/accounts/
GET https://online.manulifebank.ca/api/v2/accounts/history/{id}/start/{start}/end/{end}
```

### Account Structure

| ID | Account Number | Type | Description |
|----|----------------|------|-------------|
| 2 | 4095277 | Main | Manulife One Account |
| 3 | 4095277-1 | Sub | Secondary-account (fixed rate) |
| 4 | 4095277-2 | Sub | Secondary-account (fixed rate) |

### Date Availability

Transaction history is available from **June 29, 2021** to present (continuously growing).

⚠️ **Critical API quirk**: The `end` date must be within ~a few weeks of today's date.
If `end` is too far in the future, the API returns **HTTP 400**. Use today's date (or
a recent date) as the end of the current year's range.

## Download Script

Run this script to fetch all data and save CSVs:

```javascript
import { execSync } from 'child_process';
import fs from 'fs';

const CDP_DIR = '/home/nicolas/.pi/agent/git/github.com/pasky/chrome-cdp-skill';
const BASE = '/home/nicolas/Documents/Finances/Banque/Manuvie';
const TARGET = '60146E7E'; // Update with actual target ID from cdp.mjs list

const accounts = { '2': '4095277', '3': '4095277-1', '4': '4095277-2' };

const years = [2021, 2022, 2023, 2024, 2025, 2026];
// End date for the current year — must be a recent date, not far in the future
const today = '2026-04-04';

function evalJS(js) {
  const b64 = Buffer.from(js).toString('base64');
  return execSync(
    `cd ${CDP_DIR} && skills/chrome-cdp/scripts/cdp.mjs eval ${TARGET} "eval(atob('${b64}'))"`,
    { timeout: 60000, maxBuffer: 50 * 1024 * 1024 }
  ).toString();
}

async function fetchAll() {
  const ranges = [
    ['2021-06-29', '2022-01-01'],
    ['2022-01-01', '2023-01-01'],
    ['2023-01-01', '2024-01-01'],
    ['2024-01-01', '2025-01-01'],
    ['2025-01-01', '2026-01-01'],
    ['2026-01-01', today],
  ];
  const fetchJS = `
    (async () => {
      const accts = ['2','3','4'];
      const ranges = ${JSON.stringify(ranges)};
      const all = {};
      for (const a of accts) {
        all[a] = [];
        for (const [s,e] of ranges) {
          const r = await fetch(
            'https://online.manulifebank.ca/api/v2/accounts/history/' + a + '/start/' + s + '/end/' + e,
            { credentials: 'include' }
          );
          if (!r.ok) continue;
          const d = await r.json();
          const txns = d.historyTransactions ? d.historyTransactions.transaction : [];
          all[a] = all[a].concat(txns);
        }
      }
      window.__mdl = all;
      return Object.keys(all).map(k => k + ':' + all[k].length).join(', ');
    })()
  `;
  console.log('Fetching:', evalJS(fetchJS).trim());
}

function toCSV(acctId) {
  return `
    (function() {
      var txns = window.__mdl['${acctId}'].sort(function(a,b){return a.date-b.date;});
      var csv = "Date,Description,Withdrawal,Deposit,Balance,TransactionCode\\n";
      for (var i=0;i<txns.length;i++) {
        var t=txns[i], d=new Date(t.date);
        var ds=d.toISOString().split('T')[0];
        var desc=(t.description||'').replace(/"/g,'""');
        var w=t.withdrawalAmount!=null?t.withdrawalAmount.toFixed(2):'';
        var dep=t.depositAmount!=null?t.depositAmount.toFixed(2):'';
        var bal=t.balance!=null?t.balance.toFixed(2):'';
        csv+='"'+ds+'","'+desc+'",'+w+','+dep+','+bal+',"'+(t.transactionCode||'')+'"\\n';
      }
      return csv;
    })()
  `;
}

async function saveCSVs() {
  for (const [acctId, acctName] of Object.entries(accounts)) {
    for (const year of years) {
      const dir = `${BASE}/${acctName}/${year}`;
      fs.mkdirSync(dir, { recursive: true });

      // Fetch full CSV for this account once, then split
      if (!window.__csvCache) window.__csvCache = {};
      if (!window.__csvCache[acctId]) {
        window.__csvCache[acctId] = evalJS(toCSV(acctId));
      }
      const fullCSV = window.__csvCache[acctId];
      const lines = fullCSV.trim().split('\n');
      const header = lines[0];
      const dataLines = lines.slice(1).filter(l => l.trim().length > 0);

      // Filter by year
      const yearLines = dataLines.filter(l => l.split(',')[0].includes(String(year)));
      if (yearLines.length === 0) continue;

      // Save annual file
      const yearFile = `${dir}/${year}.csv`;
      fs.writeFileSync(yearFile, header + '\n' + yearLines.join('\n') + '\n');

      // Save monthly files
      const byMonth = {};
      for (const line of yearLines) {
        const ds = line.split(',')[0].replace(/"/g, '');
        const ym = ds.substring(0, 7);
        if (!byMonth[ym]) byMonth[ym] = [];
        byMonth[ym].push(line);
      }
      for (const [ym, mLines] of Object.entries(byMonth)) {
        const mFile = `${dir}/${ym}.csv`;
        fs.writeFileSync(mFile, header + '\n' + mLines.join('\n') + '\n');
      }
      console.log(`${acctName}/${year}: ${yearLines.length} rows, ${Object.keys(byMonth).length} month files`);
    }
  }
}

await fetchAll();
await saveCSVs();
```

## File Structure

```
/home/nicolas/Documents/Finances/Banque/Manuvie/
├── 4095277/
│   ├── 2021/
│   │   ├── 2021-06.csv
│   │   ├── 2021-07.csv
│   │   ├── …
│   │   ├── 2021-12.csv
│   │   └── 2021.csv
│   ├── 2022/
│   │   ├── 2022-01.csv
│   │   ├── …
│   │   └── 2022.csv
│   └── … 2023–2026/
├── 4095277-1/
│   └── 2021–2026/
│       ├── YYYY-MM.csv
│       └── YYYY.csv
└── 4095277-2/
    └── 2021–2026/
        ├── YYYY-MM.csv
        └── YYYY.csv
```

## UI Navigation & Download Modal

1. Click account → URL changes to `/accounts/account/details`
2. "Opérations" tab → "Télécharger" button opens download modal
3. Modal has 3 formats: **CSV**, **QuickBooks**, **Quicken**
4. Set date range with the date pickers (dd/mm/yyyy, inclusive)

The download button fires the same API call:
```
GET /api/v2/accounts/history/2/start/2026-01-01/end/2026-01-31
```

"Relevés" tab has PDF statements ("Afficher le PDF" buttons).

## CSV Format

```csv
Date,Description,Withdrawal,Deposit,Balance,TransactionCode
"2021-06-29","Advance",191207.64,,191207.64,"ADV"
"2021-06-30","Interest Posting",8.14,,48732.49,"LOCI"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Session expired | Re-login to Manulife Bank in Chrome |
| API returns 401 | Session cookie expired |
| API returns 400 | `end` date too far in future — use a recent date |
| "Error: Uncaught" | Single quote in JS breaks shell — use base64 encoding |
| No data before 2021 | History starts at 2021-06-29 |

## Related Skills

- Chrome CDP skill: `/home/nicolas/.pi/agent/git/github.com/pasky/chrome-cdp-skill/skills/chrome-cdp/SKILL.md`
- tangerine-download skill: Similar workflow for Tangerine Bank