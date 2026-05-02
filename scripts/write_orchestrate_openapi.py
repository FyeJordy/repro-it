#!/usr/bin/env python3
"""
Generate openapi.local.yaml from template with public URL.

Usage:
    python3 scripts/write_orchestrate_openapi.py https://your-public-url

This script reads the OpenAPI template and replaces the placeholder URL
with your actual public tunnel URL (from ngrok, cloudflared, etc.).

The generated openapi.local.yaml file is gitignored and should not be committed.
"""

import sys
from pathlib import Path


def validate_url(url: str) -> bool:
    """Validate that URL starts with http:// or https://"""
    return url.startswith('http://') or url.startswith('https://')


def main():
    if len(sys.argv) != 2:
        print("Error: Missing public URL argument", file=sys.stderr)
        print("", file=sys.stderr)
        print("Usage:", file=sys.stderr)
        print("  python3 scripts/write_orchestrate_openapi.py https://your-public-url", file=sys.stderr)
        print("", file=sys.stderr)
        print("Example:", file=sys.stderr)
        print("  python3 scripts/write_orchestrate_openapi.py https://abc123.ngrok.io", file=sys.stderr)
        sys.exit(1)
    
    public_url = sys.argv[1].rstrip('/')  # Remove trailing slash if present
    
    # Validate URL format
    if not validate_url(public_url):
        print(f"Error: Invalid URL format: {public_url}", file=sys.stderr)
        print("URL must start with http:// or https://", file=sys.stderr)
        sys.exit(1)
    
    # Determine paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    template_path = project_root / 'orchestrate_bridge' / 'openapi.template.yaml'
    output_path = project_root / 'orchestrate_bridge' / 'openapi.local.yaml'
    
    # Check template exists
    if not template_path.exists():
        print(f"Error: Template file not found: {template_path}", file=sys.stderr)
        sys.exit(1)
    
    # Read template
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading template: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Replace placeholder
    placeholder = 'https://REPLACE_ME_WITH_PUBLIC_URL'
    if placeholder not in content:
        print(f"Warning: Placeholder '{placeholder}' not found in template", file=sys.stderr)
    
    updated_content = content.replace(placeholder, public_url)
    
    # Write output
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Success
    print(f"✓ Generated OpenAPI specification")
    print(f"  Template: {template_path}")
    print(f"  Output:   {output_path}")
    print(f"  URL:      {public_url}")
    print("")
    print("Next steps:")
    print("  1. Import this OpenAPI spec into Orchestrate as a tool")
    print("  2. Ask Orchestrate to run Repro-It using the run_repro_it_demo operation")
    print("")
    print("Note: This file is gitignored and should not be committed.")


if __name__ == '__main__':
    main()

# Made with Bob
