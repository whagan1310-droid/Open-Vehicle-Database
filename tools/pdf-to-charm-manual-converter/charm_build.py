"""Build CHARM-style static HTML bundles from PDF bytes."""

from __future__ import annotations

import html
import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import fitz

Mode = Literal["embed", "render"]


@dataclass
class ManualMeta:
    make: str
    year_label: str
    model_title: str
    meta_description: str = ""


@dataclass
class PdfSection:
    data: bytes
    filename: str
    title: str


def _template_dir() -> Path:
    return Path(__file__).resolve().parent / "templates"


def _slug_folder(title: str) -> str:
    s = re.sub(r"[^\w\s\-]", "", title)
    s = re.sub(r"[-\s]+", "-", s).strip("-")
    return (s[:120] or "manual").strip("-")


def _safe_pdf_name(i: int, original: str) -> str:
    base = Path(original).name
    if not base.lower().endswith(".pdf"):
        base += ".pdf"
    base = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
    return f"{i:02d}_{base}" if base else f"{i:02d}.pdf"


def _esc(s: str) -> str:
    return html.escape(s, quote=True)


def _breadcrumbs_index(make: str, year: str, model: str) -> str:
    return (
        f"<a class='breadcrumb-part' href=\"\">Home</a> <b>&gt;&gt;</b> "
        f"<a class='breadcrumb-part' href=\"index.html\">{_esc(make)}</a> <b>&gt;&gt;</b> "
        f"<a class='breadcrumb-part' href=\"index.html\">{_esc(year)}</a> <b>&gt;&gt;</b> "
        f"<a class='breadcrumb-part' href=\"index.html\">{_esc(model)}</a>"
    )


def _breadcrumbs_pages(
    make: str,
    year: str,
    model: str,
    segments: list[tuple[str, str]],
) -> str:
    """segments: (href, label) for trail after model; last href can be current page."""
    out = (
        f"<a class='breadcrumb-part' href=\"../\">Home</a> <b>&gt;&gt;</b> "
        f"<a class='breadcrumb-part' href=\"../index.html\">{_esc(make)}</a> <b>&gt;&gt;</b> "
        f"<a class='breadcrumb-part' href=\"../index.html\">{_esc(year)}</a> <b>&gt;&gt;</b> "
        f"<a class='breadcrumb-part' href=\"../index.html\">{_esc(model)}</a>"
    )
    for href, label in segments:
        out += f" <b>&gt;&gt;</b> <a class='breadcrumb-part' href=\"{_esc(href)}\">{_esc(label)}</a>"
    return out


