#!/usr/bin/env python3
"""
Build catalog/charm-section-toc-cache.json: Repair + Parts table-of-contents titles
per vehicle path (same data the bookmarklet collects), using HTTP from this machine.

Reads unique paths from catalog/charm-vehicle-cache.json. Merge/resume: existing
byPath entries are skipped unless --refetch.

Full coverage can mean tens of thousands of requests; use --limit or --only-path
for tests. To commit on GitHub (100 MB file limit), gzip the output for the catalog:
  python -c "import gzip,shutil; shutil.copyfileobj(open('catalog/charm-section-toc-cache.json','rb'), gzip.open('catalog/charm-section-toc-cache.json.gz','wb',compresslevel=9))"
The picker loads .json locally first, then .json.gz. On Windows / Git Bash, avoid % in the argument (shell may strip it); use
a quoted path with spaces instead:

  python scripts/build_charm_section_toc_cache.py \\
    --only-path "/Chevrolet/2009/Silverado 1500 4WD V8-6.0L/"

  python scripts/build_charm_section_toc_cache.py --limit 50 --sleep 0.25

Resume after interrupt: run the same command again without --fresh. Paths already in
the output JSON with both repair and parts lists non-empty are skipped. Keep the same
--out file. Optional: --offset N skips the first N paths in the sorted vehicle list
(only if you cannot merge a broken output file; order must match collect_unique_paths).

Pacing: after each HTTP response, the script waits at least max(sleep, 1/max-rps)
seconds before the next GET (1/max-rps applies only when --max-rps > 0).
HTTP 429 responses are retried with Retry-After or exponential backoff (--max-429-retries).
"""
from __future__ import annotations

import argparse
import email.utils
import json
import sys
import time
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import fetch_charm_section_toc as toc  # noqa: E402

SECTION_SUFFIX = {
    "repair": "Repair%20and%20Diagnosis/",
    "parts": "Parts%20and%20Labor/",
}


