#!/usr/bin/env python3
"""EightySix Demo CLI — analyze restaurant exports from the command line.

Usage:
    python cli.py sales.csv labor.xlsx refunds.csv
    python cli.py --name "Joe's Grill" *.csv *.xlsx
    python cli.py --json report.json sales.csv labor.csv
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from analysis.pipeline import run_pipeline
from output.owner_report import to_owner_json, to_internal_json, to_text_summary


def main():
    parser = argparse.ArgumentParser(
        description="EightySix — Restaurant leakage estimator"
    )
    parser.add_argument(
        "files", nargs="+", type=Path,
        help="CSV/XLSX/TSV export files to analyze"
    )
    parser.add_argument(
        "--name", default="Restaurant",
        help="Restaurant name (default: Restaurant)"
    )
    parser.add_argument(
        "--json", dest="json_out", type=Path, default=None,
        help="Write full report to JSON file"
    )
    parser.add_argument(
        "--internal", action="store_true",
        help="Show internal report (detailed evidence)"
    )

    args = parser.parse_args()

    # Validate files exist
    for f in args.files:
        if not f.exists():
            print(f"Error: file not found: {f}", file=sys.stderr)
            sys.exit(1)
        if f.suffix.lower() not in (".csv", ".xlsx", ".xls", ".tsv"):
            print(f"Warning: skipping unsupported file: {f}", file=sys.stderr)

    valid_files = [f for f in args.files if f.suffix.lower() in (".csv", ".xlsx", ".xls", ".tsv")]
    if not valid_files:
        print("Error: no valid files to analyze.", file=sys.stderr)
        sys.exit(1)

    # Run pipeline
    report = run_pipeline(valid_files, restaurant_name=args.name)

    # Output
    print(to_text_summary(report))

    if args.internal:
        print("\n--- INTERNAL REPORT ---\n")
        print(json.dumps(to_internal_json(report), indent=2, default=str))

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump({
                "owner_report": to_owner_json(report),
                "internal_report": to_internal_json(report),
            }, f, indent=2, default=str)
        print(f"\nFull report written to: {args.json_out}")


if __name__ == "__main__":
    main()
