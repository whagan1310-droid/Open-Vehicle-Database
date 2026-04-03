#!/usr/bin/env python3
"""
Scan CHARM export folders (e.g. Acura/) for index.html and write catalog/charm-manual-index.json.

Run from repository root:
  python scripts/build_charm_manifest.py

CHARM folders to scan default to charm-manifest.config.json key "charmDirs"
(or pass --charm-dirs). Each manual href is relative to catalog/index.html.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

def parse_title(first_folder_name: str) -> tuple[int | None, str | None, str | None]:
    """Parse leading year, make token, and remainder from CHARM-style folder title."""
    m = re.match(r"^(\d{4})\s+(\S+)\s+(.+)$", first_folder_name.strip())
    if not m:
        return None, None, None
    year = int(m.group(1))
    make = m.group(2).upper()
    rest = m.group(3).strip()
    return year, make, rest


def split_model_engine(rest_after_make: str) -> tuple[str, str]:
    """
    Split CHARM remainder into a model line and an engine line.
    Engine is detected at the first L#/V# displacement token (e.g. L4-1590cc, V6-3.0L).
    """
    rest = (rest_after_make or "").strip()
    if not rest:
        return "", ""
    m = re.search(r"\s((?:L\d|V\d)\d*-\S+)", rest)
    if not m:
        return rest, ""
    cut = m.start() + 1
    return rest[:cut].strip(), rest[cut:].strip()


def find_manuals(charm_make_root: Path) -> list[dict]:
    """Index manuals under one make folder (e.g. repo_root/Acura)."""
    manuals: list[dict] = []
    if not charm_make_root.is_dir():
        return manuals

    repo_root = charm_make_root.parent
    expected_top = charm_make_root.name

    for dirpath, _, filenames in os.walk(charm_make_root):
        if "index.html" not in filenames:
            continue
        full = Path(dirpath) / "index.html"
        try:
            rel = full.relative_to(repo_root)
        except ValueError:
            continue
        parts = rel.parts
        if len(parts) < 3 or parts[0] != expected_top:
            continue
        first_seg = parts[1]
        year, make, rest = parse_title(first_seg)
        picker_model, picker_engine = split_model_engine(rest)
        posix_rel = rel.as_posix()
        href = "../" + posix_rel
        manuals.append(
            {
                "href": href,
                "title": first_seg,
                "year": year,
                "make": make,
                "restAfterMake": rest,
                "pickerModel": picker_model,
                "pickerEngine": picker_engine,
            }
        )

    return manuals


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root (default: parent of scripts/)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output JSON path (default: <root>/catalog/charm-manual-index.json)",
    )
    ap.add_argument(
        "--charm-dirs",
        nargs="*",
        default=None,
        help="CHARM export folders under repo root (default: charm-manifest.config.json)",
    )
    args = ap.parse_args()
    root: Path = args.root
    out = args.out or (root / "catalog" / "charm-manual-index.json")
    charm_dirs = args.charm_dirs
    if charm_dirs is None:
        cfg_path = root / "charm-manifest.config.json"
        if cfg_path.is_file():
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            charm_dirs = cfg.get("charmDirs") or ["Acura"]
        else:
            charm_dirs = ["Acura"]
    all_manuals: list[dict] = []
    for d in charm_dirs:
        all_manuals.extend(find_manuals(root / d))
    all_manuals.sort(key=lambda x: (x["year"] or 0, x["title"] or ""))
    payload = {
        "generatedFor": "Open-Vehicle-Database catalog → CHARM manuals",
        "pickerNote": "Make/year/model/engine are derived from CHARM folder names only (no external vehicle DB).",
        "charmDirs": charm_dirs,
        "manuals": all_manuals,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(all_manuals)} manuals to {out}")


if __name__ == "__main__":
    main()
