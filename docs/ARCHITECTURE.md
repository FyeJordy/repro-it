# Repro-It Architecture

## System Overview

Repro-It is an automated bug reproduction system that transforms vague bug reports into deterministic failing pytest tests. The system parses structured bug report JSON files, uses a deterministic heuristic agent to search the target codebase, generates pytest regression tests with proper imports and assertions, executes them locally, and validates that failures match the reported bug using either IBM watsonx.ai with Granite 8B Code Instruct or a deterministic fallback judge. This enables developers to quickly reproduce reported issues without manual investigation.

## Architecture Flow

```
bug JSON → deterministic heuristic agent → local tools → generated pytest → run_pytest → watsonx.ai judge → deterministic fallback
```

**Detailed Flow:**
1. Bug report JSON parsed for signals (discount codes, categories, keywords)
2. HeuristicAgent orchestrates deterministic test generation
3. Local tools (read_file, search_repo) gather codebase context
4. write_test tool creates pytest with proper structure
5. run_pytest tool executes test locally
6. watsonx.ai judge validates failure matches bug (optional)
7. Deterministic fallback judge used if watsonx.ai unavailable

## Component Explanations

### `repro_it.py` CLI

**Purpose:** Command-line interface and main entry point for the system.

**Responsibilities:**
- Parse command-line arguments (bug path, repo path, max iterations, verbose flag)
- Validate input paths exist
- Invoke agent runner with configuration
- Display execution summary and exit with appropriate status code

**Key Design:** Clean separation between CLI concerns and agent logic enables future integration with other interfaces (web UI, CI/CD pipelines).

### `HeuristicAgent`

**Purpose:** Deterministic rule-based agent that orchestrates bug reproduction.

**Responsibilities:**
- Parse bug reports to extract signals (discount codes, categories, domain keywords)
- Coordinate tool usage to search codebase and read relevant files
- Generate pytest code using template-based approach
- Orchestrate test execution and right-reason verification

**Key Design:** Fully deterministic with no LLM calls in the generation phase. Uses pattern matching and heuristics to identify relevant code and construct tests. Architecture allows future replacement with LLM-backed agent without changing CLI or tools.

### `read_file` Tool

**Purpose:** Read source code files from the target repository.

**Responsibilities:**
- Accept file path relative to repository root
- Return file content with error handling
- Validate paths stay within repository boundaries

**Key Design:** Simple, focused tool that provides safe file access. Used by agent to examine relevant source files identified during search phase.

### `search_repo` Tool

**Purpose:** Search repository for files containing specific terms.

**Responsibilities:**
- Accept search term and repository root
- Use grep-like functionality to find matches
- Return list of matching files with context snippets
- Limit results to prevent overwhelming agent

**Key Design:** Enables agent to discover relevant files without prior knowledge of codebase structure. Returns ranked results prioritizing files with multiple matches.

### `write_test` Tool

**Purpose:** Write generated pytest code to the repository's test directory.

**Responsibilities:**
- Accept test filename and complete test code
- Create tests/ directory if needed
- Write file with proper permissions
- Return absolute path to created test

**Key Design:** Handles filesystem operations safely. Ensures tests are placed in standard pytest-discoverable location.

### `run_pytest` Tool

**Purpose:** Execute pytest tests and capture results.

**Responsibilities:**
- Run pytest on specified test file
- Capture stdout, stderr, and exit code
- Parse failure messages from pytest output
- Return structured result with execution details

**Key Design:** Isolated test execution with comprehensive output capture. Enables both success/failure detection and detailed failure analysis for right-reason checking.

### `right_reason` Module

**Purpose:** Verify that test failures correctly reproduce the reported bug.

**Responsibilities:**
- Coordinate between watsonx.ai judge and deterministic fallback
- Implement deterministic verification logic
- Check for assertion errors vs. import/setup errors
- Validate test includes key scenario elements from bug report
- Ensure failure messages contain expected comparisons

**Key Design:** Two-tier verification system. Attempts watsonx.ai judge first for sophisticated semantic matching, falls back to deterministic rules if unavailable. Deterministic judge uses multiple heuristics: rejects placeholder tests, requires assertion errors (not import errors), validates scenario coverage, checks for numeric comparisons in failure messages.

