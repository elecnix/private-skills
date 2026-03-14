---
name: tangerine-download
description: Download Tangerine transaction exports safely, derive direct download URLs from the browser flow, and rename/move CSV files into organized finance folders.
---

# Tangerine transaction download workflow

Use this skill when the user wants to download many Tangerine transaction exports, especially credit-card statement-period CSV exports, and organize them locally.

## Related skill

Use the Chrome CDP skill for browser control and inspection:
- `/home/nicolas/.pi/agent/git/github.com/pasky/chrome-cdp-skill/skills/chrome-cdp/SKILL.md`

Follow that skill for:
- tab discovery
- clicking/selecting controls
- snapshots/screenshots
- JS evaluation in the page

## Goal

Prefer extracting the direct download URL from Tangerine's browser flow, then use that URL pattern repeatedly instead of redoing the full UI for each statement period.

## Tangerine-specific findings

The transaction export UI builds a direct URL like:

```text
https://secure.tangerine.ca/web/rest/v1/accounts/downloads?ac=<ac>&fileType=<fileType>&language=<language>&acctType=<acctType>&acctName=<acctName>&startDate=<YYYYMMDD>&endDate=<YYYYMMDD>
```

For CSV downloads:
- `fileType=CSV`

The exact values for `ac`, `acctType`, and `acctName` should be captured from the real browser flow by intercepting or observing the generated URL after one successful manual/UI-triggered export.

## Recommended process

1. Attach to the Tangerine tab with the Chrome CDP skill.
2. Open the **Télécharger mes opérations** flow.
3. Select the target account and one statement cycle.
4. Trigger one real download through the page.
5. Capture the exact generated direct URL.
6. Reuse that URL pattern for the remaining cycles by changing only `startDate` and `endDate`.
7. If direct `window.open()` is unreliable, inject a real `<a>` element with the direct URL and click it.
8. After each download, rename and move the CSV out of `~/Téléchargements` immediately so the next file name does not collide.

## File handling rules

- Watch `~/Téléchargements` for files like `5360 xxxx  xxxx 8499.CSV` or `5360 xxxx  xxxx 8499 (1).CSV`.
- Move the downloaded file out immediately after each successful download
- Rename using ISO dates when possible, using the end date of the statement period, for example:

```text
2025-03-20.csv
```

Example:
- URL: `startDate=20250221&endDate=20250321`
- Final filename: `2025-03-21.csv`

## Safety notes

- Do not assume browser-side filename override will work; Tangerine/server headers usually control the final filename.
- Before bulk downloading, archive old conflicting Tangerine CSV files from `~/Téléchargements`.
- Verify the target folder before moving files.

## Example bulk-download loop

For each cycle:
1. Trigger direct URL download from the browser.
2. Wait for the new file to appear in `~/Téléchargements`.
3. Move it to the finance folder with ISO naming.
4. Continue with the next cycle.

## Expected target folder pattern

For this user workflow, files may need to go to a folder like:

```text
/home/nicolas/Documents/Finances/Cartes de crédit/MasterCard Tangerine Nicolas 4402,4130,4326,8499/2025
```

Adjust only if the user specifies a different account folder.