def _wrap_index(title: str, description: str, crumbs: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html>
  <head>
    <title>{_esc(title)} | Operation CHARM</title>
    <meta name='description' content="{_esc(description)}">
    <link rel='stylesheet' href="style.css">
    <meta name='viewport' content='width=device-width, initial-scale=1.0' />
  </head>
  <body>
    <div class='theme-colors header'>
      <div class='branding'><b>Operation CHARM</b>: Car repair manuals for everyone.</div>
<div class=breadcrumbs>{crumbs}</div></div>
<div class='main'>
{body}
</div>
<div class="theme-colors footer">
  <i>pro multis</i> · <a href="about.html">About Operation CHARM</a>
</div>
<script src="script.js"></script>
</body>
</html>"""


def _wrap_page(title: str, description: str, crumbs: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html>
  <head>
    <title>{_esc(title)} | Operation CHARM</title>
    <meta name='description' content="{_esc(description)}">
    <link rel='stylesheet' href="../style.css">
    <meta name='viewport' content='width=device-width, initial-scale=1.0' />
  </head>
  <body>
    <div class='theme-colors header'>
      <div class='branding'><b>Operation CHARM</b>: Car repair manuals for everyone.</div>
<div class=breadcrumbs>{crumbs}</div></div>
<div class='main'>
{body}
</div>
<div class="theme-colors footer">
  <i>pro multis</i> · <a href="../about.html">About Operation CHARM</a>
</div>
<script src="../script.js"></script>
</body>
</html>"""


def _add_file(z: zipfile.ZipFile, path: str, data: bytes) -> None:
    zi = zipfile.ZipInfo(path)
    zi.compress_type = zipfile.ZIP_DEFLATED
    z.writestr(zi, data)


def build_charm_zip(
    sections: list[PdfSection],
    meta: ManualMeta,
    mode: Mode,
    render_dpi: float = 110.0,
    max_pages_per_pdf: int | None = None,
) -> tuple[bytes, str]:
    """
    Returns (zip_bytes, root_folder_name_inside_zip).

    mode=embed: original PDFs under pdfs/ + hub pages with <object> embed.
    mode=render: rasterize each page to PNG + one HTML per page with prev/next.
    """
    if not sections:
        raise ValueError("At least one PDF section is required")

    root = _slug_folder(meta.model_title)
    td = _template_dir()
    buf = io.BytesIO()

    desc = meta.meta_description or f"Service manual for {meta.model_title}."

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in ("style.css", "script.js", "about.html"):
            p = td / name
            _add_file(z, f"{root}/{name}", p.read_bytes())
        for icon in ("folder.svg", "folder-open.svg"):
            p = td / "icons" / icon
            _add_file(z, f"{root}/icons/{icon}", p.read_bytes())

        index_items = []
        for i, sec in enumerate(sections):
            pdf_rel = f"pdfs/{_safe_pdf_name(i, sec.filename)}"
            _add_file(z, f"{root}/{pdf_rel}", sec.data)

            hub = f"pages/hub_{i}.html"
            if mode == "embed":
                body = f"""<h1>{_esc(sec.title)}</h1>
<p><a href="../{pdf_rel}">Download PDF</a></p>
<object data="../{pdf_rel}" type="application/pdf" width="100%" height="1200px">
<p>Your browser may not show embedded PDFs. <a href="../{pdf_rel}">Open the PDF</a>.</p>
</object>"""
                crumbs = _breadcrumbs_pages(
                    meta.make,
                    meta.year_label,
                    meta.model_title,
                    [(Path(hub).name, sec.title)],
                )
                html_page = _wrap_page(sec.title, desc, crumbs, body)
                _add_file(z, f"{root}/{hub}", html_page.encode("utf-8"))
                index_items.append(f'<li><a href="{hub}">{_esc(sec.title)}</a></li>')

            else:
                doc = fitz.open(stream=sec.data, filetype="pdf")
                try:
                    n = doc.page_count
                    if max_pages_per_pdf is not None:
                        n = min(n, max_pages_per_pdf)
                    scale = render_dpi / 72.0
                    mat = fitz.Matrix(scale, scale)

                    toc = doc.get_toc()
                    toc_lines: list[str] = []
                    if toc:
                        for lvl, title, page1 in toc:
                            if page1 < 1 or page1 > doc.page_count:
                                continue
                            if max_pages_per_pdf is not None and page1 > max_pages_per_pdf:
                                continue
                            phtml = f"s{i}_p{page1:04d}.html"
                            pad = "&nbsp;" * (max(0, (lvl - 1)) * 4)
                            toc_lines.append(
                                f"<li>{pad}<a href=\"{phtml}\">{_esc(title)}</a> "
                                f"<span style='color:#666'>(p. {page1})</span></li>"
                            )
                        if toc_lines:
                            toc_body = (
                                "<h2>PDF outline</h2><ul>"
                                + "".join(toc_lines)
                                + "</ul><p><a href=\"../index.html\">Manual home</a></p>"
                            )
                            hub_body = (
                                f"<h1>{_esc(sec.title)}</h1>"
                                f"<p><a href=\"toc_{i}.html\">Browse by PDF outline</a> "
                                f"or open the <a href=\"../{pdf_rel}\">original PDF</a>.</p>"
                                f"<p><a href=\"s{i}_p0001.html\">Start at page 1</a></p>"
                            )
                        else:
                            hub_body = (
                                f"<h1>{_esc(sec.title)}</h1>"
                                f"<p><a href=\"s{i}_p0001.html\">Start at page 1</a> · "
                                f"<a href=\"../{pdf_rel}\">Original PDF</a></p>"
                            )
                    else:
                        hub_body = (
                            f"<h1>{_esc(sec.title)}</h1>"
                            f"<p><a href=\"s{i}_p0001.html\">Start at page 1</a> · "
                            f"<a href=\"../{pdf_rel}\">Original PDF</a></p>"
                        )

                    hub_crumbs = _breadcrumbs_pages(
                        meta.make,
                        meta.year_label,
                        meta.model_title,
                        [(Path(hub).name, sec.title)],
                    )
                    _add_file(
                        z,
                        f"{root}/{hub}",
                        _wrap_page(sec.title, desc, hub_crumbs, hub_body).encode("utf-8"),
                    )

                    if toc and toc_lines:
                        toc_hub_name = f"pages/toc_{i}.html"
                        toc_crumbs = _breadcrumbs_pages(
                            meta.make,
                            meta.year_label,
                            meta.model_title,
                            [
                                (Path(hub).name, sec.title),
                                (Path(toc_hub_name).name, "Outline"),
                            ],
                        )
                        _add_file(
                            z,
                            f"{root}/{toc_hub_name}",
                            _wrap_page(
                                f"{sec.title} — outline",
                                desc,
                                toc_crumbs,
                                toc_body,
                            ).encode("utf-8"),
                        )

                    for pidx in range(n):
                        page_no = pidx + 1
                        page = doc.load_page(pidx)
                        pix = page.get_pixmap(matrix=mat, alpha=False)
                        img_name = f"images/s{i}/page_{page_no:04d}.png"
                        _add_file(z, f"{root}/{img_name}", pix.tobytes(output="png"))

                        if pidx == 0:
                            prev_link = f'<a href="hub_{i}.html">Section home</a>'
                        else:
                            prev_link = f'<a href="s{i}_p{pidx:04d}.html">Previous</a>'

                        if pidx + 1 < n:
                            next_link = f'<a href="s{i}_p{page_no + 1:04d}.html">Next</a>'
                        else:
                            next_link = '<span>End</span>'

                        fname = f"s{i}_p{page_no:04d}.html"
                        crumbs = _breadcrumbs_pages(
                            meta.make,
                            meta.year_label,
                            meta.model_title,
                            [
                                (f"hub_{i}.html", sec.title),
                                (fname, f"Page {page_no}"),
                            ],
                        )
                        img_rel = f"../{img_name}"
                        pbody = f"""<p>{prev_link} · {next_link} · <a href="../{pdf_rel}">PDF</a></p>
<p><img src="{_esc(img_rel)}" alt="page {page_no}" style="max-width:100%;height:auto;border:1px solid #333;" /></p>
<p>{prev_link} · {next_link}</p>"""
                        _add_file(
                            z,
                            f"{root}/pages/{fname}",
                            _wrap_page(
                                f"{sec.title} — page {page_no}",
                                desc,
                                crumbs,
                                pbody,
                            ).encode("utf-8"),
                        )
                finally:
                    doc.close()

                index_items.append(f'<li><a href="{hub}">{_esc(sec.title)}</a> (rendered pages)</li>')

        h1 = f"{_esc(meta.make)}: {_esc(meta.year_label)}: {_esc(meta.model_title)}"
        index_body = f"<h1>{h1}</h1><ul>{''.join(index_items)}</ul>"
        index_html = _wrap_index(
            f"{meta.model_title} service manual",
            desc,
            _breadcrumbs_index(meta.make, meta.year_label, meta.model_title),
            index_body,
        )
        _add_file(z, f"{root}/index.html", index_html.encode("utf-8"))

    return buf.getvalue(), root
