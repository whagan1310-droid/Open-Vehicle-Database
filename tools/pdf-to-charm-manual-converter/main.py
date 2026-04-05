"""HTTP API: PDF manuals → CHARM-style static HTML (ZIP)."""

from __future__ import annotations

import json
import re
from io import BytesIO
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from charm_build import ManualMeta, Mode, PdfSection, build_charm_zip

app = FastAPI(
    title="Pdf-to-Charm-Manual-Converter",
    description=(
        "Upload one or more PDFs plus manual metadata; receive a ZIP whose layout "
        "matches Operation CHARM–style HTML (see charm.li): index.html, pages/, "
        "style.css, breadcrumbs. "
        "**embed** keeps vector PDFs and wraps them in CHARM chrome. "
        "**render** rasterizes pages to PNG (large output) for image-based browsing."
    ),
    version="1.0.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _safe_zip_filename(name: str) -> str:
    name = re.sub(r'[^\w.\-]+', "-", name).strip("-") or "manual"
    if not name.lower().endswith(".zip"):
        name += ".zip"
    return name[:200]


@app.post("/v1/convert")
async def convert(
    make: Annotated[str, Form(description="Manufacturer or brand, e.g. John Deere")],
    year_label: Annotated[str, Form(description="Model years label, e.g. 2002-2006")],
    model_title: Annotated[
        str, Form(description="Full manual title for H1 and ZIP folder name")
    ],
    files: Annotated[list[UploadFile], File(description="One or more PDF files")],
    meta_description: str = Form(""),
    mode: str = Form("embed", description="embed | render"),
    render_dpi: float = Form(110.0),
    max_pages_per_pdf: int | None = Form(None),
    section_titles: str = Form(
        "[]",
        description='JSON array of section titles, e.g. ["Technical manual","Electrical"]',
    ),
) -> StreamingResponse:
    if mode not in ("embed", "render"):
        raise HTTPException(400, detail='mode must be "embed" or "render"')
    if not files:
        raise HTTPException(400, detail="At least one PDF file is required")
    if render_dpi < 36 or render_dpi > 300:
        raise HTTPException(400, detail="render_dpi must be between 36 and 300")
    if max_pages_per_pdf is not None and max_pages_per_pdf < 1:
        raise HTTPException(400, detail="max_pages_per_pdf must be >= 1 when set")

    try:
        titles_list: list = json.loads(section_titles)
        if not isinstance(titles_list, list):
            raise ValueError("section_titles must be a JSON array")
        titles = [str(x) for x in titles_list]
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(400, detail=f"Invalid section_titles JSON: {e}") from e

    sections: list[PdfSection] = []
    for idx, up in enumerate(files):
        raw = await up.read()
        if not raw.startswith(b"%PDF"):
            raise HTTPException(
                400, detail=f"File {up.filename!r} does not look like a PDF"
            )
        name = up.filename or f"section_{idx}.pdf"
        title = titles[idx] if idx < len(titles) and titles[idx] else Path(name).stem
        sections.append(PdfSection(data=raw, filename=name, title=title))

    meta = ManualMeta(
        make=make.strip(),
        year_label=year_label.strip(),
        model_title=model_title.strip(),
        meta_description=meta_description.strip(),
    )
    if not meta.make or not meta.year_label or not meta.model_title:
        raise HTTPException(400, detail="make, year_label, and model_title are required")

    m: Mode = "embed" if mode == "embed" else "render"
    try:
        zip_bytes, root = build_charm_zip(
            sections,
            meta,
            mode=m,
            render_dpi=render_dpi,
            max_pages_per_pdf=max_pages_per_pdf,
        )
    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from e

    fname = _safe_zip_filename(root + ".zip")
    return StreamingResponse(
        BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
