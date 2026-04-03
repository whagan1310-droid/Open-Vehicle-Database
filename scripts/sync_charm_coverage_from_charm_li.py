#!/usr/bin/env python3
"""
Fetch make/year lists from https://charm.li/ and write catalog/charm-coverage.json.

This is the source of truth for picker coverage (fixes hand-maintained list drift).
Requires network. Be polite: run occasionally, not in a tight loop.

Usage:
  python scripts/sync_charm_coverage_from_charm_li.py
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://charm.li"
UA = "Open-Vehicle-Database-coverage-sync/1.0 (community mirror; +https://github.com)"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_home_makes(html: str) -> list[tuple[str, str]]:
    """Return list of (href_path, display_name). href_path like 'Acura' or 'Dodge%20and%20Ram'."""
    pairs = re.findall(
        r'<a href="([^"]+)/">([^<]+)</a>',
        html,
    )
    out = []
    for href, name in pairs:
        if href.startswith("http") or href.startswith("/"):
            continue
        if "about" in href.lower():
            continue
        out.append((href, name.strip()))
    return out


def parse_years_on_make_page(html: str) -> list[int]:
    return sorted({int(y) for y in re.findall(r'<a href="(\d{4})/"', html)})


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    out = root / "catalog" / "charm-coverage.json"

    home_html = fetch(f"{BASE}/")
    make_entries = parse_home_makes(home_html)
    if not make_entries:
        raise SystemExit("Could not parse makes from charm.li home page.")

    makes_out = []
    for href_path, charm_name in make_entries:
        url = f"{BASE}/{href_path}/"
        try:
            page = fetch(url)
        except urllib.error.HTTPError as e:
            print(f"SKIP {charm_name}: {e.code}")
            continue
        years = parse_years_on_make_page(page)
        if not years:
            print(f"SKIP {charm_name}: no years parsed")
            continue
        make_key = charm_name.upper()
        makes_out.append(
            {
                "charmName": charm_name,
                "makeKey": make_key,
                "years": years,
            }
        )
        time.sleep(0.15)

    makes_out.sort(key=lambda x: x["charmName"].lower())
    payload = {
        "description": "Synced from Operation CHARM (https://charm.li/) — do not edit by hand; re-run sync script.",
        "charmBaseUrl": "https://charm.li",
        "syncedFrom": BASE,
        "makes": makes_out,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(makes_out)} makes to {out}")


if __name__ == "__main__":
    main()
