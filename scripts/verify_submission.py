#!/usr/bin/env python3
"""
Deterministic local readiness checker for hackathon submissions.
Validates project structure, content, and tests before submission.
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict


class SubmissionVerifier:
    """Validates hackathon submission readiness."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.failures: List[str] = []
        self.passes: List[str] = []
        
    def check_mark(self, passed: bool) -> str:
        """Return check or cross mark."""
        return "✓" if passed else "✗"
    
    def verify_file_exists(self, filepath: str) -> bool:
        """Check if a file exists."""
        full_path = self.project_root / filepath
        exists = full_path.is_file()
        status = self.check_mark(exists)
        
        if exists:
            self.passes.append(f"{status} File exists: {filepath}")
        else:
            self.failures.append(f"{status} Missing file: {filepath}")
        
        return exists
    
    def verify_directory_exists(self, dirpath: str) -> bool:
        """Check if a directory exists."""
        full_path = self.project_root / dirpath
        exists = full_path.is_dir()
        status = self.check_mark(exists)
        
        if exists:
            self.passes.append(f"{status} Directory exists: {dirpath}")
        else:
            self.failures.append(f"{status} Missing directory: {dirpath}")
        
        return exists
    
    def verify_readme_word_count(self) -> bool:
        """Verify README.md has fewer than 450 words."""
        readme_path = self.project_root / "README.md"
        
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count words by splitting on whitespace
            words = content.split()
            word_count = len(words)
            
            passed = word_count < 450
            status = self.check_mark(passed)
            
            if passed:
                self.passes.append(f"{status} README.md word count: {word_count} < 450")
            else:
                self.failures.append(f"{status} README.md word count: {word_count} >= 450 (too long)")
            
            return passed
            
        except Exception as e:
            self.failures.append(f"✗ Error reading README.md: {e}")
            return False
    
    def is_false_positive(self, line: str, match: str, filepath: Path) -> bool:
        """Check if a secret match is a false positive."""
        line_lower = line.lower()
        
        # Exclude this verification script itself (pattern definitions)
        if filepath.name == "verify_submission.py":
            return True
        
        # Common false positive patterns
        false_positives = [
            "your-key",
            "your_api_key",
            "example-token",
            "example_token",
            "sample-key",
            "sample_key",
        ]
        
        # Check for environment variable patterns
        env_patterns = [
            r'os\.getenv\s*\(\s*["\']',
            r'os\.environ\s*\[\s*["\']',
            r'\$\{[A-Z_]+\}',
            r'process\.env\.',
        ]
        
        for pattern in env_patterns:
            if re.search(pattern, line):
                return True
        
        # Check for common placeholder text
        for fp in false_positives:
            if fp in line_lower:
                return True
        
        return False
    
    def scan_file_for_secrets(self, filepath: Path) -> List[Tuple[int, str, str]]:
        """Scan a file for exposed secrets. Returns list of (line_num, line, secret_type)."""
        secrets_found = []
        
        # Secret patterns to detect
        patterns = [
            (r'ApiKey-', "ApiKey-", True),  # case-sensitive
            (r'access_token', "access_token", False),
            (r'refresh_token', "refresh_token", False),
            (r'iam_token', "iam_token", False),
            (r'bearer\s+[a-zA-Z0-9]', "bearer token", False),
            (r'eyJ[a-zA-Z0-9]', "JWT token (eyJ)", True),  # case-sensitive
        ]
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    for pattern, secret_type, case_sensitive in patterns:
                        flags = 0 if case_sensitive else re.IGNORECASE
                        if re.search(pattern, line, flags):
                            # Check if it's a false positive
                            if not self.is_false_positive(line, secret_type, filepath):
                                secrets_found.append((line_num, line.strip(), secret_type))
        except Exception:
            # Skip files that can't be read
            pass
        
        return secrets_found
    
    def verify_no_exposed_secrets(self) -> bool:
        """Scan all text files for exposed secrets."""
        text_extensions = {'.md', '.py', '.txt', '.yml', '.yaml', '.json'}
        all_secrets = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip hidden directories and common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                filepath = Path(root) / file
                if filepath.suffix in text_extensions:
                    secrets = self.scan_file_for_secrets(filepath)
                    if secrets:
                        rel_path = filepath.relative_to(self.project_root)
                        for line_num, line, secret_type in secrets:
                            all_secrets.append((rel_path, line_num, line, secret_type))
        
        if not all_secrets:
            self.passes.append("✓ No exposed secrets found")
            return True
        else:
            self.failures.append("✗ Exposed secrets detected:")
            for rel_path, line_num, line, secret_type in all_secrets:
                self.failures.append(f"  - {rel_path}:{line_num} ({secret_type})")
                self.failures.append(f"    {line[:80]}")
            return False
    
    def run_tests(self, test_path: str, description: str) -> bool:
        """Run pytest on specified path and capture results."""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', test_path, '-v'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            passed = result.returncode == 0
            status = self.check_mark(passed)
            
            if passed:
                self.passes.append(f"{status} {description}: PASSED")
            else:
                self.failures.append(f"{status} {description}: FAILED")
                # Include relevant error output
                if result.stdout:
                    lines = result.stdout.split('\n')
                    # Get last 10 lines or FAILED lines
                    relevant_lines = [l for l in lines if 'FAILED' in l or 'ERROR' in l]
                    if relevant_lines:
                        for line in relevant_lines[:5]:  # Limit output
                            self.failures.append(f"  {line}")
            
            return passed
            
        except subprocess.TimeoutExpired:
            self.failures.append(f"✗ {description}: TIMEOUT (>60s)")
            return False
        except Exception as e:
            self.failures.append(f"✗ {description}: ERROR - {e}")
            return False
    
    def verify_all(self) -> bool:
        """Run all verification checks."""
        print("=" * 70)
        print("HACKATHON SUBMISSION VERIFICATION")
        print("=" * 70)
        print()
        
        all_passed = True
        
        # 1. File and Directory Existence
        print("1. FILE AND DIRECTORY EXISTENCE")
        print("-" * 70)
        
        required_files = [
            "README.md",
            "SUBMISSION.md",
            "DEMO.md",
            "requirements.txt",
            "repro_it.py",
            "bugs/discount_double_gift_card.json",
            "demo_repo/tests/test_pricing.py",
            ".github/workflows/tests.yml",
        ]
        
        for filepath in required_files:
            if not self.verify_file_exists(filepath):
                all_passed = False
        
        if not self.verify_directory_exists("bob_sessions"):
            all_passed = False
        
        print()
        
        # 2. Content Validation
        print("2. CONTENT VALIDATION")
        print("-" * 70)
        
        if not self.verify_readme_word_count():
            all_passed = False
        
        if not self.verify_no_exposed_secrets():
            all_passed = False
        
        print()
        
        # 3. Test Execution
        print("3. TEST EXECUTION")
        print("-" * 70)
        
        if not self.run_tests("tests/", "Main test suite (tests/)"):
            all_passed = False
        
        if not self.run_tests("demo_repo/tests/test_pricing.py", "Demo pricing tests"):
            all_passed = False
        
        print()
        
        # Print results
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        
        if self.passes:
            print(f"\n✓ PASSED ({len(self.passes)}):")
            for msg in self.passes:
                print(f"  {msg}")
        
        if self.failures:
            print(f"\n✗ FAILED ({len(self.failures)}):")
            for msg in self.failures:
                print(f"  {msg}")
        
        print()
        print("=" * 70)
        
        if all_passed:
            print("✓ OVERALL: PASS - Submission is ready!")
        else:
            print("✗ OVERALL: FAIL - Please fix the issues above")
        
        print("=" * 70)
        
        return all_passed


def main():
    """Main entry point."""
    # Determine project root (parent of scripts directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    verifier = SubmissionVerifier(project_root)
    success = verifier.verify_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

# Made with Bob
