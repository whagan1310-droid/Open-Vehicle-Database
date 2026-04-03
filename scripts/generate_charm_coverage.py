#!/usr/bin/env python3
"""
Backward-compatible entry point: regenerates catalog/charm-coverage.json from
https://charm.li/ (same as sync_charm_coverage_from_charm_li.py).

The hand-maintained COVERAGE_LINES list was removed — live sync avoids drift.

  python scripts/generate_charm_coverage.py
  python scripts/sync_charm_coverage_from_charm_li.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    script = Path(__file__).resolve().parent / "sync_charm_coverage_from_charm_li.py"
    raise SystemExit(subprocess.call([sys.executable, str(script)]))


if __name__ == "__main__":
    main()
