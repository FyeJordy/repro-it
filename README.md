# Repro-It

**Turn vague bug reports into deterministic failing pytest tests using IBM watsonx.ai.**

## What + Why

Bug reports are often vague: "discount code not working on gift cards." Developers waste hours manually reproducing issues. Repro-It automates this: reads bug report JSON, searches codebase, generates pytest regression test, runs it, and uses IBM watsonx.ai with Granite 8B Code Instruct to verify it fails for the right reason.

## Demo

```bash
cd repro-it
python3 repro_it.py --bug bugs/discount_double_gift_card.json --repo demo_repo --verbose
```

**Output:**
```
✅ SUCCESS: Bug reproduced with failing test
Test file: demo_repo/tests/test_bug_discount_code_double_returns_w.py
Right-reason check: ✓ PASS
Judge provider: watsonx.ai
Failure message: AssertionError: Expected 80.0, got 100.0
```

## How It Works

1. Parse bug report → Extract signals (discount codes, categories, keywords)
2. Search repository → Find relevant files
3. Generate test → Create pytest with proper imports/assertions (deterministic)
4. Run pytest → Execute test locally
5. watsonx.ai judge → Granite 8B verifies failure matches bug (or deterministic fallback)

## IBM Bob & This Project

Bob was the development partner. Contributions: designed architecture, generated demo repo with seeded bug, built local tools (read_file, search_repo, write_test, run_pytest), implemented deterministic agent, integrated watsonx.ai judge, debugged SDK, stabilized demo (3/3 watsonx.ai runs, 5/5 deterministic).

## Architecture

```
bug.json → repro_it.py → HeuristicAgent → Tools → tests/
                              ↓              ↓
                    watsonx.ai judge    read_file
                    (Granite 8B)        search_repo
                         ↓              write_test
                  deterministic         run_pytest
                    fallback
```

## How To Run

```bash
cd repro-it

# 1. Install Repro-It agent dependencies
python3 -m pip install -r requirements.txt

# 2. Install demo Flask app dependencies
python3 -m pip install -r demo_repo/requirements.txt

# 3. Run with deterministic judge
python3 repro_it.py --bug bugs/discount_double_gift_card.json --repo demo_repo --verbose

# Optional: Enable watsonx.ai judge
export WATSONX_API_KEY="your-key"
export WATSONX_PROJECT_ID="your-project-id"
export WATSONX_URL="https://us-south.ml.cloud.ibm.com"
python3 repro_it.py --bug bugs/discount_double_gift_card.json --repo demo_repo --verbose
```

Automatically falls back to deterministic judge if watsonx.ai unavailable.

---

**Built for IBM Bob Dev Day Hackathon 2026**