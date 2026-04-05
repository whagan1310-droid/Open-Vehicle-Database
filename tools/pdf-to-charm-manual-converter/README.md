# Pdf-to-Charm-Manual-Converter

Standalone **HTTP API** (FastAPI + PyMuPDF) that converts one or more **PDF** service manuals into a **CHARM-style** static HTML bundle: `index.html`, `pages/`, shared **Operation CHARM**–like chrome (`style.css`, breadcrumbs, footer). Output matches the *layout pattern* of manuals on [charm.li](https://charm.li/); it does not recreate OEM HTML at thousands-of-topic granularity unless you use **`render`** mode (page images).

This tool lives under **`tools/pdf-to-charm-manual-converter/`** in the **Open Vehicle Database** repo. It is **optional**—the **`catalog/`** picker does not require it.

---

## Requirements

- **Python 3.10+**
- **pip** packages listed in [`requirements.txt`](./requirements.txt) (`fastapi`, `uvicorn`, `python-multipart`, `pymupdf`)

---

## Install

From **this directory** (`tools/pdf-to-charm-manual-converter/`):

```powershell
pip install -r requirements.txt
```

---

## Start the server

```powershell
cd tools\pdf-to-charm-manual-converter
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

On Windows you can also run [`run-server.ps1`](./run-server.ps1) from this folder.

If `uvicorn` is not on your PATH, always use **`python -m uvicorn`** (see repo root README notes for Python Scripts PATH).

Open **http://127.0.0.1:8000/docs** (Swagger UI).

**Health check:** **GET** `http://127.0.0.1:8000/health`

---

## Using Swagger (`/docs`) — step by step

1. **Scroll to `POST /v1/convert`** and expand it.

2. **Click `Try it out`**

3. **Fill the form** (example — John Deere garden tractors):

   | Field | Value |
   |--------|--------|
   | **make** | `John Deere` |
   | **year_label** | `2002-2006` |
   | **model_title** | `Garden Tractors X465 X475 X485 X575 X585 TM2023` |
   | **meta_description** | leave empty |
   | **mode** | `embed` (recommended for full PDFs) |
   | **render_dpi** | `110` (only matters for `render`) |
   | **max_pages_per_pdf** | leave empty for all pages (`render` only) |
   | **section_titles** | `["TM2023 technical manual","Electrical technical manual"]` |

4. **Attach PDFs (required)** — **`files`** → **Choose File**  
   - Put **TM2023** first, **Electrical** second so titles match `section_titles`.  
   - Use a second **Add item** row for `files` if Swagger shows it, or **Ctrl+click** to select both files in one dialog when supported.

5. **Execute**

6. **HTTP 200** → **Download** the `.zip` → unzip → open **`index.html`** in a browser.

7. **HTTP 422** with `files` / **missing** → no PDF was uploaded; repeat step 4.

---

## Modes

| Mode | Behavior |
|------|----------|
| **`embed`** | Keeps PDFs under `pdfs/`; hub pages embed them with CHARM-style header/footer. **Small ZIP, fast** — best for large manuals. |
| **`render`** | Rasterizes each page to PNG + one HTML per page. **Very large** outputs for big PDFs. Use **`max_pages_per_pdf`** (e.g. `5`) to test. |

---

## Hooking into this repo (Open Vehicle Database)

After you unzip the converter output:

1. Place the **manual folder** (the directory that contains `index.html`) at the **repo root**, or under a path your **`charm-manifest.config.json`** / **`charmDirs`** setup already scans.
2. Run from the **repo root**:

   ```bash
   python scripts/build_charm_manifest.py
   ```

3. Serve the repo and open **`/catalog/`** — the picker can pick up the new manual if the manifest indexes it (see root [`README.md`](../../README.md)).

Respect **copyright** and **Operation CHARM** / publisher terms for any manuals you convert or redistribute.

---

## Command-line example (curl)

From a machine where the API is running and paths are correct:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/v1/convert" `
  -H "accept: application/zip" `
  -F "make=John Deere" `
  -F "year_label=2002-2006" `
  -F "model_title=Garden Tractors X465 X475 X485 X575 X585 TM2023" `
  -F "mode=embed" `
  -F "section_titles=[\"TM2023 technical manual\",\"Electrical technical manual\"]" `
  -F "files=@C:\path\to\TM2023.pdf" `
  -F "files=@C:\path\to\Electrical.pdf" `
  -o charm-output.zip
```

Omit **`max_pages_per_pdf`** entirely when using **`embed`**.

---

## GitHub Releases — separate ZIP?

**Not required.** Anyone can use **Code → Download ZIP** on this repository and get the tool under `tools/pdf-to-charm-manual-converter/`.

A **separate release asset** (ZIP containing only this folder + `README.md`) is **optional** convenience for users who want the converter **without** the full database tree. If you create one, zip the contents of `tools/pdf-to-charm-manual-converter/` only and attach it to a GitHub Release with a short note pointing to this README.

---

## API

- **OpenAPI / Swagger:** `http://127.0.0.1:8000/docs`  
- **Endpoint:** **`POST /v1/convert`** — multipart form; response **`application/zip`**.

---

*Tool maintained as part of Open Vehicle Database; see root [`ATTRIBUTION.md`](../../ATTRIBUTION.md) for CHARM and third-party context.*
