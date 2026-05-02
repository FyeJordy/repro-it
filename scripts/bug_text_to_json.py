#!/usr/bin/env python3
"""
Convert plain-text bug reports to JSON format for Repro-It.

Usage:
    # From inline text
    python3 scripts/bug_text_to_json.py --text "Bug description..." --out bugs/bug.json
    
    # From input file
    python3 scripts/bug_text_to_json.py --input bugs/raw_bug.txt --out bugs/bug.json
    
    # With overrides
    python3 scripts/bug_text_to_json.py --text "..." --out bugs/bug.json --id BUG-123 --severity high --reporter qa-team
"""

import argparse
import json
import os
import re
import sys


def extract_title(text):
    """Extract title from text (first sentence or first 80 chars)."""
    # Try to find first sentence
    match = re.match(r'^([^.!?]+[.!?])', text.strip())
    if match:
        title = match.group(1).strip()
        if len(title) <= 80:
            return title
    
    # Fall back to first 80 characters
    title = text.strip()[:80]
    if len(text.strip()) > 80:
        title = title.rstrip() + "..."
    return title


def extract_expected(text):
    """Extract expected behavior from text."""
    # Look for sentences containing "expected"
    # Split on sentence-ending punctuation followed by whitespace or end of string
    # This preserves decimal numbers like 10.0 and 0.0
    sentences = re.split(r'[.!?]+(?:\s+|$)', text)
    for sentence in sentences:
        if re.search(r'\bexpected\b', sentence, re.IGNORECASE):
            return sentence.strip()
    return ""


def extract_observed(text):
    """Extract observed behavior from text."""
    # Look for sentences containing observed/actual/got/returns/shows
    keywords = r'\b(observed|actual|got|returns?|shows?)\b'
    # Split on sentence-ending punctuation followed by whitespace or end of string
    # This preserves decimal numbers like 10.0 and 0.0
    sentences = re.split(r'[.!?]+(?:\s+|$)', text)
    for sentence in sentences:
        if re.search(keywords, sentence, re.IGNORECASE):
            return sentence.strip()
    return ""


def convert_text_to_bug_json(text, bug_id="BUG-local-001", reporter="manual", severity="medium"):
    """Convert plain text to bug JSON format."""
    return {
        "id": bug_id,
        "title": extract_title(text),
        "description": text.strip(),
        "reporter": reporter,
        "severity": severity,
        "expected": extract_expected(text),
        "observed": extract_observed(text)
    }


def main():
    parser = argparse.ArgumentParser(
        description="Convert plain-text bug reports to JSON format for Repro-It"
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--text", help="Bug report text inline")
    input_group.add_argument("--input", help="Path to input text file")
    
    # Output
    parser.add_argument("--out", required=True, help="Output JSON file path")
    
    # Optional overrides
    parser.add_argument("--id", default="BUG-local-001", help="Bug ID (default: BUG-local-001)")
    parser.add_argument("--reporter", default="manual", help="Reporter name (default: manual)")
    parser.add_argument("--severity", default="medium", 
                       choices=["low", "medium", "high", "critical"],
                       help="Bug severity (default: medium)")
    
    # Safety
    parser.add_argument("--force", action="store_true", 
                       help="Overwrite output file if it exists")
    
    args = parser.parse_args()
    
    # Get input text
    if args.text:
        text = args.text
    else:
        try:
            with open(args.input, 'r', encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading input file: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Check if output file exists
    if os.path.exists(args.out) and not args.force:
        print(f"Error: Output file already exists: {args.out}", file=sys.stderr)
        print("Use --force to overwrite", file=sys.stderr)
        sys.exit(1)
    
    # Convert to JSON
    bug_json = convert_text_to_bug_json(text, args.id, args.reporter, args.severity)
    
    # Create parent directories if needed
    output_dir = os.path.dirname(args.out)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Write output
    try:
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump(bug_json, f, indent=2)
            f.write('\n')  # Add trailing newline
        print(f"Bug report written to: {args.out}")
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
