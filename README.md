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

The **`catalog/`** site is a **Year → Make → Model → Engine** picker that points to **Operation CHARM** exports in this repo (e.g. **`Acura/`**). Dropdown values are **derived from your folder names** when you run the indexer—not from a third-party vehicle database.

1. **Index manuals:** `python scripts/build_charm_manifest.py` — reads **`charm-manifest.config.json`** (`charmDirs`) and writes `catalog/charm-manual-index.json`.
2. **Serve:** from the repo root, e.g. `python -m http.server 8080`, then open **`/catalog/`**.

To add more makes, add a top-level CHARM folder (e.g. `Toyota/`) and append its name to **`charmDirs`** in **`charm-manifest.config.json`**, then rebuild the manifest.

Full **attribution** and **inspiration** notes: **[ATTRIBUTION.md](./ATTRIBUTION.md)**.

---

## Contributing

**Contributions are welcome.** Whether you fix a typo, add documentation, expand vehicle or procedure coverage, or improve how data is organized, you help keep repair knowledge **free** and **fair**.

If you maintain a shop, teach, wrench on weekends, or write software: you belong here. Let’s **stop the monopoly** and keep **equal right to repair** something we defend in practice—not only in principle.

---

*Free access. Open collaboration. For technicians, owners, and the communities that depend on them.*
