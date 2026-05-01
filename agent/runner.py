"""Agent runner orchestration."""

import json
from pathlib import Path
from typing import Dict, Any
from .heuristic_agent import HeuristicAgent


def run_agent(bug_path: str, repo_root: str, max_iterations: int = 5, 
              verbose: bool = False) -> Dict[str, Any]:
    """
    Run the Repro-It agent to generate a regression test from a bug report.
    
    Args:
        bug_path: Path to bug report JSON file
        repo_root: Root directory of target repository
        max_iterations: Maximum number of agent iterations
        verbose: Enable verbose logging
    
    Returns:
        Dict with agent run results:
            - success: bool
            - test_path: Path to generated test
            - iterations: Number of iterations used
            - failure_message: Test failure message
            - right_reason: Whether test failed for the right reason
    """
    
    # Load bug report
    try:
        with open(bug_path, 'r') as f:
            bug_data = json.load(f)
    except Exception as e:
        return {
            "success": False,
            "test_path": None,
            "iterations": 0,
            "failure_message": f"Failed to load bug report: {e}",
            "right_reason": False
        }
    
    # Validate repo root
    repo_path = Path(repo_root).resolve()
    if not repo_path.exists():
        return {
            "success": False,
            "test_path": None,
            "iterations": 0,
            "failure_message": f"Repository not found: {repo_root}",
            "right_reason": False
        }
    
    # Import tools
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    from tools import read_file, search_repo, write_test, run_pytest
    
    # Create tools dict
    tools = {
        "read_file": read_file,
        "search_repo": search_repo,
        "write_test": write_test,
        "run_pytest": run_pytest
    }
    
    # Initialize agent
    agent = HeuristicAgent(tools, verbose=verbose)
    
    # Run agent
    result = agent.run(bug_data, str(repo_path), max_iterations)
    
    return result


def print_summary(result: Dict[str, Any], verbose: bool = False):
    """
    Print a formatted summary of the agent run.
    
    Args:
        result: Agent run result dict
        verbose: Include detailed output
    """
    print("\n" + "=" * 60)
    print("REPRO-IT AGENT SUMMARY")
    print("=" * 60)
    
    if result["success"]:
        print("✅ SUCCESS: Bug reproduced with failing test")
    else:
        print("❌ FAILURE: Could not reproduce bug")
    
    print(f"\nIterations used: {result['iterations']}")
    
    if result["test_path"]:
        print(f"Test file: {result['test_path']}")
    
    print(f"Right-reason check: {'✓ PASS' if result['right_reason'] else '✗ FAIL'}")
    
    # Show judge provider
    judge_provider = result.get("judge_provider", "deterministic")
    print(f"Judge provider: {judge_provider}")
    
    # Show reasoning if available and verbose
    if verbose and result.get("judge_reasoning"):
        print(f"Judge reasoning: {result['judge_reasoning']}")
    
    if result["failure_message"]:
        print(f"\nFailure message:")
        print("-" * 60)
        print(result["failure_message"])
        print("-" * 60)
    
    print("=" * 60 + "\n")

# Made with Bob
