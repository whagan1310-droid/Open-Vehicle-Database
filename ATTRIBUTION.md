# Attribution and inspiration

This file summarizes **who to credit** for what, and **what inspired** this repository. It is not legal advice.

---

## Operation CHARM (manual content)

Service manuals reached through this repository’s CHARM-style exports (for example under `Acura/`) come from **[Operation CHARM](https://charm.li/)** ([charm.li](https://charm.li/)). Keep **clear credit** to Operation CHARM wherever you show or redistribute that content, and follow **their** terms for use and sharing.

The **`catalog/`** picker does not replace CHARM; it helps visitors find the right local `index.html` when you host an export, and can **link out** to [charm.li](https://charm.li/) year pages when you do not.

**`catalog/charm-coverage.json`** is generated from live [charm.li](https://charm.li/) pages (`scripts/sync_charm_coverage_from_charm_li.py` or `scripts/generate_charm_coverage.py`). It is for navigation only; manual text and layout remain CHARM’s.

---

## Xerostatic and Open Labor Project (values, ecosystem, inspiration)

**[ShopBase](https://shopbasehq.com/)**, **[Open Labor Project](https://openlaborproject.com/)** — created by **Xerostatic** — provides **free** labor times, torque specs, fluid specs, DTC codes, battery specs, and related shop-facing data, plus web-based shop management. This **Open Vehicle Database** repository is a **separate** community library; it does not ship Open Labor Project’s datasets.

We **acknowledge and thank Xerostatic** for **Open Labor Project** as **major inspiration** and as part of the same **right-to-repair** ecosystem: practical, no-paywall information for technicians and owners. When you describe this project publicly, crediting **[Open Labor Project](https://openlaborproject.com/)** alongside Operation CHARM helps people find related free resources.

---

## Vehicle picker data (this repository) — Built By Gam3rGoon, MasterTech-Pro

The **Year / Make / Model / Engine** dropdowns in **`catalog/`** are **not** copied from any external vehicle database. They are generated from **folder names** in your CHARM exports when you run:

`python scripts/build_charm_manifest.py`

That script writes `catalog/charm-manual-index.json` with fields such as `pickerModel` and `pickerEngine` derived by parsing those names (see `split_model_engine` in the script). The manifest and catalog UI are **yours** to extend; refine parsing as your exports grow.

---

## Other inspiration (not shipped as data)

| Inspiration | Role |
|-------------|------|
| **[plowman/open-vehicle-db](https://github.com/plowman/open-vehicle-db)** | Early **UX idea**: a structured **year / make / model** style picker. **This repo does not vendor or redistribute their JSON.** |
| **MasterTech-Pro** | Referenced in project messaging as a **values** touchstone for professional, technician-focused tooling. |

---

## Maintainer / tooling note (README)

**Gam3rgoon** — referenced in the main **[README](./README.md)** — builds multi-platform applications and related tooling so this library can reach real workflows and devices. That partnership is described there, not as a third-party content license.

---

For redistribution of CHARM exports or a commercial product, confirm terms with **Operation CHARM** and seek counsel if you need certainty.
