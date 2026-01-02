#!/usr/bin/env python3
"""
Script to run the daily pipeline manually.

Usage:
    python -m scripts.run_daily_pipeline [--date YYYY-MM-DD] [--max-keywords N]
"""

import sys
import os
from pathlib import Path
from datetime import date
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.services.daily_pipeline import run_daily_pipeline
from app.utils.logging import setup_logging

logger = setup_logging()


def main():
    """Main function to run the daily pipeline."""
    parser = argparse.ArgumentParser(description="Run the daily pipeline")
    parser.add_argument(
        "--date",
        type=str,
        help="Snapshot date (YYYY-MM-DD), default: today",
    )
    parser.add_argument(
        "--max-keywords",
        type=int,
        help="Maximum number of keywords to process (default: all)",
    )

    args = parser.parse_args()

    # Parse date if provided
    snapshot_date = None
    if args.date:
        try:
            snapshot_date = date.fromisoformat(args.date)
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
            sys.exit(1)

    logger.info("Starting daily pipeline")
    logger.info(f"Snapshot date: {snapshot_date or date.today()}")
    if args.max_keywords:
        logger.info(f"Max keywords: {args.max_keywords}")

    try:
        results = run_daily_pipeline(
            snapshot_date=snapshot_date, max_keywords=args.max_keywords
        )

        # Print results
        print("\n" + "=" * 60)
        print("Pipeline Execution Results")
        print("=" * 60)
        print(f"Snapshot Date: {results['snapshot_date']}")
        print(f"Duration: {results.get('duration_seconds', 0):.2f} seconds")
        print(f"Keywords Fetched: {results['keywords_fetched']}")
        print(f"Keywords Saved: {results['keywords_saved']}")
        print(f"Scores Calculated: {results['scores_calculated']}")
        print(f"Scores Failed: {results['scores_failed']}")
        print(f"Success: {results.get('success', False)}")

        if results.get("errors"):
            print(f"\nErrors ({len(results['errors'])}):")
            for error in results["errors"]:
                print(f"  - {error}")

        print("=" * 60)

        if results.get("success"):
            logger.info("Pipeline completed successfully")
            sys.exit(0)
        else:
            logger.warning("Pipeline completed with errors")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error running pipeline: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

