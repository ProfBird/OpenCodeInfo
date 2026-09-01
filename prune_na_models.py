#!/usr/bin/env python3
"""Remove N.A. models from models.json after they have been N.A. for over 6 months.

Companion to update_zen_prices.py, which never removes rows — it only flags
them `na: true` and records `naSince` (the date the model was first flagged).
This script reaps rows whose `naSince` is older than the cutoff (default
6 months). Rows missing a parseable `naSince` are never touched and are
reported, so nothing is removed on a hunch.

Run periodically; the daily GitHub Actions job (.github/workflows/
update_models.yml) runs it right after the data update, before committing.

Usage:
    python3 prune_na_models.py --output docs/models.json           # prune
    python3 prune_na_models.py --dry-run --output docs/models.json # preview
    python3 prune_na_models.py --months 12                         # custom cutoff
"""
import argparse
import calendar
import json
import sys
from datetime import date
from pathlib import Path

DEFAULT_MODELS_PATH = Path("docs/models.json")


def cutoff_date(today: date, months: int) -> date:
    """Same calendar day `months` months earlier, clamped to month end."""
    y, m = today.year, today.month - months
    while m <= 0:
        m += 12
        y -= 1
    return date(y, m, min(today.day, calendar.monthrange(y, m)[1]))


def main():
    parser = argparse.ArgumentParser(
        description="Remove models that have been N.A. for longer than the cutoff (default 6 months).")
    parser.add_argument("--output", type=Path, default=DEFAULT_MODELS_PATH)
    parser.add_argument("--months", type=int, default=6,
                        help="Remove models N.A. for more than this many months (default: 6)")
    parser.add_argument("--dry-run", action="store_true", help="Report without writing")
    args = parser.parse_args()

    data = json.loads(args.output.read_text(encoding="utf-8"))
    models = data.get("models", [])
    today = date.today()
    cutoff = cutoff_date(today, args.months)

    removed, kept = [], []
    keep = []
    for m in models:
        if m.get("na"):
            since_raw = m.get("naSince")
            try:
                since = date.fromisoformat(since_raw) if since_raw else None
            except (TypeError, ValueError):
                since = None
            if since is None:
                kept.append((m["name"], "no parseable naSince — skipped"))
                keep.append(m)
                continue
            if since <= cutoff:
                removed.append((m["name"], since_raw))
                if not args.dry_run:
                    continue
            else:
                kept.append((m["name"], f"N.A. since {since_raw} (not past {args.months}-month cutoff {cutoff})"))
        keep.append(m)

    if removed:
        print(f"\n{len(removed)} N.A. model(s) past the {args.months}-month cutoff"
              + (" (dry-run)" if args.dry_run else "") + ":", file=sys.stderr)
        for name, since in removed:
            print(f"  - {name:34} N.A. since {since}", file=sys.stderr)
    else:
        print(f"No N.A. models past the {args.months}-month cutoff (cutoff date {cutoff}).", file=sys.stderr)
    for name, why in kept:
        print(f"  kept: {name:34} {why}", file=sys.stderr)

    if removed and not args.dry_run:
        data["models"] = keep
        args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\nWrote {args.output} ({len(keep)} models remaining)", file=sys.stderr)
    elif args.dry_run and removed:
        print("\nDry-run: no file written.", file=sys.stderr)
    elif not removed:
        print("Nothing to prune.", file=sys.stderr)


if __name__ == "__main__":
    main()