def _relative_or_abs(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def path_key_for_catalog(encoded_path: str) -> str:
    """Match catalog app.js charmVehicleRootPathForStorage (decoded, no trailing slash)."""
    p = (encoded_path or "").strip()
    if not p.startswith("/"):
        p = "/" + p
    p = p.rstrip("/")
    if not p or p == "/":
        return "/"
    segs = [urllib.parse.unquote(s) for s in p.split("/") if s]
    return "/" + "/".join(segs)


def normalize_path_dir(p: str) -> str:
    p = (p or "").strip()
    if not p.startswith("/"):
        p = "/" + p
    if not p.endswith("/"):
        p += "/"
    return p


def collect_unique_paths(vehicle_cache: dict) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    by_my = vehicle_cache.get("byMakeYear") or {}
    for _mk, years in by_my.items():
        if not isinstance(years, dict):
            continue
        for _yk, rows in years.items():
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                path = row.get("path")
                if not isinstance(path, str) or not path.strip():
                    continue
                norm = normalize_path_dir(path)
                if norm not in seen:
                    seen.add(norm)
                    out.append(norm)
    out.sort()
    return out


def charm_path_segments_url(path_with_slashes: str) -> str:
    """
    Path may be %20-encoded or contain literal spaces (shell eats %). Emit a valid URL path.
    """
    p = normalize_path_dir(path_with_slashes)
    inner = p.strip("/")
    if not inner:
        return "/"
    segs = [urllib.parse.quote(urllib.parse.unquote(s), safe="") for s in inner.split("/") if s]
    return "/" + "/".join(segs) + "/"


def section_url(base: str, vehicle_path: str, section: str) -> str:
    mid = charm_path_segments_url(vehicle_path)
    return f"{base.rstrip('/')}{mid}{SECTION_SUFFIX[section]}"


def fetch_titles(url: str, session: toc.CharmSession) -> list[str]:
    html = session.fetch(url)
    titles = toc.titles_from_html(url, html)
    return titles


def retry_after_seconds(err: urllib.error.HTTPError) -> float | None:
    """Parse Retry-After header (seconds or HTTP-date). Returns None if missing/invalid."""
    raw = err.headers.get("Retry-After") if err.headers else None
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip()
    try:
        sec = int(s)
        if sec >= 0:
            return float(sec)
    except ValueError:
        pass
    try:
        dt = email.utils.parsedate_to_datetime(s)
        if dt is not None:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            delta = (dt - datetime.now(timezone.utc)).total_seconds()
            return max(0.0, float(delta))
    except (TypeError, ValueError, OSError):
        pass
    return None


class RequestPacer:
    """
    After each HTTP response, enforce a quiet period before the next GET starts:
    wait at least max(--sleep, 1/--max-rps) seconds (whichever is stricter when both set).
    """

    def __init__(self, sleep: float, max_rps: float):
        self.sleep = max(0.0, float(sleep))
        self.max_rps = float(max_rps)
        self._last_end: float = 0.0

    def min_gap(self) -> float:
        g = self.sleep
        if self.max_rps > 0:
            g = max(g, 1.0 / self.max_rps)
        return g

    def before_request(self) -> None:
        if self._last_end <= 0.0:
            return
        gap = self.min_gap()
        if gap <= 0:
            return
        elapsed = time.monotonic() - self._last_end
        need = gap - elapsed
        if need > 0:
            time.sleep(need)

    def after_response(self) -> None:
        self._last_end = time.monotonic()


def cap_titles(titles: list[str], max_n: int) -> list[str]:
    if max_n <= 0 or len(titles) <= max_n:
        return titles
    return titles[:max_n]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root",
    )
    ap.add_argument(
        "--vehicle-cache",
        type=Path,
        default=None,
        help="Input charm-vehicle-cache.json (default: catalog/charm-vehicle-cache.json)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output JSON (default: catalog/charm-section-toc-cache.json)",
    )
    ap.add_argument(
        "--sleep",
        type=float,
        default=0.2,
        help="Minimum seconds after each response before the next GET (default 0.2)",
    )
    ap.add_argument(
        "--max-rps",
        type=float,
        default=0.0,
        metavar="N",
        help="Max requests per second (0 = no cap). Wait max(--sleep, 1/N) after each response",
    )
    ap.add_argument(
        "--max-429-retries",
        type=int,
        default=8,
        metavar="N",
        help="How many times to retry the same URL on HTTP 429 before skipping section",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=0,
        metavar="N",
        help="Process at most N vehicle paths (0 = all)",
    )
    ap.add_argument(
        "--offset",
        type=int,
        default=0,
        metavar="N",
        help="Skip first N paths after sorting (only if output JSON cannot be merged)",
    )
    ap.add_argument(
        "--only-path",
        action="append",
        default=[],
        metavar="PATH",
        help="Only fetch this vehicle path (repeatable). Must match cache form, e.g. /Make/year/Model/",
    )
    ap.add_argument(
        "--max-titles",
        type=int,
        default=3500,
        help="Cap titles per section in output (default: 3500, same as catalog datalist cap)",
    )
    ap.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore existing output file (start empty byPath)",
    )
    ap.add_argument(
        "--refetch",
        action="store_true",
        help="Re-fetch paths already present in output",
    )
    args = ap.parse_args()
    if args.max_rps < 0:
        raise SystemExit("--max-rps must be >= 0")
    if args.max_429_retries < 0:
        raise SystemExit("--max-429-retries must be >= 0")
    if args.offset < 0:
        raise SystemExit("--offset must be >= 0")

    root: Path = args.root
    vc_path = args.vehicle_cache or (root / "catalog" / "charm-vehicle-cache.json")
    out_path = args.out or (root / "catalog" / "charm-section-toc-cache.json")

    if not vc_path.is_file():
        raise SystemExit(f"Missing {vc_path}")

    data = load_json(vc_path)
    base = (data.get("charmBaseUrl") or "https://charm.li").rstrip("/")
    base_u = urllib.parse.urlparse(base if "://" in base else f"https://{base}")
    charm_host = base_u.netloc.split("@")[-1] or "charm.li"

    if args.only_path:
        paths = [normalize_path_dir(p) for p in args.only_path]
    else:
        paths = collect_unique_paths(data)
        if args.offset > 0:
            paths = paths[args.offset :]
        if args.limit > 0:
            paths = paths[: args.limit]

    by_path: dict[str, dict[str, list[str]]] = {}
    if not args.fresh and out_path.is_file():
        try:
            old = load_json(out_path)
            raw = old.get("byPath") or {}
            if isinstance(raw, dict):
                for k, v in raw.items():
                    if isinstance(v, dict) and isinstance(k, str):
                        by_path[k] = {
                            "repair": list(v.get("repair") or []),
                            "parts": list(v.get("parts") or []),
                        }
        except (json.JSONDecodeError, OSError, TypeError) as e:
            print(f"WARN: could not merge {out_path} ({e}); starting empty.")

    total = len(paths)
    pacer = RequestPacer(args.sleep, args.max_rps)
    with toc.CharmSession(charm_host) as session:
        for i, vpath in enumerate(paths, start=1):
            key = path_key_for_catalog(vpath)
            if (
                not args.refetch
                and key in by_path
                and by_path[key].get("repair")
                and by_path[key].get("parts")
            ):
                print(f"[{i}/{total}] {key} SKIP (cached)")
                continue

            row: dict[str, list[str]] = {"repair": [], "parts": []}
            if not args.refetch and key in by_path:
                row["repair"] = list(by_path[key].get("repair") or [])
                row["parts"] = list(by_path[key].get("parts") or [])

            for sec in ("repair", "parts"):
                if not args.refetch and row[sec]:
                    print(f"[{i}/{total}] {key} {sec} SKIP (cached)")
                    continue
                url = section_url(base, vpath, sec)
                titles: list[str] | None = None
                n429 = 0
                while True:
                    pacer.before_request()
                    try:
                        titles = fetch_titles(url, session)
                        pacer.after_response()
                        break
                    except urllib.error.HTTPError as e:
                        pacer.after_response()
                        if e.code == 429 and n429 < args.max_429_retries:
                            wait_s = retry_after_seconds(e)
                            if wait_s is None:
                                wait_s = min(30.0 * (2**n429), 300.0)
                            print(
                                f"[{i}/{total}] {key} {sec} HTTP 429, "
                                f"waiting {wait_s:.1f}s (retry {n429 + 1}/{args.max_429_retries})"
                            )
                            time.sleep(wait_s)
                            n429 += 1
                            continue
                        print(f"[{i}/{total}] {key} {sec} HTTP {e.code} {url}")
                        break
                    except urllib.error.URLError as e:
                        pacer.after_response()
                        print(f"[{i}/{total}] {key} {sec} URL error {e}")
                        break
                if titles is not None:
                    row[sec] = cap_titles(titles, args.max_titles)
                    print(f"[{i}/{total}] {key} {sec} -> {len(row[sec])} titles")

            by_path[key] = row

            out_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "description": "Repair/Parts TOC titles per vehicle — rebuild with "
                "scripts/build_charm_section_toc_cache.py; keys match decoded vehicle pathname "
                "(no trailing slash), same as catalog sessionStorage.",
                "version": 1,
                "charmBaseUrl": base,
                "generatedAt": datetime.now(timezone.utc).isoformat(),
                "sourceVehicleCache": _relative_or_abs(vc_path, root).replace("\\", "/"),
                "byPath": dict(sorted(by_path.items(), key=lambda kv: kv[0])),
            }
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
                f.write("\n")

    print(f"Done. Wrote {out_path} ({len(by_path)} paths)")


if __name__ == "__main__":
    main()
