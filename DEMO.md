# Repro-It Demo Guide

## Quick Start

### Run the Demo

```bash
python3 repro_it.py --bug bugs/discount_double_gift_card.json --repo demo_repo --verbose
```

## Expected Success Signals

When the demo runs successfully, you should see:

```
✅ SUCCESS: Bug reproduced with failing test
Judge provider: watsonx.ai
```

The generated test will fail with:

```
AssertionError: Expected 80.0, got 100.0
```

This confirms that Repro-It successfully:
1. Analyzed the vague bug report
2. Generated a deterministic failing pytest test
3. Verified the test fails for the right reason using IBM watsonx.ai

## 90-Second Video Walkthrough Script

**[0:00-0:15] Introduction**
- "Hi, I'm demonstrating Repro-It, a tool that turns vague bug reports into deterministic failing pytest tests."
- "This was built for the IBM Bob Dev Day Hackathon 2026."

**[0:15-0:30] Show the Bug Report**
- Open `bugs/discount_double_gift_card.json`
- "Here's a vague bug report: 'Discount code and gift card both apply, customer gets double discount.'"
- "No stack trace, no line numbers, just a description."

**[0:30-0:50] Run Repro-It**
- Run: `python3 repro_it.py --bug bugs/discount_double_gift_card.json --repo demo_repo --verbose`
- "Repro-It uses local Python tools to read code, search the repo, and generate a test."
- "It then uses IBM watsonx.ai Granite 8B Code Instruct to verify the test fails for the right reason."

**[0:50-1:15] Show the Results**
- Show terminal output: "SUCCESS: Bug reproduced with failing test"
- Show "Judge provider: watsonx.ai"
- Open generated test file: `demo_repo/tests/test_bug_discount_code_double_returns_w.py`
- "The test is deterministic and fails with: AssertionError: Expected 80.0, got 100.0"

**[1:15-1:30] Conclusion**
- "Repro-It bridges the gap between vague bug reports and actionable regression tests."
- "It combines deterministic local tools with optional AI verification for production-ready test generation."
- "Optional: IBM watsonx Orchestrate can also call Repro-It through an imported OpenAPI tool for agent-driven demos."

## Important Notes

### Security
⚠️ **DO NOT print or display your `WATSONX_API_KEY` on screen during the demo.**

The API key is read from the environment variable and should remain confidential.

### Fallback Behavior
If IBM watsonx.ai is unavailable or the API key is not set, Repro-It automatically falls back to **deterministic judging** using rule-based verification. The demo will still work and generate valid tests, but the judge provider will show `deterministic` instead of `watsonx.ai`.

This ensures the tool remains useful even without AI access.

### IBM watsonx Orchestrate Integration (Optional)
Repro-It can be called through IBM watsonx Orchestrate as an imported OpenAPI tool. The Orchestrate agent successfully reproduced the discount gift-card bug with these results:
- **Bug reproduced**: Yes
- **Judge provider**: watsonx.ai
- **Failure summary**: E AssertionError: Expected 80.0, got 100.0

The integration uses a Flask bridge exposed via temporary Cloudflare Tunnel. See [ORCHESTRATE.md](ORCHESTRATE.md) for setup details.

**Note**: The main reliable demo remains the local CLI. Orchestrate integration is optional and for advanced demos.

## Demo Environment Setup

Before running the demo, ensure:

1. **Dependencies installed:**
   ```bash
   python3 -m pip install -r requirements.txt
   python3 -m pip install -r demo_repo/requirements.txt
   ```

2. **watsonx.ai API key set (optional):**
   ```bash
   export WATSONX_API_KEY="your-api-key-here"
   ```

3. **Python 3.9+ available:**
   ```bash
   python3 --version
   ```

## Troubleshooting

- **Test already exists:** Delete `demo_repo/tests/test_bug_*.py` files before re-running
- **Import errors:** Ensure both requirements.txt files are installed
- **watsonx.ai errors:** The tool will automatically fall back to deterministic judging