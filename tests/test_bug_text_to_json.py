"""Tests for bug_text_to_json.py converter."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from bug_text_to_json import (
    convert_text_to_bug_json,
    extract_title,
    extract_expected,
    extract_observed
)


class TestExtractTitle(unittest.TestCase):
    """Test title extraction logic."""
    
    def test_first_sentence(self):
        """Should extract first sentence if under 80 chars."""
        text = "This is the first sentence. This is the second sentence."
        result = extract_title(text)
        self.assertEqual(result, "This is the first sentence.")
    
    def test_first_80_chars_when_no_sentence(self):
        """Should extract first 80 chars when no sentence boundary."""
        text = "A" * 100
        result = extract_title(text)
        self.assertEqual(len(result), 83)  # 80 + "..."
        self.assertTrue(result.endswith("..."))
    
    def test_first_80_chars_when_sentence_too_long(self):
        """Should extract first 80 chars when first sentence is too long."""
        text = "A" * 100 + ". Second sentence."
        result = extract_title(text)
        self.assertEqual(len(result), 83)  # 80 + "..."
        self.assertTrue(result.endswith("..."))
    
    def test_exclamation_mark(self):
        """Should handle exclamation marks as sentence boundaries."""
        text = "Bug found! More details here."
        result = extract_title(text)
        self.assertEqual(result, "Bug found!")
    
    def test_question_mark(self):
        """Should handle question marks as sentence boundaries."""
        text = "Why is this broken? Because of a bug."
        result = extract_title(text)
        self.assertEqual(result, "Why is this broken?")


class TestExtractExpected(unittest.TestCase):
    """Test expected behavior extraction."""
    
    def test_finds_expected_keyword(self):
        """Should find sentence with 'expected' keyword."""
        text = "Bug in checkout. Expected 20% discount. Got 0% instead."
        result = extract_expected(text)
        self.assertEqual(result, "Expected 20% discount")
    
    def test_case_insensitive(self):
        """Should be case insensitive."""
        text = "Bug found. EXPECTED behavior is 10.0. Actual is 0.0."
        result = extract_expected(text)
        self.assertEqual(result, "EXPECTED behavior is 10.0")
    
    def test_no_expected_returns_empty(self):
        """Should return empty string when no 'expected' found."""
        text = "Bug in the system. It should work correctly."
        result = extract_expected(text)
        self.assertEqual(result, "")
    
    def test_word_boundary(self):
        """Should match 'expected' as whole word."""
        text = "Unexpected behavior. Expected result is 5."
        result = extract_expected(text)
        self.assertEqual(result, "Expected result is 5")


class TestExtractObserved(unittest.TestCase):
    """Test observed behavior extraction."""
    
    def test_finds_observed_keyword(self):
        """Should find sentence with 'observed' keyword."""
        text = "Bug in checkout. Expected 20%. Observed 0% discount."
        result = extract_observed(text)
        self.assertEqual(result, "Observed 0% discount")
    
    def test_finds_actual_keyword(self):
        """Should find sentence with 'actual' keyword."""
        text = "Expected 10.0. Actual value is 0.0."
        result = extract_observed(text)
        self.assertEqual(result, "Actual value is 0.0")
    
    def test_finds_got_keyword(self):
        """Should find sentence with 'got' keyword."""
        text = "Expected 10.0. Got 0.0 instead."
        result = extract_observed(text)
        self.assertEqual(result, "Got 0.0 instead")
    
    def test_finds_returns_keyword(self):
        """Should find sentence with 'returns' keyword."""
        text = "Function parse_price returns 0.0 but should return 10.0."
        result = extract_observed(text)
        self.assertEqual(result, "Function parse_price returns 0.0 but should return 10.0")
    
    def test_finds_shows_keyword(self):
        """Should find sentence with 'shows' keyword."""
        text = "Expected $20 off. Checkout shows $100 total."
        result = extract_observed(text)
        self.assertEqual(result, "Checkout shows $100 total")
    
    def test_case_insensitive(self):
        """Should be case insensitive."""
        text = "Expected 5. ACTUAL is 0."
        result = extract_observed(text)
        self.assertEqual(result, "ACTUAL is 0")
    
    def test_no_keyword_returns_empty(self):
        """Should return empty string when no keyword found."""
        text = "Bug in the system. It is broken."
        result = extract_observed(text)
        self.assertEqual(result, "")


class TestConvertTextToBugJson(unittest.TestCase):
    """Test full conversion logic."""
    
    def test_basic_conversion(self):
        """Should convert text to JSON with all fields."""
        text = "Discount code DOUBLE is broken. Expected 20% off. Got 0% discount."
        result = convert_text_to_bug_json(text)
        
        self.assertEqual(result["id"], "BUG-local-001")
        self.assertEqual(result["title"], "Discount code DOUBLE is broken.")
        self.assertEqual(result["description"], text)
        self.assertEqual(result["reporter"], "manual")
        self.assertEqual(result["severity"], "medium")
        self.assertEqual(result["expected"], "Expected 20% off")
        self.assertEqual(result["observed"], "Got 0% discount")
    
    def test_custom_id(self):
        """Should use custom bug ID."""
        text = "Bug found."
        result = convert_text_to_bug_json(text, bug_id="BUG-123")
        self.assertEqual(result["id"], "BUG-123")
    
    def test_custom_reporter(self):
        """Should use custom reporter."""
        text = "Bug found."
        result = convert_text_to_bug_json(text, reporter="qa-team")
        self.assertEqual(result["reporter"], "qa-team")
    
    def test_custom_severity(self):
        """Should use custom severity."""
        text = "Bug found."
        result = convert_text_to_bug_json(text, severity="high")
        self.assertEqual(result["severity"], "high")
    
    def test_no_expected_or_observed(self):
        """Should have empty strings when expected/observed not found."""
        text = "There is a bug in the system."
        result = convert_text_to_bug_json(text)
        self.assertEqual(result["expected"], "")
        self.assertEqual(result["observed"], "")


class TestCLIIntegration(unittest.TestCase):
    """Test CLI functionality."""
    
    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_inline_text_conversion(self):
        """Should convert inline text to JSON file."""
        output_path = os.path.join(self.temp_dir, "bug.json")
        text = "QA says DOUBLE discount is broken on gift cards. Expected 20% off but checkout shows $100."
        
        # Simulate CLI call
        import subprocess
        result = subprocess.run([
            sys.executable,
            "scripts/bug_text_to_json.py",
            "--text", text,
            "--out", output_path
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data["id"], "BUG-local-001")
        self.assertEqual(data["reporter"], "manual")
        self.assertEqual(data["severity"], "medium")
        self.assertIn("DOUBLE discount", data["title"])
        self.assertEqual(data["description"], text)
        self.assertIn("Expected", data["expected"])
        self.assertIn("shows", data["observed"])
    
    def test_file_input_conversion(self):
        """Should convert file input to JSON."""
        input_path = os.path.join(self.temp_dir, "input.txt")
        output_path = os.path.join(self.temp_dir, "bug.json")
        text = "Bug in parse_price. Expected 10.0. Returns 0.0."
        
        with open(input_path, 'w') as f:
            f.write(text)
        
        import subprocess
        result = subprocess.run([
            sys.executable,
            "scripts/bug_text_to_json.py",
            "--input", input_path,
            "--out", output_path
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data["description"], text)
    
    def test_custom_overrides(self):
        """Should apply custom ID, reporter, and severity."""
        output_path = os.path.join(self.temp_dir, "bug.json")
        
        import subprocess
        result = subprocess.run([
            sys.executable,
            "scripts/bug_text_to_json.py",
            "--text", "Bug found.",
            "--out", output_path,
            "--id", "BUG-999",
            "--reporter", "qa-team",
            "--severity", "critical"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        self.assertEqual(result.returncode, 0)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data["id"], "BUG-999")
        self.assertEqual(data["reporter"], "qa-team")
        self.assertEqual(data["severity"], "critical")
    
    def test_refuses_overwrite_without_force(self):
        """Should refuse to overwrite existing file without --force."""
        output_path = os.path.join(self.temp_dir, "bug.json")
        
        # Create existing file
        with open(output_path, 'w') as f:
            f.write("{}")
        
        import subprocess
        result = subprocess.run([
            sys.executable,
            "scripts/bug_text_to_json.py",
            "--text", "Bug found.",
            "--out", output_path
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists", result.stderr)
    
    def test_overwrites_with_force(self):
        """Should overwrite existing file with --force."""
        output_path = os.path.join(self.temp_dir, "bug.json")
        
        # Create existing file
        with open(output_path, 'w') as f:
            f.write('{"old": "data"}')
        
        import subprocess
        result = subprocess.run([
            sys.executable,
            "scripts/bug_text_to_json.py",
            "--text", "New bug.",
            "--out", output_path,
            "--force"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        self.assertEqual(result.returncode, 0)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data["description"], "New bug.")
        self.assertNotIn("old", data)
    
    def test_creates_parent_directories(self):
        """Should create parent directories if needed."""
        output_path = os.path.join(self.temp_dir, "nested", "dir", "bug.json")
        
        import subprocess
        result = subprocess.run([
            sys.executable,
            "scripts/bug_text_to_json.py",
            "--text", "Bug found.",
            "--out", output_path
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(output_path))


if __name__ == "__main__":
    unittest.main()

# Made with Bob
