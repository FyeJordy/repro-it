# Orchestrate Bridge for Repro-It

**IMPORTANT: Orchestrate integration is OPTIONAL.** The main Repro-It CLI demo works perfectly without it. This bridge is provided for users who want to trigger Repro-It via IBM watsonx Orchestrate.

## Overview

The Orchestrate Bridge exposes Repro-It functionality via a REST API that can be imported into Orchestrate as a custom tool. This allows you to ask Orchestrate to run Repro-It demos using natural language.

**The local CLI remains the source of truth.** Use `python3 repro_it.py` for direct control and debugging.

## Architecture

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────┐
│ Orchestrate │─────▶│ Public Tunnel    │─────▶│ Flask Bridge│
│             │      │ (ngrok/cloudflare)│      │ (port 5001) │
└─────────────┘      └──────────────────┘      └──────┬──────┘
                                                       │
                                                       ▼
                                                ┌──────────────┐
                                                │ repro_it.py  │
                                                │ (subprocess) │
                                                └──────────────┘
```

## Security

- ✅ **No hardcoded secrets** - Environment variables stay in your environment
- ✅ **Path validation** - Prevents directory traversal attacks
- ✅ **No secret exposure** - API never prints or returns environment variable values
- ✅ **Timeout protection** - Commands timeout after 120 seconds
- ⚠️ **Tunnel URLs are temporary** - Never commit them to git

## Quick Start

### 1. Install Flask

The bridge requires Flask, which is not needed for the main demo:

```bash
pip install flask
```

### 2. Start the Bridge Server

```bash
cd repro-it
python3 orchestrate_bridge/app.py
```

You should see:
```
Starting Orchestrate Bridge on port 5001
Project root: /path/to/repro-it
Health check: http://localhost:5001/health
Run repro: POST http://localhost:5001/run-repro
```

### 3. Test Locally with curl

Health check:
```bash
curl http://localhost:5001/health
```

Expected response:
```json
{"ok": true}
```

Run Repro-It with default paths:
```bash
curl -X POST http://localhost:5001/run-repro \
  -H "Content-Type: application/json" \
  -d '{}'
```

Run with custom paths:
```bash
curl -X POST http://localhost:5001/run-repro \
  -H "Content-Type: application/json" \
  -d '{
    "bug_path": "bugs/discount_double_gift_card.json",
    "repo_path": "demo_repo"
  }'
```

Expected response:
```json
{
  "ok": true,
  "exit_code": 0,
  "success": true,
  "judge_provider": "watsonx",
  "failure_summary": "",
  "stdout": "...",
  "stderr": ""
}
```

## Exposing to Orchestrate

To use with Orchestrate, you need to expose your local server via a public tunnel.

### Option A: Using ngrok

1. Install ngrok: https://ngrok.com/download

2. Start tunnel:
```bash
ngrok http 5001
```

3. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

### Option B: Using cloudflared

1. Install cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

2. Start tunnel:
```bash
cloudflared tunnel --url http://localhost:5001
```

3. Copy the HTTPS URL (e.g., `https://xyz789.trycloudflare.com`)

## Generate OpenAPI Specification

Once you have a public URL, generate the OpenAPI spec:

```bash
python3 scripts/write_orchestrate_openapi.py https://your-tunnel-url
```

Example:
```bash
python3 scripts/write_orchestrate_openapi.py https://abc123.ngrok.io
```

This creates `orchestrate_bridge/openapi.local.yaml` with your tunnel URL. This file is gitignored.

## Import into Orchestrate

1. Log into IBM watsonx Orchestrate

2. Navigate to **Tools** → **Import Tool**

3. Select **OpenAPI Specification**

4. Upload `orchestrate_bridge/openapi.local.yaml`

5. Configure the tool:
   - Name: "Repro-It Demo"
   - Description: "Run Repro-It to reproduce bugs and generate tests"

6. Save and activate the tool

## Using with Orchestrate

Once imported, you can ask Orchestrate:

> "Run the Repro-It demo with the discount double gift card bug"

> "Use Repro-It to reproduce the bug in bugs/discount_double_gift_card.json"

> "Execute the run_repro_it_demo operation"

Orchestrate will call your bridge, which will execute Repro-It and return the results.

## API Reference

