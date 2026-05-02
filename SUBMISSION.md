# Repro-It: IBM Bob Dev Day Hackathon 2026 Submission

---

## 📋 Problem and Solution Statement (paste into form)

**Problem**: Developers waste hours manually reproducing bugs from vague reports like "discount code not working on gift cards." This slows debugging and delays fixes.

**Solution**: Repro-It automates bug reproduction by reading structured bug reports, searching codebases, generating pytest regression tests, and using IBM watsonx.ai with Granite 8B Code Instruct to verify test failures match the reported bug.

**How it works**:
1. Parse bug report JSON to extract signals (discount codes, categories, keywords)
2. Search repository for relevant files using local tools
3. Generate pytest test with proper imports and assertions (deterministic agent)
4. Run test locally and capture output
5. Use IBM watsonx.ai (Granite 8B Code Instruct) to judge if failure matches bug report
6. Fall back to deterministic verification if watsonx.ai unavailable

**Demo**: Bug report "Discount code DOUBLE returns wrong total on gift cards" → Generated test creates gift_card order with DOUBLE code → Test fails with "Expected 80.0, got 100.0" → watsonx.ai judge confirms match (confidence: 1.0)

**Impact**: Automates hours of manual work, ensures test quality with AI verification, provides reliable fallback for always-working demo.

**Technologies**: Python, pytest, IBM watsonx.ai (Granite 8B Code Instruct), ibm-watsonx-ai SDK

**Repository**: https://github.com/FyeJordy/repro-it

---

## 🤖 IBM Bob and watsonx Usage Statement (paste into form)

**IBM Bob Role**: Development partner and pair programmer throughout the hackathon.

**Bob Contributions**:
- Assessed Bobcoin budget and tool constraints
- Designed modular architecture (tools → agent → CLI → watsonx.ai → Orchestrate)
- Generated demo repository with seeded gift card discount bug
- Built local Python tools: read_file, search_repo, write_test, run_pytest
- Wrote comprehensive unit tests for all tools
- Implemented deterministic heuristic agent for test generation
- Fixed false-success handling (placeholder test detection)
- Integrated IBM watsonx.ai as right-reason judge
- Debugged SDK integration for ibm-watsonx-ai 0.0.5
- Created Orchestrate bridge with Flask API and OpenAPI specification
- Stabilized demos (3/3 watsonx.ai runs, 5/5 deterministic runs, 1/1 Orchestrate run)

**IBM watsonx.ai Usage**:
- **Model**: Granite 8B Code Instruct (`ibm/granite-8b-code-instruct`)
- **Purpose**: Right-reason judge for test failures
- **Integration**: Python SDK (`ibm-watsonx-ai 0.0.5`)
- **Prompt Design**: Structured judge prompt that rejects import errors, placeholder tests (TODO, assert False), and unrelated assertion failures
- **Parameters**: Greedy decoding, temperature 0.0, max 200 tokens
- **Fallback**: Graceful degradation to deterministic verification if credentials missing or API fails
- **Results**: 3/3 successful runs with confidence 1.0, correctly identifying valid bug reproductions

**Architecture**: Deterministic test generation (rule-based agent) + AI-powered verification (watsonx.ai judge with deterministic fallback)

---

## Project Overview

**Repro-It** turns vague bug reports into deterministic failing pytest regression tests using IBM watsonx.ai.

## IBM Technologies Used

### IBM watsonx.ai
- **Model**: Granite 8B Code Instruct (`ibm/granite-8b-code-instruct`)
- **Purpose**: Right-reason judge for test failures
- **Integration**: Python SDK (`ibm-watsonx-ai 0.0.5`)
- **Prompt**: Structured judge prompt rejecting import errors, placeholders, and unrelated failures
- **Fallback**: Graceful degradation to deterministic verification

### IBM watsonx Orchestrate
- **Integration**: Optional agent interface via OpenAPI tool
- **Tool Name**: "Run Repro-It test reproduction"
- **Architecture**: Flask bridge exposed via temporary Cloudflare Tunnel
- **Demo Result**: Successfully reproduced discount gift-card bug
  - Bug reproduced: Yes
  - Judge provider: watsonx.ai
  - Failure summary: E AssertionError: Expected 80.0, got 100.0
- **Note**: Main reliable demo remains the local Repro-It CLI

### IBM Bob
- **Role**: Development partner and pair programmer
- **Contributions**:
  - Designed modular architecture
  - Generated demo repository with seeded bug
  - Built local Python tools (read_file, search_repo, write_test, run_pytest)
  - Implemented deterministic heuristic agent
  - Integrated watsonx.ai as right-reason judge
  - Created Orchestrate bridge with Flask API and OpenAPI spec
  - Debugged SDK integration
  - Stabilized demos (3/3 watsonx.ai, 5/5 deterministic, 1/1 Orchestrate)

## Technical Architecture

```
Bug Report (JSON)
    ↓
repro_it.py (CLI)
    ↓
HeuristicAgent (deterministic test generation)
    ↓
Local Tools (read_file, search_repo, write_test, run_pytest)
    ↓
Generated Test (pytest)
    ↓
watsonx.ai Judge (Granite 8B Code Instruct)
    ↓ (fallback if unavailable)
Deterministic Judge
    ↓
Success/Failure Report
```

## Demo Results

**Test case**: Gift card discount bug in e-commerce checkout

**Bug report**: "Discount code DOUBLE returns wrong total on gift cards"

**Generated test**:
```python
from models import Item, Order
from pricing import calculate_total

def test_bug_discount_code_double_returns_w():
    """Regression test: Discount code DOUBLE returns wrong total on gift cards"""
    items = [Item("Gift Card", 100.0, "gift_card")]
    order = Order(items, discount_code="DOUBLE")
    total = calculate_total(order)
    expected = 80.0  # 100 - 20%
    assert total == expected, f'Expected {expected}, got {total}'
```

**Result**: Test fails with `AssertionError: Expected 80.0, got 100.0`

**watsonx.ai judge**: ✓ PASS (confidence: 1.0)

## Key Features

1. **Deterministic test generation**: Rule-based agent ensures reproducible results
2. **IBM watsonx.ai integration**: Granite model verifies test quality
3. **Graceful fallback**: Works without watsonx.ai credentials
4. **Safe diagnostics**: Verbose mode shows judge selection without exposing secrets
5. **Local execution**: All tools run locally, no external dependencies for core functionality

## Innovation

- **Hybrid approach**: Deterministic generation + AI-powered verification
- **Production-ready**: Comprehensive error handling and fallback mechanisms
- **Extensible**: Clean architecture allows replacing deterministic agent with LLM later

## Impact

- **Time savings**: Automates hours of manual bug reproduction
- **Quality**: watsonx.ai ensures generated tests are meaningful
- **Reliability**: Deterministic fallback ensures always-working demo

## Repository

**GitHub**: https://github.com/FyeJordy/repro-it

## Installation & Usage

```bash
cd repro-it
python3 -m pip install -r demo_repo/requirements.txt

# With watsonx.ai (optional)
export WATSONX_API_KEY="your-key"
export WATSONX_PROJECT_ID="your-project-id"
export WATSONX_URL="https://us-south.ml.cloud.ibm.com"
python3 -m pip install ibm-watsonx-ai

# Run demo
python3 repro_it.py --bug bugs/discount_double_gift_card.json --repo demo_repo --verbose
```

## Team

**Developer**: Jordan (FyeJordy)  
**Development Partner**: IBM Bob

---

**Built for IBM Bob Dev Day Hackathon 2026**