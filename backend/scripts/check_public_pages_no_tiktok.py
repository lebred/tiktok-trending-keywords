#!/usr/bin/env python3
"""
Check that generated public pages contain no TikTok mentions.

Scans all HTML files in the public pages directory for forbidden words
and fails if any are found.

Usage:
    python -m scripts.check_public_pages_no_tiktok <PUBLIC_DIR>
"""

import sys
import argparse
from pathlib import Path
from typing import List, Tuple

# Forbidden words/phrases that should not appear in public pages
FORBIDDEN_WORDS = [
    "tiktok",
    "TikTok",
    "TIKTOK",
    "creative center",
    "Creative Center",
    "CREATIVE CENTER",
    "hashtag trend",
    "Hashtag Trend",
    "trending hashtag",
    "Trending Hashtag",
    "trending sound",
    "Trending Sound",
    "tiktok creative",
    "TikTok Creative",
    "ads.tiktok.com",
    "tiktok.com",
]


def scan_file(file_path: Path) -> List[Tuple[int, str]]:
    """
    Scan a single HTML file for forbidden words.

    Args:
        file_path: Path to HTML file

    Returns:
        List of tuples (line_number, forbidden_word) found
    """
    violations = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                line_lower = line.lower()
                for forbidden in FORBIDDEN_WORDS:
                    if forbidden.lower() in line_lower:
                        violations.append((line_num, forbidden))
    except Exception as e:
        print(f"ERROR: Failed to read {file_path}: {e}", file=sys.stderr)
        return [(0, f"READ_ERROR: {e}")]

    return violations


def check_directory(public_dir: Path) -> bool:
    """
    Check all HTML files in the public directory.

    Args:
        public_dir: Path to public pages directory

    Returns:
        True if all checks pass, False otherwise
    """
    if not public_dir.exists():
        print(f"ERROR: Directory does not exist: {public_dir}", file=sys.stderr)
        return False

    if not public_dir.is_dir():
        print(f"ERROR: Not a directory: {public_dir}", file=sys.stderr)
        return False

    # Find all HTML files
    html_files = list(public_dir.rglob("*.html"))

    if not html_files:
        print(f"WARNING: No HTML files found in {public_dir}", file=sys.stderr)
        return False

    print(f"INFO: Scanning {len(html_files)} HTML file(s) in: {public_dir}")

    total_violations = 0

    for html_file in sorted(html_files):
        relative_path = html_file.relative_to(public_dir)
        print(f"INFO: Checking {relative_path}")

        violations = scan_file(html_file)

        if violations:
            total_violations += len(violations)
            for line_num, forbidden in violations:
                print(
                    f"ERROR: Found forbidden word in {relative_path}: "
                    f'"{forbidden}" (line {line_num})',
                    file=sys.stderr,
                )

    if total_violations > 0:
        print(
            f"\nERROR: ✗ Check failed: Found {total_violations} forbidden word(s)",
            file=sys.stderr,
        )
        return False

    print(f"\nINFO: ✓ All pages passed: No TikTok mentions found")
    return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Check public pages for forbidden TikTok mentions"
    )
    parser.add_argument(
        "public_dir",
        type=str,
        help="Path to public pages directory",
    )

    args = parser.parse_args()

    public_dir = Path(args.public_dir).resolve()

    success = check_directory(public_dir)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

