#!/usr/bin/env python3
"""
Repro-It: Turn vague bug reports into deterministic failing pytest tests.

This is a deterministic rule-based MVP. The architecture supports replacing
the heuristic agent with an LLM-backed agent later without changing the CLI.
"""

import sys
import argparse
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agent.runner import run_agent, print_summary


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Repro-It: Generate regression tests from bug reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run against demo repository
  python repro_it.py --bug bugs/gift_card_discount_bug.json --repo demo_repo

  # With verbose output
  python repro_it.py --bug bugs/gift_card_discount_bug.json --repo demo_repo --verbose

  # Custom max iterations
  python repro_it.py --bug bugs/gift_card_discount_bug.json --repo demo_repo --max-iterations 10
        """
    )
    
    parser.add_argument(
        "--bug",
        required=True,
        help="Path to bug report JSON file"
    )
    
    parser.add_argument(
        "--repo",
        required=True,
        help="Path to target repository"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=5,
        help="Maximum number of agent iterations (default: 5)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Validate paths
    bug_path = Path(args.bug)
    if not bug_path.exists():
        print(f"Error: Bug report not found: {args.bug}", file=sys.stderr)
        return 1
    
    repo_path = Path(args.repo)
    if not repo_path.exists():
        print(f"Error: Repository not found: {args.repo}", file=sys.stderr)
        return 1
    
    # Print header
    if args.verbose:
        print("=" * 60)
        print("REPRO-IT: Bug Reproduction Agent")
        print("=" * 60)
        print(f"Bug report: {bug_path}")
        print(f"Repository: {repo_path}")
        print(f"Max iterations: {args.max_iterations}")
        print("=" * 60 + "\n")
    
    # Run agent
    result = run_agent(
        bug_path=str(bug_path),
        repo_root=str(repo_path),
        max_iterations=args.max_iterations,
        verbose=args.verbose
    )
    
    # Print summary
    print_summary(result, verbose=args.verbose)
    
    # Exit with appropriate code
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
