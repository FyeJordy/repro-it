"""Deterministic rule-based agent for bug reproduction."""

import re
from pathlib import Path
from typing import Dict, List, Any


class HeuristicAgent:
    """
    Rule-based agent that generates regression tests from bug reports.
    
    This is a deterministic MVP. The architecture allows replacing this
    with an LLM-backed agent later without changing the CLI or tools.
    """
    
    def __init__(self, tools: Dict[str, Any], verbose: bool = False):
        """
        Initialize the heuristic agent.
        
        Args:
            tools: Dict of tool functions (read_file, search_repo, write_test, run_pytest)
            verbose: Enable verbose logging
        """
        self.tools = tools
        self.verbose = verbose
        self.iteration = 0
    
    def log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[Agent] {message}")
    
    def parse_bug_report(self, bug_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key signals from bug report.
        
        Returns dict with:
            - keywords: List of domain-specific terms
            - discount_codes: List of discount code names
            - categories: List of category names
            - expected: Expected behavior description
            - observed: Observed behavior description
        """
        self.log("Parsing bug report...")
        
        title = bug_data.get("title", "")
        description = bug_data.get("description", "")
        expected = bug_data.get("expected", "")
        observed = bug_data.get("observed", "")
        
        full_text = f"{title} {description} {expected} {observed}".lower()
        
        # Extract discount codes (uppercase words, often in quotes)
        discount_codes = re.findall(r'\b[A-Z][A-Z0-9]+\b',
                                   f"{title} {description} {expected} {observed}")
        
        # Extract category names with normalization
        categories = []
        
        # Find underscore-separated words
        categories.extend(re.findall(r'\b\w+_\w+\b', full_text))
        
        # Find "X category" patterns
        categories.extend(re.findall(r'(\w+)\s+category', full_text))
        
        # Normalize common multi-word categories
        # "gift card" / "gift-card" -> "gift_card"
        if "gift card" in full_text or "gift-card" in full_text:
            categories.append("gift_card")
        
        # Remove duplicates and normalize
        categories = list(set(categories))
        
        # Extract domain keywords
        domain_keywords = [
            "discount", "pricing", "checkout", "order", "item",
            "gift", "card", "calculate", "total", "subtotal", "parse_price"
        ]
        keywords = [kw for kw in domain_keywords if kw in full_text]
        
        # Also extract function names (snake_case identifiers)
        function_names = re.findall(r'\b[a-z]+_[a-z]+\b', full_text)
        keywords.extend(function_names)
        
        return {
            "keywords": list(set(keywords)),
            "discount_codes": list(set(discount_codes)),
            "categories": categories,
            "expected": expected,
            "observed": observed,
            "title": title
        }
    
    def find_relevant_files(self, signals: Dict[str, Any], repo_root: str) -> List[str]:
        """
        Search repository for files likely related to the bug.
        
        Returns list of file paths.
        """
        self.log("Searching for relevant files...")
        
        relevant_files = set()
        search_terms = signals["keywords"] + signals["discount_codes"]
        
        for term in search_terms[:5]:  # Limit searches
            result = self.tools["search_repo"](term, repo_root)
            if result["ok"]:
                for match in result["matches"][:10]:
                    relevant_files.add(match["file_path"])
        
        # Prioritize certain file patterns
        prioritized = []
        for f in relevant_files:
            if "discount" in f or "pricing" in f:
                prioritized.insert(0, f)
            else:
                prioritized.append(f)
        
        self.log(f"Found {len(prioritized)} relevant files")
        return prioritized[:5]  # Limit to top 5
    
    def read_relevant_code(self, file_paths: List[str], repo_root: str) -> Dict[str, str]:
        """
        Read content of relevant files.
        
        Returns dict mapping file_path to content.
        """
        self.log(f"Reading {len(file_paths)} files...")
        
        code_map = {}
        for file_path in file_paths:
            full_path = Path(repo_root) / file_path
            result = self.tools["read_file"](str(full_path), repo_root)
            if result["ok"]:
                code_map[file_path] = result["content"]
        
        return code_map
    
    def generate_test(self, signals: Dict[str, Any], code_map: Dict[str, str],
                     repo_root: str) -> Dict[str, Any]:
        """
        Generate a pytest regression test based on signals and code.
        
        Returns dict with:
            - test_code: Generated test code
            - test_filename: Suggested filename
        """
        self.log("Generating regression test...")
        
        # Use template system to generate test
        from .test_templates import select_template
        
        # Select appropriate template based on bug report
        template_class = select_template(signals)
        template = template_class()
        
        self.log(f"Using template: {template_class.__name__}")
        
        # Generate test code using template
        test_code = template.generate_test(signals, code_map, repo_root)
        
        # Determine test filename from bug title
        title_slug = re.sub(r'[^a-z0-9]+', '_', signals["title"].lower())
        test_filename = f"test_bug_{title_slug[:30]}.py"
        
        return {
            "test_code": test_code,
            "test_filename": test_filename
        }
    
    def run(self, bug_data: Dict[str, Any], repo_root: str, max_iterations: int = 5) -> Dict[str, Any]:
        """
        Main agent loop.
        
        Returns dict with:
            - success: bool
            - test_path: Path to generated test
            - iterations: Number of iterations used
            - failure_message: Test failure message if applicable
            - right_reason: Whether test failed for the right reason
        """
        self.log(f"Starting agent with max {max_iterations} iterations")
        
        # Parse bug report
        signals = self.parse_bug_report(bug_data)
        self.log(f"Extracted signals: {len(signals['keywords'])} keywords, "
                f"{len(signals['discount_codes'])} discount codes")
        
        # Find relevant files
        relevant_files = self.find_relevant_files(signals, repo_root)
        if not relevant_files:
            return {
                "success": False,
                "test_path": None,
                "iterations": 1,
                "failure_message": "No relevant files found",
                "right_reason": False
            }
        
        # Read code
        code_map = self.read_relevant_code(relevant_files, repo_root)
        
        # Generate test
        test_info = self.generate_test(signals, code_map, repo_root)
        
        # Check if test generation failed
        if test_info.get("error") or not test_info.get("test_code"):
            return {
                "success": False,
                "test_path": None,
                "iterations": 1,
                "failure_message": test_info.get("error", "Failed to generate test"),
                "right_reason": False
            }
        
        # Write test
        test_rel_path = f"tests/{test_info['test_filename']}"
        write_result = self.tools["write_test"](
            test_rel_path,
            test_info["test_code"],
            repo_root
        )
        
        if not write_result["ok"]:
            return {
                "success": False,
                "test_path": None,
                "iterations": 1,
                "failure_message": write_result["error"],
                "right_reason": False
            }
        
        test_path = write_result["path"]
        self.log(f"Generated test: {test_path}")
        
        # Run test
        run_result = self.tools["run_pytest"](test_rel_path, repo_root)
        
        if not run_result["ok"]:
            return {
                "success": False,
                "test_path": test_path,
                "iterations": 1,
                "failure_message": run_result["error"],
                "right_reason": False
            }
        
        # Check if test failed (which is what we want for a bug reproduction)
        test_failed = run_result["exit_code"] != 0
        failure_messages = run_result["failure_messages"]
        
        # Right-reason check with optional watsonx.ai judge
        from .right_reason import check_right_reason_with_fallback
        
        right_reason_result = check_right_reason_with_fallback(
            run_result,
            signals,
            test_info["test_code"],
            bug_data,
            verbose=self.verbose
        )
        
        return {
            "success": test_failed and right_reason_result["match"],
            "test_path": test_path,
            "iterations": 1,
            "failure_message": "\n".join(failure_messages) if failure_messages else "Test passed (no bug reproduced)",
            "right_reason": right_reason_result["match"],
            "judge_provider": right_reason_result["provider"],
            "judge_reasoning": right_reason_result.get("reasoning", "")
        }

# Made with Bob