### `watsonx_judge` Module

**Purpose:** Optional AI-powered verification using IBM watsonx.ai and Granite 8B Code Instruct.

**Responsibilities:**
- Check for required environment variables (WATSONX_API_KEY, WATSONX_PROJECT_ID, WATSONX_URL)
- Initialize watsonx.ai Model with Granite 8B Code Instruct
- Build structured prompt with bug report, test code, and pytest output
- Parse JSON response from model
- Return match decision with confidence and reasoning

**Key Design:** Graceful degradation architecture. Returns "unavailable" status if credentials missing or SDK not installed, triggering automatic fallback. Uses greedy decoding (temperature=0.0) for deterministic responses. Prompt engineering guides model to reject common test generation failures (import errors, placeholders) and accept valid assertion failures matching bug scenarios.

## Design Rationale: Deterministic Generator + AI Judge

**Why the generator is deterministic:**
- **Reliability:** Template-based generation produces consistent, valid pytest code
- **Speed:** No API latency or token costs during test generation
- **Debuggability:** Rule-based logic is transparent and easy to troubleshoot
- **Offline capability:** Works without network access or API credentials
- **Cost efficiency:** No LLM calls for the generation phase

**Why the judge can use watsonx.ai:**
- **Semantic understanding:** AI excels at matching test failures to bug descriptions
- **Nuanced validation:** Can detect subtle mismatches between expected and actual behavior
- **Flexibility:** Handles edge cases that rigid rules might miss
- **Graceful degradation:** Falls back to deterministic judge if unavailable
- **Optional enhancement:** System works fully without watsonx.ai credentials

This hybrid approach maximizes reliability (deterministic generation) while leveraging AI where it adds most value (semantic validation), with no single point of failure.

## Fallback Behavior

**When watsonx.ai is unavailable:**

The system automatically falls back to deterministic right-reason checking in these scenarios:

1. **Missing credentials:** WATSONX_API_KEY, WATSONX_PROJECT_ID, or WATSONX_URL not set
2. **SDK unavailable:** ibm-watsonx-ai package not installed
3. **API errors:** Network failures, authentication errors, or service unavailability

**Fallback judge logic:**
- Rejects tests with import/setup errors (ImportError, NameError, ModuleNotFoundError)
- Rejects placeholder tests (TODO, "not yet implemented", "assert False")
- Requires AssertionError in pytest output
- Validates test includes at least 2 of 3 scenario elements (discount codes, categories, keywords)
- Checks failure messages contain numeric comparisons

**User experience:** Fallback is transparent. Verbose mode shows which judge was used. System always returns a definitive pass/fail decision.

## Current Scope

**Strong demo support for pricing/discount bugs:**
- Discount code application logic
- Category-based pricing rules
- Gift card handling
- Order total calculations
- Multi-item scenarios

**Template-based generation currently handles:**
- Discount code + category combinations
- Expected vs. actual price comparisons
- Order construction with Item and Order models
- calculate_total function invocation

**Designed to expand with templates for:**
- **API bugs:** HTTP request/response validation, status code checks, JSON schema validation
- **Database bugs:** Query result verification, transaction isolation, constraint violations
- **Exception bugs:** Expected exception types, error message validation, stack trace analysis
- **Function output bugs:** Return value validation, side effect checking, state mutation verification

**Expansion approach:** Add new signal extraction patterns in `parse_bug_report()`, new test templates in `generate_test()`, and corresponding right-reason validation rules. Architecture supports multiple bug type templates without modifying core agent loop or tools.

## Orchestrate Note

**IBM Orchestrate integration:** Optional and not required for the main demo functionality. The core Repro-It system operates independently using local tools and direct watsonx.ai API calls. If the Orchestrate bridge is completed in the future, it could provide:
- Centralized workflow orchestration across multiple repositories
- Integration with issue tracking systems
- Automated test execution in CI/CD pipelines
- Team collaboration features for bug reproduction workflows

The current architecture is designed to work standalone while remaining compatible with future Orchestrate integration through its modular tool-based design.

---

**Architecture designed for IBM Bob Dev Day Hackathon 2026**