### GET /health

Health check endpoint.

**Response:**
```json
{"ok": true}
```

### POST /run-repro

Run Repro-It with specified bug and repo paths.

**Request Body (all fields optional):**
```json
{
  "bug_path": "bugs/discount_double_gift_card.json",
  "repo_path": "demo_repo"
}
```

**Response:**
```json
{
  "ok": true,
  "exit_code": 0,
  "success": true,
  "judge_provider": "watsonx",
  "failure_summary": "",
  "stdout": "...",
  "stderr": ""
}
```

**Fields:**
- `ok`: Whether the API call succeeded
- `exit_code`: Process exit code (0 = success)
- `success`: Whether repro_it.py succeeded
- `judge_provider`: AI judge used ("watsonx", "heuristic", or null)
- `failure_summary`: Summary of any failure
- `stdout`: Full standard output
- `stderr`: Full standard error

## Path Validation

The bridge validates all paths to prevent security issues:

- ❌ Absolute paths (starting with `/`) are rejected
- ❌ Path traversal (`..`) is rejected
- ✅ Only relative paths within the project root are allowed

Examples:
```bash
# ✅ Valid
{"bug_path": "bugs/discount_double_gift_card.json"}

# ❌ Invalid - absolute path
{"bug_path": "/etc/passwd"}

# ❌ Invalid - path traversal
{"bug_path": "../../../etc/passwd"}
```

## Environment Variables

The bridge respects the same environment variables as the CLI:

- `WATSONX_API_KEY` - Your watsonx API key (required for AI judge)
- `WATSONX_PROJECT_ID` - Your watsonx project ID (required for AI judge)

**IMPORTANT:** The bridge never prints or returns these values. They remain secure in your environment.

Set them before starting the bridge:
```bash
export WATSONX_API_KEY="your-key-here"
export WATSONX_PROJECT_ID="your-project-id"
python3 orchestrate_bridge/app.py
```

## Troubleshooting

### Bridge won't start
- Check if port 5001 is already in use: `lsof -i :5001`
- Try a different port by editing `app.py`

### Tunnel connection fails
- Ensure bridge is running on port 5001
- Check firewall settings
- Try a different tunnel service

### Orchestrate can't reach the bridge
- Verify tunnel URL is correct in `openapi.local.yaml`
- Test the tunnel URL directly with curl
- Check tunnel service logs

### Path validation errors
- Ensure paths are relative to project root
- Don't use absolute paths or `..`
- Check that files exist: `ls bugs/discount_double_gift_card.json`

### Environment variables not working
- Set them in the same terminal where you start the bridge
- Don't set them in a different terminal
- Verify with `echo $WATSONX_API_KEY` (but don't share the output!)

## Limitations

- **Tunnel URLs are temporary** - They expire when you close the tunnel
- **Single request at a time** - The bridge doesn't queue requests
- **120-second timeout** - Long-running operations will be killed
- **No authentication** - Anyone with the tunnel URL can use the bridge

## Best Practices

1. **Use the CLI for development** - It's faster and gives you more control
2. **Use Orchestrate for demos** - It's great for showing off to stakeholders
3. **Never commit tunnel URLs** - They're temporary and should stay local
4. **Regenerate openapi.local.yaml** - Each time you start a new tunnel
5. **Monitor bridge logs** - Watch for errors and security issues

## Comparison: CLI vs Orchestrate

| Feature | CLI | Orchestrate Bridge |
|---------|-----|-------------------|
| Setup | ✅ Simple | ⚠️ Requires tunnel |
| Speed | ✅ Fast | ⚠️ Network latency |
| Control | ✅ Full control | ⚠️ Limited |
| Debugging | ✅ Easy | ⚠️ Harder |
| Demo value | ⚠️ Technical | ✅ Impressive |
| Security | ✅ Local only | ⚠️ Exposed via tunnel |

**Recommendation:** Use the CLI for development and testing. Use Orchestrate for demos and presentations.

## Support

For issues with:
- **Repro-It CLI** - See README.md and DEMO.md
- **Bridge server** - Check bridge logs and this document
- **Orchestrate** - Consult IBM watsonx Orchestrate documentation
- **Tunnel services** - See ngrok or cloudflared documentation

## License

Same as Repro-It main project.