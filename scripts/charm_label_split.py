"""
Split a manual site's vehicle line (path tail or link text) into picker model vs engine.

LEMON Manuals (lemon-manuals.la) uses the same path layout as classic CHARM exports, but
many newer listings use patterns like \"TLX Base, 2.4L Eng\" or \"ILX 2.0L Eng VIN 1\"
instead of only \"L4-1834cc ...\". This module keeps one implementation for:

- scripts/build_charm_vehicle_cache.py (remote year pages)
- scripts/build_charm_manifest.py (local export folder titles)
"""

from __future__ import annotations

import re


def split_model_engine(rest_after_make: str) -> tuple[str, str]:
    """
    Split remainder after make/year into a model line and an engine line.

    Tries, in order:
    1. CHARM-style displacement token (space + L4- / V6- / …).
    2. Trailing \"…, 2.4L Eng\" or \"…, 3.5L Eng, AWD\" (comma before X.XL Eng).
    3. Trailing \"… 2.0L Eng VIN 1\" (space before X.XL Eng).
    4. Other inline tokens: I6- / H4- / W12- style (space + letter + digits + hyphen).
    """
    rest = (rest_after_make or "").strip()
    if not rest:
        return "", ""

    # 1) Classic CHARM: " Integra L4-1590cc 1.6L ..."
    m = re.search(r"\s((?:L\d|V\d)\d*-\S+)", rest)
    if m:
        cut = m.start() + 1
        return rest[:cut].strip(), rest[cut:].strip()

    # 2) Honda/Acura-style: "TLX Base, 2.4L Eng" / "…, 3.5L Eng, FWD" / "…, 2.0L Eng VIN 4, 4WD"
    pat_comma_eng = re.compile(
        r",\s*((?:\d+\.\d|\d)\s*L\s+Eng(?:\s+VIN\s+\S+)?"
        r"(?:\s*,\s*(?:FWD|AWD|4WD|2WD|RWD))?)(?=\s*,|\s*$)",
        re.I,
    )
    matches = list(pat_comma_eng.finditer(rest))
    if matches:
        mm = matches[-1]
        eng = mm.group(1).strip()
        left = rest[: mm.start()].strip()
        if left and eng:
            return left, eng

    # 3) Space before displacement Eng: "ILX 2.0L Eng VIN 1"
    m = re.search(
        r"\s+((?:\d+\.\d|\d)\s*L\s+Eng(?:\s+VIN\s+\S+)?)\s*$",
        rest,
        re.I,
    )
    if m:
        eng = m.group(1).strip()
        left = rest[: m.start()].strip()
        if left and eng:
            return left, eng

    # 4) I6 / H4 / W12 … hyphenated
    m = re.search(r"\s((?:I|H|W)\d*-\S+)", rest)
    if m:
        cut = m.start() + 1
        return rest[:cut].strip(), rest[cut:].strip()

    return rest, ""
