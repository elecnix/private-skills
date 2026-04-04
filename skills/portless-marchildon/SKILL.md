---
name: portless-marchildon
description: Set up and use portless with the marchildon.net wildcard DNS for local development. Use when setting up local dev URLs like https://myapp.local.marchildon.net
---

# Portless with marchildon.net

Local development URLs using the `*.local.marchildon.net` wildcard DNS.

## DNS Setup

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) → **marchildon.net** → **DNS**
2. Add record:
   ```
   Type:   A
   Name:   *.local
   IPv4:   127.0.0.1
   Proxy:  DNS only (grey cloud)
   ```
3. Save

This makes all `*.local.marchildon.net` subdomains resolve to 127.0.0.1.

## Start Portless Proxy

```bash
# Start proxy with .local TLD and --wildcard (requires sudo for port 80)
sudo portless proxy start --no-tls -p 80 --tld local --wildcard
```

The `--wildcard` flag allows subdomains (e.g., `myapp.local.marchildon.net`) to fall back to registered routes (e.g., `myapp.local`).

## Run Apps

```bash
# Use simple app name - portless appends .local
portless myapp npm run dev

# Access via http://myapp.local.marchildon.net
```

The `--wildcard` proxy routes `myapp.local.marchildon.net` → `myapp.local`.

## Example: email4ynab

```bash
# 1. Start proxy (once)
sudo portless proxy start --no-tls -p 80 --tld local --wildcard

# 2. Start app with simple name
cd ~/projects/email4ynab
portless email4ynab npm run dev

# 3. Access via http://email4ynab.local.marchildon.net
```

## Useful Commands

| Command | Description |
|---------|-------------|
| `portless list` | Show active routes |
| `portless get <name>` | Print URL for a service |
| `portless hosts sync` | Sync /etc/hosts (for Safari) |

## Test

```bash
# Verify DNS
nslookup test.local.marchildon.net
# Should show: Address: 127.0.0.1

# Test the proxy
curl http://email4ynab.local.marchildon.net
```

## Stop Proxy

```bash
sudo pkill -f "portless proxy"
```
