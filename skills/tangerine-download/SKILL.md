---
name: tangerine-download
description: Download Tangerine transaction exports safely via direct URL extraction or UI flow, and rename/move CSV files into organized finance folders.
---

# Tangerine transaction download workflow

Use this skill when the user wants to download Tangerine transaction exports (credit cards, checking, savings) and organize them locally.

## Related skill

Use the Chrome CDP skill for browser control and inspection:
- `/home/nicolas/.pi/agent/git/github.com/pasky/chrome-cdp-skill/skills/chrome-cdp/SKILL.md`

## Account types and download methods

### Credit cards (CREDITLINE)
- **Direct URL works** - can use programmatic `<a>` element clicks
- Has billing cycle dropdown with date ranges
- Filename pattern: `5360 xxxx  xxxx XXXX.CSV`
- Use statement period naming: `YYYY-MM-DD.csv` (endDate from URL)

### Checking accounts (CHEQUING)
- **Direct URL does NOT work** - must use UI download flow
- No billing cycle dropdown
- Filename pattern: `<Account Nickname>.CSV`
- Use: `<Nickname> <Last4Digits>.csv`

### Savings accounts (SAVINGS)
- **Direct URL does NOT work** - must use UI download flow
- No billing cycle dropdown
- Filename pattern: `<Account Nickname>.CSV`
- Use: `<Nickname> <Last4Digits>.csv`

## Getting account information

Use the PFM API to discover all accounts:

```javascript
fetch('https://secure.tangerine.ca/web/rest/pfm/v1/accounts', {credentials: 'include'})
  .then(r => r.json())
  .then(d => d.accounts.map(a => ({
    nickname: a.nickname,
    number: a.number,
    displayName: a.display_name,
    type: a.type
  })))
```

This returns all accounts with their ac tokens (in the `number` field, format: `31323334353637383930313233343536<HEX_TOKEN>`).

### Known accounts (as of March 2025)

| Nickname | Last 4 | Type | Target Folder |
|----------|--------|------|---------------|
| Nicolas 166 | 8166 | CHEQUING | Banque/Tangerine/ |
| Dépenses variables | 8227 | CHEQUING | Banque/Tangerine/ |
| Épargne | 7270 | SAVINGS | Banque/Tangerine/ |
| Vacances | 9143 | SAVINGS | Banque/Tangerine/ |
| Nicolas | 2609 | SAVINGS | Banque/Tangerine/ |
| Étincelles | 0728 | SAVINGS | Banque/Tangerine/ |
| Maëva | 5130 | SAVINGS | Banque/Tangerine/ |
| Coralie | 5161 | SAVINGS | Banque/Tangerine/ |
| World Mastercard Remises | 8499 | CREDIT_CARD | Cartes de crédit/MC Tangerine.../ |
| World Mastercard Remises | 1194 | CREDIT_CARD | Cartes de crédit/MC Tangerine.../ |

## Direct URL (credit cards only)

```
https://secure.tangerine.ca/web/rest/v1/accounts/downloads?
  ac=<TOKEN>&
  fileType=CSV&
  language=fra&
  acctType=CREDITLINE&
  acctName=<URL_ENCODED_DISPLAY_NAME>&
  startDate=<YYYYMMDD>&
  endDate=<YYYYMMDD>
```

For credit cards, the `<ac>` token is 96 hex characters. The `endDate` is **exclusive** (one day after the last statement day).

### Filename from URL
- URL: `startDate=20250221&endDate=20250321`
- Filename: `2025-03-21.csv`

## UI download flow (all accounts)

This is the reliable method for checking/savings accounts:

### Steps

1. Navigate to download page:
   ```javascript
   window.location.hash = '#/download-transactions';
   ```
   Or use `location.href` with the full URL. Wait 10-15 seconds for Angular to render.

2. **Wait for mat-select elements** (Angular Material dropdowns):
   ```javascript
   document.querySelectorAll('mat-select').length  // Should be 2 for checking/savings, 3 for credit cards
   ```
   If 0, wait longer or hard-reload.

3. **Select account** (first mat-select):
   ```javascript
   document.querySelector('#e-transfer-account').click();
   // Wait 1s, then click the option:
   document.querySelector('mat-option:nth-child(N)').click();
   ```

4. **Select format** (second mat-select, id=mat-select-0 or mat-select-2):
   ```javascript
   document.querySelectorAll('mat-select')[1].click();
   // Wait 1s, then:
   Array.from(document.querySelectorAll('mat-option'))
     .find(o => o.textContent.includes('Excel'))?.click();
   ```
   **Important**: For credit cards, the format dropdown (mat-select-2) contains BOTH billing cycles AND format options. Select "Excel et autres logiciels" which appears at the END of the list.

5. **For credit cards only**: Also select a billing cycle (mat-select-3):
   ```javascript
   document.querySelector('#mat-select-3').click();
   // Select first option for most recent cycle
   document.querySelector('mat-option').click();
   ```

6. **Click Télécharger**:
   ```javascript
   document.querySelector('button.mat-primary').click();
   ```

7. **Wait for completion** (2-5 seconds):
   ```javascript
   document.body.innerText.includes('Terminé')  // true when done
   ```

8. **Move file immediately**:
   ```bash
   mv ~/Téléchargements/<filename>.CSV /target/folder/<new-name>.csv
   ```

### Navigation gotchas

- After download, the page shows "Terminé" completion state
- **Hard reload is required** to reset the form: `location.reload(true)`
- Then navigate: `location.href = 'https://www.tangerine.ca/app/#/download-transactions'`
- Wait 15 seconds after reload before expecting the form to load
- The Angular app caches state aggressively

### Download behavior

- Checking/savings "since last download" returns all transactions since account creation (or last download)
- Credit cards need billing cycle selection
- Download completes in 2-5 seconds typically
- File appears in `~/Téléchargements/` with account-based name

## Target folders

- **Checking/Savings**: `/home/nicolas/Documents/Finances/Banque/Tangerine/`
- **Credit cards**: `/home/nicolas/Documents/Finances/Cartes de crédit/MasterCard Tangerine Nicolas 4402,4130,4326,8499/2025`

## Naming conventions

### Credit cards
```
YYYY-MM-DD.csv  (statement period end date)
```

### Checking/Savings
```
<Nickname> <Last4Digits>.csv
```
Examples:
- `Nicolas 166 8166.csv`
- `Dépenses variables 8227.csv`
- `Épargne 7270.csv`

## Pre-download checklist

1. Archive old CSVs from `~/Téléchargements`:
   ```bash
   mkdir -p ~/Téléchargements/tangerine_csv_archive_$(date +%Y%m%d)
   mv ~/Téléchargements/*5360* ~/Téléchargements/*transactions* ~/Téléchargements/tangerine_csv_archive_*/
   ```

2. Ensure target folders exist:
   ```bash
   mkdir -p "/home/nicolas/Documents/Finances/Banque/Tangerine"
   mkdir -p "/home/nicolas/Documents/Finances/Cartes de crédit/MasterCard Tangerine Nicolas 4402,4130,4326,8499/2025"
   ```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| 0 mat-selects found | Angular not loaded | Wait 15s, or hard-reload |
| Page shows "Terminé" | Previous download cached | Hard-reload (`location.reload(true)`) |
| Format dropdown has billing cycles | Credit card selected (has 3 selects) | Use mat-select-2, pick "Excel..." from end of list |
| Download stuck "En traitement" | Format not selected | Cancel and retry with proper format selection |
| Empty CSV | No new transactions since last download | Normal - move on to next account |
| Session expired | Logged out | Ask user to log back in |
