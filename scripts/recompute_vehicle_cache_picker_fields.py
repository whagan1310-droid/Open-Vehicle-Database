#!/usr/bin/env python3
"""
Re-apply split_model_engine to every row in charm-vehicle-cache.json using each row's
\"label\" (no HTTP). Use after improving charm_label_split.py so the picker gets better
model/engine dropdowns without a full site re-scrape.

Usage (from repo root):
  python scripts/recompute_vehicle_cache_picker_fields.py
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from charm_label_split import split_model_engine


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root",
    )
    ap.add_argument(
        "--cache",
        type=Path,
        default=None,
        help="Path to charm-vehicle-cache.json (default: <root>/catalog/...)",
    )
    args = ap.parse_args()
    root: Path = args.root
    path = args.cache or (root / "catalog" / "charm-vehicle-cache.json")
    if not path.is_file():
        raise SystemExit(f"Missing {path}")

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    by_my = data.get("byMakeYear") or {}
    n = 0
    for _mk, years in by_my.items():
        if not isinstance(years, dict):
            continue
        for _ys, rows in years.items():
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                lab = (row.get("label") or "").strip()
                if not lab:
                    continue
                pm, pe = split_model_engine(lab)
                if not pm:
                    pm = lab
                row["pickerModel"] = pm
                row["pickerEngine"] = pe
                n += 1

    data["pickerFieldsRecomputedAt"] = datetime.now(timezone.utc).isoformat()
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Updated pickerModel/pickerEngine on {n} rows in {path}")


if __name__ == "__main__":
    main()
