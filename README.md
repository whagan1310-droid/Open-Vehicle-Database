# Open Vehicle Database

**Code and scripts:** All **software** in this repository—`scripts/`, the **`catalog/`** picker, build tooling, and automation—is written and maintained by **Gam3rGoon** and **MasterTech-Pro**. **Operation CHARM** and **Xerostatic** ([**ShopBase**](https://shopbasehq.com/), **[Open Labor Project](https://openlaborproject.com/)**) **did not** author this codebase; they appear only as **inspiration**, **ecosystem context**, and (where applicable) **attributed manual sources** or links to their sites. What comes from where is spelled out in **[ATTRIBUTION.md](./ATTRIBUTION.md)**.

A community-driven, **free** automotive knowledge library—built in the spirit of **MasterTech-Pro**, **[ShopBase](https://shopbasehq.com/)**, **[Open Labor Project](https://openlaborproject.com/)**, **[Operation CHARM](https://charm.li/)**, and the broader **open repair-data** movement. Contributors are always welcome in the open realm of **equal right to repair**: *by the people, for the people*—so that repair information stays accessible instead of locked behind paywalls and gatekeeping.

**Attribution and inspirations** (CHARM, **[ShopBase](https://shopbasehq.com/)**, **[Open Labor Project](https://openlaborproject.com/)**, catalog picker notes) are summarized in **[ATTRIBUTION.md](./ATTRIBUTION.md)**. Inspiration from **[plowman/open-vehicle-db](https://github.com/plowman/open-vehicle-db)**.

---

## Why this exists

Vehicles do not last and behave as they once did. Parts, software, and diagnostics have changed dramatically over the last two decades. Along the way, much of the industry has made it harder for independent shops, mobile techs, and owners to keep what they drive on the road.

A small group of **respectable, industry-driven leaders**—with **decades of real-world experience**—decided that was enough. **We are here to stay.**

This repository is intended as a **living library** that **anyone** can use **without cost**. The goal is simple: push back on monopoly, share knowledge openly, and **grow and learn together**.

---

## Making the library usable for everyone

We have asked the same question many times: *How do we make this library useful for people who are not computer experts?*

Our answer has **two parts**:

1. **Xerostatic** — **[ShopBase](https://shopbasehq.com/)**, **[Open Labor Project](https://openlaborproject.com/)** — offers **free, web-based shop management** in the same category as tools like Mitchell1, ShopKey, and ShopMonkey, so data and workflows can live where shops already work. Learn more at [shopbasehq.com](https://shopbasehq.com/) and [openlaborproject.com](https://openlaborproject.com/). *This repo is independent from **[Open Labor Project](https://openlaborproject.com/)**’s datasets; we cite Xerostatic, **[ShopBase](https://shopbasehq.com/)**, and OLP as **inspiration** and ecosystem kinship—see [ATTRIBUTION.md](./ATTRIBUTION.md).*

2. **Gam3rGoon** — builds **custom, multi-platform applications** (Windows, macOS, Android, iOS) with add-on solutions tailored to business needs, including an **Android-based OBD2 scanner** (coming soon), so the library and related tooling can meet people on the devices they already use.

Together, the aim is for this growing library to be **something you can build on and plug into real businesses**—not just a folder of files for developers only.

---

## Related projects, attribution, and inspiration

| Resource | How we relate to it |
|----------|---------------------|
| **[ShopBase](https://shopbasehq.com/)**, **[Open Labor Project](https://openlaborproject.com/)** | **Inspiration & ecosystem alignment** — free labor, specs, DTCs, and shop tools. We **thank and credit** Xerostatic; we do **not** ship OLP data here. |
| **[Operation CHARM (charm.li)](https://charm.li/)** | **Manual content** — CHARM exports in this repo (e.g. under `Acura/`) should be **attributed** per CHARM’s terms. See [ATTRIBUTION.md](./ATTRIBUTION.md). |
| **[plowman/open-vehicle-db](https://github.com/plowman/open-vehicle-db)** | **Past inspiration** for a structured vehicle picker; **we do not redistribute their JSON.** The `catalog/` picker uses **your folder names** only. |
| **MasterTech-Pro (Gam3rGoon)** | **Values / lineage** — professional, technician-focused tooling as a guiding reference. |

---

## Vehicle catalog (CHARM picker) — Built by Gam3rGoon

The **`catalog/`** site is a **Make → Year → Model → Engine** picker.

- **Local manuals:** when a manual exists under a **`charmDirs`** folder (e.g. **`Acura/`**) or another **top-level folder** the indexer picked up, the picker links to your offline **`index.html`** or **`.pdf`** (one picker row per PDF). **CHARM-style** layouts use subfolders named like **`1994 Acura Integra …`**. **Flat** bundles may use **`index.html`**, **`.pdf`** files, or both; PDFs in the same directory as an **`index.html`** are not double-listed (HTML wins for that folder). Some bundles use **`yearFrom`** / **`yearTo`** instead of a single **`year`** (e.g. John Deere garden tractor PDFs); the picker shows every year in that range. Optional **`makeDisplayNames`** in **`charm-manual-index.json`** overrides the Make dropdown label (e.g. **John-Deere** instead of **John-deere**).
- **No local export, cached listings:** **`catalog/charm-vehicle-cache.json`** is built by scraping public **`charm.li/{Make}/{year}/`** pages (see script below). The picker fills **model** and **engine** from that file and opens each vehicle’s **directory URL** on [Operation CHARM](https://charm.li/) (CHARM’s UI; you continue to the manual there). On some year pages, CHARM nests links under plain-text group titles (for example *Avalanche 1500 2WD* or *Cobalt*); the anchor text may show only the engine line. **`build_charm_vehicle_cache.py`** takes each vehicle’s full line from the decoded **`href`** path after `/Make/year/`, so grouped entries still get correct **model** and **engine** in the picker.
- **No cache row for that make/year:** the status shows **Index not yet added**, with an optional link to the **year index** on charm.li so you can still open the manual in the browser.
- **Deeper scan (remote CHARM only):** when there is **no** local export for the vehicle you picked, the picker enables **CHARM menu section**, **Search on that CHARM page**, and the **Load CHARM table of contents** panel. Build **`charm-section-toc-cache.json`** (setup step 4) for offline search suggestions; see **Restart, merge, and Charm updates** to resume long builds or refresh after CHARM changes.

**Setup**

1. **Coverage (make/year ranges):** run `python scripts/sync_charm_coverage_from_charm_li.py` (or `python scripts/generate_charm_coverage.py`) to refresh **`catalog/charm-coverage.json`** from live [charm.li](https://charm.li/) — avoids errors in a hand-written list.
2. **Local index:** `python scripts/build_charm_manifest.py` → **`catalog/charm-manual-index.json`**. Folders listed under **`charmDirs`** in **`charm-manifest.config.json`** are always scanned. Set **`scanRepoRootForManuals`** to **`true`** to also scan **other top-level directories** that contain an **`index.html`** (any depth) or **`.pdf`** manuals within **`pdfScanMaxDepth`** levels under that folder (default **3**; set **`0`** to disable PDF indexing). Skips **`catalog/`**, **`scripts/`**, **`.git`**, etc. Use **`manualRootSkip`** to exclude specific folder names from that scan. CLI: **`--scan-repo`** / **`--no-scan-repo`**, **`--pdf-depth N`**. The generated JSON lists every root that was indexed in **`indexRoots`**.
3. **Vehicle cache (model/engine → remote manual URLs):** `python scripts/build_charm_vehicle_cache.py` → **`catalog/charm-vehicle-cache.json`**. Default **`--scope manifest`** only fetches `(makeKey, year)` pairs that appear in the local manifest (typically matches your **`charmDirs`** exports, e.g. Acura only). For a **full** cache of every make/year on CHARM, use **`--scope coverage`** (many HTTP requests and a large JSON). Example full rebuild: `python scripts/build_charm_vehicle_cache.py --fresh --scope coverage --sleep 0.2` (add **`--refetch`** if you are merging into an existing file and want to force re-download of everything in scope). **Resume / merge:** by default the script **loads** an existing cache and **skips** pairs already present; it **rewrites the JSON after each fetch** (use **`--checkpoint-every N`** to batch writes). **Ctrl+C** saves progress; re-run the **same command** to continue. **`--fresh`** (or **`--no-merge`**) starts empty; **`--refetch`** ignores the skip and re-downloads everything in scope.
4. **CHARM section TOC (deeper picker / search):** `python scripts/build_charm_section_toc_cache.py` → **`catalog/charm-section-toc-cache.json`**. This file lists **Repair and Diagnosis** and **Parts and Labor** table-of-contents titles per vehicle path (same idea as the in-catalog bookmarklet). The picker loads it so the **“Search on that CHARM page”** field can suggest real section names without calling charm.li from the browser (CORS). **How to use the deeper controls in the picker** (only when you picked a **remote** manual—no local export for that make/year): choose **CHARM menu section** (*Vehicle menu (root)*, *Repair and Diagnosis*, or *Parts and Labor*); the manual link opens that branch on charm.li. Type a phrase in **Search on that CHARM page** and use **Google · this folder** beside the link to run a Google search scoped to the same path on charm.li. If you do **not** ship **`charm-section-toc-cache.json`**, expand the **Load CHARM table of contents** panel: copy the bookmarklet, use it on an expanded charm.li page, or paste JSON / one title per line and **Save for this manual & CHARM section** (stored in the browser’s **sessionStorage** for that session).
5. **Serve** the repo root (`python -m http.server 8080`) and open **`/catalog/`**.

**How you refresh coverage later**

```bash
python scripts/sync_charm_coverage_from_charm_li.py
```

(or `python scripts/generate_charm_coverage.py`)

That keeps the picker in sync with CHARM even if they add years or makes later, without you maintaining the big list by hand.

### Restart, merge, and Charm updates

When CHARM’s site or your exports change, refresh the JSON the picker reads. **You usually do not delete old files:** both builder scripts **merge** into an existing file by default and **skip** work that is already done.

| Data file | Builder | Restart / resume | Force full redo | Notes |
|-----------|---------|------------------|-----------------|-------|
| **`charm-vehicle-cache.json`** | `scripts/build_charm_vehicle_cache.py` | Re-run the **same** command **without** `--fresh`. Skips make/year pairs already in the file. | `--fresh` or `--no-merge` for an empty start; **`--refetch`** to re-download everything in scope | Writes after each fetch (or batched with **`--checkpoint-every N`**). **Ctrl+C** is safe; run again to continue. |
| **`charm-section-toc-cache.json`** | `scripts/build_charm_section_toc_cache.py` | Re-run **without** `--fresh`. Skips vehicle paths that already have **both** `repair` and `parts` title lists non-empty. | `--fresh` drops merged data; **`--refetch`** re-fetches paths even if present | One vehicle path = two HTTP pages (Repair + Parts). Uses a keep-alive HTTPS session. Optional **`--sleep`** (default `0.2`), **`--max-rps`** to cap requests/sec (**`max(sleep, 1/rps)`** after each response), **`--max-429-retries`** for HTTP 429 backoff. **`--offset N`** skips the first *N* sorted paths only if you cannot load a **valid** JSON file (prefer fixing/restoring the file so merge works). |

**Typical “pick up where I left off”:** keep **`catalog/charm-section-toc-cache.json`** (or vehicle cache) on disk, run for example:

```bash
python scripts/build_charm_section_toc_cache.py --sleep 0.15
```

Do **not** pass **`--fresh`** unless you intend to rebuild **`byPath`** from scratch. If merge fails with a JSON error, restore the file from git or a backup; a corrupted file cannot be merged until it is valid JSON again.

**After CHARM adds vehicles or years:** refresh **`charm-coverage.json`** (see above), then rebuild **`charm-vehicle-cache.json`** for the new scope; then extend **`charm-section-toc-cache.json`** with the same merge/resume command so new paths get Repair/Parts titles.

To add more **local** manuals, either add a folder name to **`charmDirs`**, or place the folder at the **repo root** and enable **`scanRepoRootForManuals`**, then rebuild the manifest.

**Large PDFs:** GitHub rejects files over **100 MB**. If a PDF is larger than that, do not commit it (use **`.gitignore`**, **Releases**, or another host). Run **`python scripts/build_charm_manifest.py`** when adding or removing local manuals so **`charm-manual-index.json`** stays in sync.

### Build plan (going further)

| Phase | Goal |
|-------|------|
| **Now** | Picker + coverage JSON + **`charm-vehicle-cache.json`** + optional **`charm-section-toc-cache.json`** for remote **charm.li** URLs, deeper section links, and search suggestions. |
| **Next** | Optional **CI on a schedule** to regenerate `charm-vehicle-cache.json` (respect CHARM’s terms and rate limits). |
| **Later** | Small **backend proxy** (same-origin API) if you need live CHARM HTML in-app without committing huge caches. |
| **Caution** | Browsers cannot read charm.li from `fetch()` on a static catalog (CORS); committed JSON or a server is required for deep menus. |
| **Multi-word makes** | Local `index.html` paths use the first token after the year as `make` today (e.g. `Mercedes`). CHARM URLs use full names (e.g. `Mercedes Benz`). Until the manifest script learns multi-token makes, **charm.li** links still work; **local** rows may not merge for those makes without a small parser tweak. |

### How to test picker — By Gam3rGoon

**Quick start** (files already in the repo)

1. Open a terminal **at the repo root** (the folder that contains `catalog/`).
2. Start a local web server, for example:

   ```bash
   python -m http.server 8080
   ```

3. In your browser go to: **http://localhost:8080/catalog/**
4. **Make selections** in the picker (**Make → Year → Model → Engine**). For **remote** CHARM rows, use **CHARM menu section** and **Search on that CHARM page** as described in setup step 4 above.

**Reference** — picker UI:

![Vehicle picker — Pick a vehicle](catalog/vehicle-picker-reference.png)

Full **attribution** and **inspiration** notes: **[ATTRIBUTION.md](./ATTRIBUTION.md)**.

---

## Contributing

**Contributions are welcome.** Whether you fix a typo, add documentation, expand vehicle or procedure coverage, or improve how data is organized, you help keep repair knowledge **free** and **fair**.

If you maintain a shop, teach, wrench on weekends, or write software: you belong here. Let’s **stop the monopoly** and keep **equal right to repair** something we defend in practice—not only in principle.

---

*Free access. Open collaboration. For technicians, owners, and the communities that depend on them.*
