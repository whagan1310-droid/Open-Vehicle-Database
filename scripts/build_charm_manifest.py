#!/usr/bin/env python3
"""
Scan manual export folders under the repo root for index.html and write catalog/charm-manual-index.json.

Run from repository root:
  python scripts/build_charm_manifest.py

Roots default to charm-manifest.config.json key "charmDirs" (e.g. Acura/). Optional
scanRepoRootForManuals adds other top-level folders that contain index.html or PDF manuals
(within pdfScanMaxDepth). CHARM-style trees use "YYYY Make …" subfolders; flat trees may use
a single folder with index.html and/or .pdf files at the top (or shallow subfolders).

Each manual href is relative to catalog/index.html.
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


def parse_fallback_folder(folder_name: str) -> tuple[int | None, str | None, str | None]:
    """
    Best-effort year/make from a non-CHARM folder name (e.g. technical manual slugs).
    Year: rightmost plausible 19xx/20xx in the name. Make: text before -GARDEN, -TECHNICAL,
    -SERVICE, -MANUAL, or first one or two hyphen segments.
    """
    name = folder_name.strip()
    if not name:
        return None, None, None
    years = [int(m.group(1)) for m in re.finditer(r"\b((?:19|20)\d{2})\b", name)]
    years = [y for y in years if 1980 <= y <= 2039]
    year = years[-1] if years else None
    make = None
    upper = name.upper()
    for kw in ("-GARDEN", "-TECHNICAL", "-SERVICE", "-MANUAL", "_TM"):
        idx = upper.find(kw)
        if idx > 0:
            make = name[:idx].upper()
            break
    if not make:
        parts = name.split("-")
        make = "-".join(parts[: min(2, len(parts))]).upper() if parts else name.upper()
    rest = name
    return year, make, rest


def parse_charm_or_fallback(segment: str) -> tuple[int | None, str | None, str | None]:
    y, mk, rest = parse_title(segment)
    if mk:
        return y, mk, rest
    return parse_fallback_folder(segment)


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


def _meta_for_pdf_entry(
    rel: Path, expected_top: str
) -> tuple[int | None, str, str, str]:
    """Year, make, rest, first_seg for a PDF path under a manual root."""
    parts = rel.parts
    if len(parts) >= 3 and parts[0] == expected_top:
        candidate = parts[1]
        if re.match(r"^\d{4}\s", candidate):
            y, mk, r = parse_charm_or_fallback(candidate)
            if mk:
                return y, mk, r or "", candidate
    y, mk, r = parse_charm_or_fallback(expected_top)
    return y, mk, r or "", expected_top


def _is_john_deere_garden_tractor_bundle(expected_top: str) -> bool:
    u = expected_top.upper().replace(" ", "")
    return "JOHN" in u and "DEERE" in u and "GARDEN" in u and "TRACTOR" in u


def _john_deere_garden_pdf_overrides(expected_top: str, filename: str) -> dict | None:
    """
    Recognised bundle: JOHN-DEERE-*Garden-Tractor* folder with TM / electrical PDFs.
    Make key JOHN-DEERE (display \"John-Deere\" via makeDisplayNames). Model from filename.
    Years 2002–2006 (product range for X465/X475/X485/X575/X585 per TM2023 family).
    """
    if not _is_john_deere_garden_tractor_bundle(expected_top):
        return None
    stem = Path(filename).stem
    model = None
    m = re.search(r"(?i)Garden_?Tractor[_-](.+)$", stem)
    if m:
        model = m.group(1).strip()
    if not model:
        m2 = re.search(r"(X\d+(?:_X\d+)+)", stem)
        if m2:
            model = m2.group(1)
    if not model:
        model = "X465_X475_X485_X575_X585"
    if re.search(r"(?i)electrical", stem) and not re.search(
        r"(?i)garden_?tractor", stem
    ):
        picker_model = f"{model} - Electrical"
    else:
        picker_model = model
    return {
        "make": "JOHN-DEERE",
        "yearFrom": 2002,
        "yearTo": 2006,
        "pickerModel": picker_model,
        "title": f"{picker_model} (PDF)",
        "restAfterMake": "Garden Tractors",
    }


def find_manuals(charm_make_root: Path, *, pdf_max_depth: int) -> list[dict]:
    """Index index.html and (optionally) .pdf files under one top-level manual folder."""
    manuals: list[dict] = []
    if not charm_make_root.is_dir():
        return manuals

    repo_root = charm_make_root.parent
    expected_top = charm_make_root.name

    try:
        top_r = charm_make_root.resolve()
    except OSError:
        top_r = charm_make_root

    for dirpath, _, filenames in os.walk(charm_make_root):
        if "index.html" not in filenames:
            continue
        full = Path(dirpath) / "index.html"
        try:
            rel = full.relative_to(repo_root)
        except ValueError:
            continue
        parts = rel.parts
        if len(parts) < 2 or parts[0] != expected_top:
            continue
        if len(parts) == 2:
            first_seg = expected_top
        else:
            first_seg = parts[1]
        year, make, rest = parse_charm_or_fallback(first_seg)
        if not make:
            continue
        picker_model, picker_engine = split_model_engine(rest or "")
        if not picker_model:
            picker_model = (rest or first_seg or "").strip() or first_seg
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
                "kind": "html",
            }
        )

    if pdf_max_depth > 0:
        seen_pdf: set[str] = set()
        for dirpath, _, filenames in os.walk(charm_make_root):
            if "index.html" in filenames:
                continue
            d = Path(dirpath)
            try:
                depth = len(d.relative_to(top_r).parts)
            except ValueError:
                continue
            if depth > pdf_max_depth:
                continue
            for fn in filenames:
                if not fn.lower().endswith(".pdf"):
                    continue
                full = d / fn
                try:
                    rel = full.relative_to(repo_root)
                except ValueError:
                    continue
                if rel.parts and rel.parts[0] != expected_top:
                    continue
                key = rel.as_posix()
                if key in seen_pdf:
                    continue
                seen_pdf.add(key)
                year, make, rest, first_seg = _meta_for_pdf_entry(rel, expected_top)
                if not make:
                    continue
                stem = Path(fn).stem
                under = rel.parts[1:-1] + (stem,)
                display_key = "/".join(under) if under else stem
                href = "../" + key
                jd = _john_deere_garden_pdf_overrides(expected_top, fn)
                if jd:
                    row = {
                        "href": href,
                        "title": jd["title"],
                        "make": jd["make"],
                        "yearFrom": jd["yearFrom"],
                        "yearTo": jd["yearTo"],
                        "restAfterMake": jd["restAfterMake"],
                        "pickerModel": jd["pickerModel"],
                        "pickerEngine": "",
                        "kind": "pdf",
                    }
                else:
                    row = {
                        "href": href,
                        "title": f"{display_key} (PDF)",
                        "year": year,
                        "make": make,
                        "restAfterMake": rest,
                        "pickerModel": display_key,
                        "pickerEngine": "",
                        "kind": "pdf",
                    }
                manuals.append(row)

    return manuals


def tree_has_manual_signal(base: Path, pdf_max_depth: int) -> bool:
    """True if subtree has index.html (any depth) or a .pdf within pdf_max_depth under base."""
    try:
        base_r = base.resolve()
    except OSError:
        return False
    for dirpath, _, filenames in os.walk(base):
        if "index.html" in filenames:
            return True
        if pdf_max_depth <= 0:
            continue
        d = Path(dirpath)
        try:
            depth = len(d.relative_to(base_r).parts)
        except ValueError:
            continue
        if depth > pdf_max_depth:
            continue
        if any(f.lower().endswith(".pdf") for f in filenames):
            return True
    return False


DEFAULT_REPO_SCAN_SKIP = frozenset(
    {
        ".cursor",
        ".git",
        ".github",
        ".vscode",
        "assets",
        "build",
        "catalog",
        "dist",
        "node_modules",
        "scripts",
        "__pycache__",
    }
)


def discover_manual_roots(
    root: Path,
    indexed_names: set[str],
    extra_skip: set[str],
    pdf_max_depth: int,
) -> list[str]:
    """
    Top-level directories under root that qualify as manual bundles (index.html at any
    depth, or .pdf within pdf_max_depth) and are not already in indexed_names.
    Skips DEFAULT_REPO_SCAN_SKIP ∪ extra_skip.
    """
    skip = DEFAULT_REPO_SCAN_SKIP | extra_skip
    out: list[str] = []
    try:
        candidates = sorted(p.name for p in root.iterdir() if p.is_dir())
    except OSError:
        return out
    for name in candidates:
        if name in skip or name.startswith("."):
            continue
        if name in indexed_names:
            continue
        base = root / name
        if tree_has_manual_signal(base, pdf_max_depth):
            out.append(name)
    return out


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
    ap.add_argument(
        "--scan-repo",
        action="store_true",
        help="Also index top-level repo folders that contain index.html or PDF manuals (within "
        "--pdf-depth) but are not in charmDirs (or set scanRepoRootForManuals in config).",
    )
    ap.add_argument(
        "--no-scan-repo",
        action="store_true",
        help="Disable repo scan even if charm-manifest.config.json enables it.",
    )
    ap.add_argument(
        "--pdf-depth",
        type=int,
        default=None,
        metavar="N",
        help="Index .pdf files up to N directory levels under each manual root (0 = PDFs off). "
        "Default: charm-manifest.config.json pdfScanMaxDepth or 3.",
    )
    args = ap.parse_args()
    root: Path = args.root
    out = args.out or (root / "catalog" / "charm-manual-index.json")
    cfg_path = root / "charm-manifest.config.json"
    cfg: dict = {}
    if cfg_path.is_file():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    charm_dirs = args.charm_dirs
    if charm_dirs is None:
        charm_dirs = cfg.get("charmDirs") or ["Acura"]
    cfg_scan = bool(cfg.get("scanRepoRootForManuals"))
    cfg_skip: set[str] = set()
    for s in cfg.get("manualRootSkip") or []:
        if isinstance(s, str) and s.strip():
            cfg_skip.add(s.strip())
    raw_pdf_depth = cfg.get("pdfScanMaxDepth")
    if args.pdf_depth is not None:
        pdf_max_depth = max(0, int(args.pdf_depth))
    elif isinstance(raw_pdf_depth, int):
        pdf_max_depth = max(0, raw_pdf_depth)
    else:
        pdf_max_depth = 3
    do_scan = (args.scan_repo or cfg_scan) and not args.no_scan_repo
    extra_roots: list[str] = []
    if do_scan:
        indexed = set(charm_dirs)
        extra_roots = discover_manual_roots(
            root, indexed, cfg_skip, pdf_max_depth
        )
    index_roots = list(charm_dirs) + extra_roots
    all_manuals: list[dict] = []
    for d in index_roots:
        all_manuals.extend(
            find_manuals(root / d, pdf_max_depth=pdf_max_depth)
        )
    all_manuals.sort(
        key=lambda x: (
            x["year"]
            if x.get("year") is not None
            else (x.get("yearFrom") or 0),
            x["title"] or "",
        )
    )
    payload = {
        "generatedFor": "Open-Vehicle-Database catalog → CHARM manuals",
        "pickerNote": "Make/year/model/engine are derived from folder names under indexed roots (CHARM layout or flat manual folders).",
        "charmDirs": charm_dirs,
        "scanRepoRootForManuals": do_scan,
        "pdfScanMaxDepth": pdf_max_depth,
        "indexRoots": index_roots,
        "manuals": all_manuals,
    }
    if any(m.get("make") == "JOHN-DEERE" for m in all_manuals):
        payload["makeDisplayNames"] = {"JOHN-DEERE": "John-Deere"}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(all_manuals)} manuals to {out}")


if __name__ == "__main__":
    main()
