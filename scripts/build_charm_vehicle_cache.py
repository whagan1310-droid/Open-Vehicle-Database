#!/usr/bin/env python3
"""
Scrape public https://charm.li/{Make}/{year}/ pages and write a compact JSON cache
for the catalog picker (model/engine → manual index URLs). Browsers cannot fetch
charm.li from static catalog/ (CORS), so this is build-time data.

Be polite: use modest delays; run occasionally, not in a tight loop.

Scopes:
  manifest — only (makeKey, year) pairs that appear in catalog/charm-manual-index.json
             (smallest cache, good default for repos with partial exports).
  coverage — every (makeKey, year) from catalog/charm-coverage.json (many requests;
             large JSON — use when you want the full picker without local exports).

Merge / resume (default): if the output file already exists, its byMakeYear is loaded first.
Each (makeKey, year) that already has an entry is skipped unless --refetch. After each
successful fetch the file is rewritten (--checkpoint-every to batch writes). Ctrl+C
writes the partial cache so you can re-run the same command to continue.

Usage:
  python scripts/build_charm_vehicle_cache.py
  python scripts/build_charm_vehicle_cache.py --scope coverage --sleep 0.2
  python scripts/build_charm_vehicle_cache.py --scope coverage --checkpoint-every 10
  python scripts/build_charm_vehicle_cache.py --fresh --scope manifest
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

UA = "Open-Vehicle-Database-vehicle-cache/1.0 (community mirror; +https://github.com)"

# Same heuristic as scripts/build_charm_manifest.split_model_engine
def split_model_engine(rest_after_make: str) -> tuple[str, str]:
    rest = (rest_after_make or "").strip()
    if not rest:
        return "", ""
    m = re.search(r"\s((?:L\d|V\d)\d*-\S+)", rest)
    if not m:
        return rest, ""
    cut = m.start() + 1
    return rest[:cut].strip(), rest[cut:].strip()


LINK_RE = re.compile(r'<li><a href="(/[^"]+/)">([^<]+)</a>')


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read().decode("utf-8", errors="replace")


def charm_make_path_segment(charm_name: str) -> str:
    """Path segment as used on charm.li (spaces → %20, etc.)."""
    return urllib.parse.quote(charm_name, safe="")


def parse_vehicle_rows(html: str) -> list[dict]:
    rows: list[dict] = []
    for path, label in LINK_RE.findall(html):
        label = label.strip()
        if not label or not path.startswith("/"):
            continue
        # Expect /Make/year/Variant.../
        parts = [p for p in path.split("/") if p]
        if len(parts) < 3:
            continue
        pm, pe = split_model_engine(label)
        if not pm:
            pm = label
        rows.append(
            {
                "path": path if path.endswith("/") else path + "/",
                "label": label,
                "pickerModel": pm,
                "pickerEngine": pe,
            }
        )
    return rows


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def pairs_from_manifest(root: Path) -> set[tuple[str, int]]:
    p = root / "catalog" / "charm-manual-index.json"
    data = load_json(p)
    out: set[tuple[str, int]] = set()
    for m in data.get("manuals") or []:
        mk = (m.get("make") or "").strip().upper()
        y = m.get("year")
        if mk and isinstance(y, int):
            out.add((mk, y))
    return out


def pairs_from_coverage(root: Path) -> set[tuple[str, int]]:
    p = root / "catalog" / "charm-coverage.json"
    data = load_json(p)
    out: set[tuple[str, int]] = set()
    for row in data.get("makes") or []:
        mk = (row.get("makeKey") or "").strip().upper()
        name = (row.get("charmName") or "").strip()
        if not mk or not name:
            continue
        for y in row.get("years") or []:
            if isinstance(y, int):
                out.add((mk, y))
    return out


def charm_name_for_make(root: Path, make_key: str) -> str | None:
    p = root / "catalog" / "charm-coverage.json"
    if not p.is_file():
        return None
    data = load_json(p)
    for row in data.get("makes") or []:
        if (row.get("makeKey") or "").strip().upper() == make_key:
            return (row.get("charmName") or "").strip() or None
    return None


def load_existing_by_make_year(out_path: Path) -> dict[str, dict[str, list[dict]]]:
    """Load byMakeYear from a prior run for merge/resume."""
    if not out_path.is_file():
        return {}
    try:
        data = load_json(out_path)
        raw = data.get("byMakeYear") or {}
        if not isinstance(raw, dict):
            return {}
        out: dict[str, dict[str, list[dict]]] = {}
        for mk, years in raw.items():
            if not isinstance(years, dict):
                continue
            mk_norm = str(mk).strip().upper()
            bucket: dict[str, list[dict]] = {}
            for yk, vehicles in years.items():
                if isinstance(vehicles, list):
                    bucket[str(yk)] = vehicles
            if bucket:
                out[mk_norm] = bucket
        return out
    except (json.JSONDecodeError, OSError, TypeError) as e:
        print(f"WARN: could not load existing cache for merge ({e}); starting empty.")
        return {}


def write_cache_payload(
    out_path: Path,
    *,
    base: str,
    scope: str,
    by_make_year: dict[str, dict[str, list[dict]]],
) -> None:
    payload = {
        "description": "Scraped public charm.li year index pages — rebuild with "
        "scripts/build_charm_vehicle_cache.py; do not edit by hand.",
        "version": 1,
        "charmBaseUrl": base,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "scope": scope,
        "byMakeYear": by_make_year,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--scope",
        choices=("manifest", "coverage"),
        default="manifest",
        help="Which (make,year) pairs to fetch (default: manifest only).",
    )
    ap.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root (default: parent of scripts/).",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output JSON path (default: catalog/charm-vehicle-cache.json).",
    )
    ap.add_argument(
        "--sleep",
        type=float,
        default=0.15,
        help="Seconds between HTTP requests (default: 0.15).",
    )
    ap.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore existing output file; start with an empty byMakeYear.",
    )
    ap.add_argument(
        "--no-merge",
        action="store_true",
        help="Same as --fresh (do not load prior byMakeYear from output).",
    )
    ap.add_argument(
        "--refetch",
        action="store_true",
        help="Re-download every (makeKey, year) even if already present in the cache file.",
    )
    ap.add_argument(
        "--checkpoint-every",
        type=int,
        default=1,
        metavar="N",
        help="Write JSON after every N newly fetched pages (default: 1). Use a larger "
        "value to reduce disk I/O on huge caches.",
    )
    args = ap.parse_args()
    root: Path = args.root
    out_path = args.out or (root / "catalog" / "charm-vehicle-cache.json")

    if args.checkpoint_every < 1:
        raise SystemExit("--checkpoint-every must be >= 1")

    cov_path = root / "catalog" / "charm-coverage.json"
    if not cov_path.is_file():
        raise SystemExit(f"Missing {cov_path}; run sync_charm_coverage_from_charm_li.py first.")

    cov = load_json(cov_path)
    base = (cov.get("charmBaseUrl") or "https://charm.li").rstrip("/")

    if args.scope == "manifest":
        pairs = pairs_from_manifest(root)
        if not pairs:
            print("No (make,year) pairs in charm-manual-index.json — writing empty byMakeYear.")
    else:
        pairs = pairs_from_coverage(root)

    fresh = args.fresh or args.no_merge
    if fresh:
        by_make_year: dict[str, dict[str, list[dict]]] = {}
        print("Starting with empty cache (--fresh / --no-merge).")
    else:
        by_make_year = load_existing_by_make_year(out_path)
        if by_make_year:
            n = sum(len(years) for years in by_make_year.values())
            print(f"Loaded {n} (makeKey, year) entries from existing {out_path} for merge/resume.")

    sorted_pairs = sorted(pairs, key=lambda t: (t[0], t[1]))
    total = len(sorted_pairs)
    pending_writes = 0

    def maybe_checkpoint(force: bool = False) -> None:
        nonlocal pending_writes
        if force or pending_writes >= args.checkpoint_every:
            write_cache_payload(
                out_path, base=base, scope=args.scope, by_make_year=by_make_year
            )
            pending_writes = 0

    try:
        for i, (make_key, year) in enumerate(sorted_pairs, start=1):
            ys = str(year)
            if (
                not args.refetch
                and ys in by_make_year.get(make_key, {})
            ):
                n = len(by_make_year[make_key][ys])
                print(f"[{i}/{total}] {make_key} {year} SKIP (cached, {n} vehicles)")
                continue

            charm_name = charm_name_for_make(root, make_key)
            if not charm_name:
                print(f"SKIP {make_key} {year}: no charmName in charm-coverage.json")
                continue
            seg = charm_make_path_segment(charm_name)
            url = f"{base}/{seg}/{year}/"
            try:
                html = fetch(url)
            except urllib.error.HTTPError as e:
                print(f"SKIP {make_key} {year}: HTTP {e.code}")
                time.sleep(args.sleep)
                continue
            except urllib.error.URLError as e:
                print(f"SKIP {make_key} {year}: {e}")
                time.sleep(args.sleep)
                continue

            rows = parse_vehicle_rows(html)
            by_make_year.setdefault(make_key, {})[ys] = rows
            pending_writes += 1
            print(f"[{i}/{total}] {make_key} {year} -> {len(rows)} vehicles")
            maybe_checkpoint()
            time.sleep(args.sleep)

        maybe_checkpoint(force=True)
        print(f"Done. Saved {out_path}")
    except KeyboardInterrupt:
        print("\nInterrupted — writing partial cache (merge/resume safe)...")
        write_cache_payload(
            out_path, base=base, scope=args.scope, by_make_year=by_make_year
        )
        print(f"Wrote partial {out_path}; re-run the same command to continue.")
        raise SystemExit(130) from None


if __name__ == "__main__":
    main()
