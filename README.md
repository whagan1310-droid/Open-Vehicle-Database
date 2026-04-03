# Open Vehicle Database

A community-driven, **free** automotive knowledge library—built in the spirit of **MasterTech-Pro**, **[Open Labor Project](https://openlaborproject.com/)** (Xerostatic), **[Operation CHARM](https://charm.li/)**, and the broader **open repair-data** movement. Contributors are always welcome in the open realm of **equal right to repair**: *by the people, for the people*—so that repair information stays accessible instead of locked behind paywalls and gatekeeping.

**Attribution and inspirations** (CHARM, Open Labor Project, catalog picker notes) are summarized in **[ATTRIBUTION.md](./ATTRIBUTION.md)**.

---

## Why this exists

Vehicles do not last and behave as they once did. Parts, software, and diagnostics have changed dramatically over the last two decades. Along the way, much of the industry has made it harder for independent shops, mobile techs, and owners to keep what they drive on the road.

A small group of **respectable, industry-driven leaders**—with **decades of real-world experience**—decided that was enough. **We are here to stay.**

This repository is intended as a **living library** that **anyone** can use **without cost**. The goal is simple: push back on monopoly, share knowledge openly, and **grow and learn together**.

---

## Making the library usable for everyone

We have asked the same question many times: *How do we make this library useful for people who are not computer experts?*

Our answer has **two parts**:

1. **Xerostatic** — creator of **[Open Labor Project](https://openlaborproject.com/)** — offers **free, web-based shop management** (including **ShopBase**) in the same category as tools like Mitchell1, ShopKey, and ShopMonkey, so data and workflows can live where shops already work. Learn more at [openlaborproject.com](https://openlaborproject.com/). *This repo is independent from Open Labor Project’s datasets; we cite Xerostatic and OLP as **inspiration** and ecosystem kinship—see [ATTRIBUTION.md](./ATTRIBUTION.md).*

2. **Gam3rgoon** — builds **custom, multi-platform applications** (Windows, macOS, Android, iOS) with add-on solutions tailored to business needs, including an **Android-based OBD2 scanner** (coming soon), so the library and related tooling can meet people on the devices they already use.

Together, the aim is for this growing library to be **something you can build on and plug into real businesses**—not just a folder of files for developers only.

---

## Related projects, attribution, and inspiration

| Resource | How we relate to it |
|----------|---------------------|
| **[Open Labor Project](https://openlaborproject.com/)** (Xerostatic) | **Inspiration & ecosystem alignment** — free labor, specs, DTCs, and shop tools. We **thank and credit** Xerostatic; we do **not** ship OLP data here. |
| **[Operation CHARM (charm.li)](https://charm.li/)** | **Manual content** — CHARM exports in this repo (e.g. under `Acura/`) should be **attributed** per CHARM’s terms. See [ATTRIBUTION.md](./ATTRIBUTION.md). |
| **[plowman/open-vehicle-db](https://github.com/plowman/open-vehicle-db)** | **Past inspiration** for a structured vehicle picker; **we do not redistribute their JSON.** The `catalog/` picker uses **your folder names** only. |
| **MasterTech-Pro** | **Values / lineage** — professional, technician-focused tooling as a guiding reference. |

---

## Vehicle catalog (CHARM picker)

The **`catalog/`** site is a **Make → Year → Model → Engine** picker.

- **Local manuals:** when a vehicle exists under a **`charmDirs`** folder (e.g. **`Acura/`**), the indexer links to your offline **`index.html`** (folder names drive model/engine).
- **No local export, cached listings:** **`catalog/charm-vehicle-cache.json`** is built by scraping public **`charm.li/{Make}/{year}/`** pages (see script below). The picker fills **model** and **engine** from that file and opens each vehicle’s **directory URL** on [Operation CHARM](https://charm.li/) (CHARM’s UI; you continue to the manual there).
- **No cache row for that make/year:** the status shows **Index not yet added**, with an optional link to the **year index** on charm.li so you can still open the manual in the browser.

**Setup**

1. **Coverage (make/year ranges):** run `python scripts/sync_charm_coverage_from_charm_li.py` (or `python scripts/generate_charm_coverage.py`) to refresh **`catalog/charm-coverage.json`** from live [charm.li](https://charm.li/) — avoids errors in a hand-written list.
2. **Local index:** `python scripts/build_charm_manifest.py` → **`catalog/charm-manual-index.json`**.
3. **Vehicle cache (model/engine → remote manual URLs):** `python scripts/build_charm_vehicle_cache.py` → **`catalog/charm-vehicle-cache.json`**. Default **`--scope manifest`** only fetches years that appear in the local manifest (keeps the file small). Use **`--scope coverage`** to scrape **every** make/year from `charm-coverage.json` (many HTTP requests and a large JSON). **Resume / merge:** by default the script **loads** an existing cache and **skips** `(makeKey, year)` pairs already present; it **rewrites the JSON after each fetch** (use **`--checkpoint-every N`** to batch writes). **Ctrl+C** saves progress; re-run the **same command** to continue. **`--fresh`** (or **`--no-merge`**) starts empty; **`--refetch`** ignores the skip and re-downloads everything in scope.
4. **Serve** the repo root (`python -m http.server 8080`) and open **`/catalog/`**.

**How you refresh coverage later**

```bash
python scripts/sync_charm_coverage_from_charm_li.py
```

(or `python scripts/generate_charm_coverage.py`)

That keeps the picker in sync with CHARM even if they add years or makes later, without you maintaining the big list by hand.

To add more **local** makes, add a CHARM export folder and its name to **`charm-manifest.config.json`**, then rebuild the manifest.

### Build plan (going further)

| Phase | Goal |
|-------|------|
| **Now** | Picker + coverage JSON + **`build_charm_vehicle_cache.py`** + **`charm-vehicle-cache.json`** for model/engine and remote **charm.li** vehicle URLs when there is no local export. |
| **Next** | Optional **CI on a schedule** to regenerate `charm-vehicle-cache.json` (respect CHARM’s terms and rate limits). |
| **Later** | Small **backend proxy** (same-origin API) if you need live CHARM HTML in-app without committing huge caches. |
| **Caution** | Browsers cannot read charm.li from `fetch()` on a static catalog (CORS); committed JSON or a server is required for deep menus. |
| **Multi-word makes** | Local `index.html` paths use the first token after the year as `make` today (e.g. `Mercedes`). CHARM URLs use full names (e.g. `Mercedes Benz`). Until the manifest script learns multi-token makes, **charm.li** links still work; **local** rows may not merge for those makes without a small parser tweak. |

Full **attribution** and **inspiration** notes: **[ATTRIBUTION.md](./ATTRIBUTION.md)**.

---

## Contributing

**Contributions are welcome.** Whether you fix a typo, add documentation, expand vehicle or procedure coverage, or improve how data is organized, you help keep repair knowledge **free** and **fair**.

If you maintain a shop, teach, wrench on weekends, or write software: you belong here. Let’s **stop the monopoly** and keep **equal right to repair** something we defend in practice—not only in principle.

---

*Free access. Open collaboration. For technicians, owners, and the communities that depend on them.*
