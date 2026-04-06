#!/usr/bin/env python3
"""
Fetch a lemon-manuals.la manual index page (e.g. Repair and Diagnosis or Parts and Labor)
and print JSON { "sourceUrl", "titles" } for pasting into the catalog TOC box.

Same data shape as the in-browser bookmarklet. Use when you prefer a script over
the bookmarklet.

Example:
  python scripts/fetch_charm_section_toc.py \\
    "https://lemon-manuals.la/Chevrolet/2009/Silverado%201500%204WD%20V8-6.0L/Repair%20and%20Diagnosis/"
"""
from __future__ import annotations

import argparse
import http.client
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from io import BytesIO

UA = "Open-Vehicle-Database-toc-fetch/1.0 (+https://github.com)"

A_RE = re.compile(
    r"<a\b[^>]*\bhref\s*=\s*(['\"])([^'\"]+)\1[^>]*>([^<]*)</a>",
    re.IGNORECASE,
)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read().decode("utf-8", errors="replace")


class CharmSession:
    """
    Reuse one HTTPS connection to lemon-manuals.la (or another host) for many GETs.
    Cuts TLS handshake overhead vs. one urllib.urlopen per URL — same request
    rate as sequential fetches, less connection churn on the server.
    """

    def __init__(self, host: str, timeout: float = 90.0):
        self.host = host.lower().split(":")[0]  # strip :port if present
        self.timeout = timeout
        self._conn: http.client.HTTPSConnection | None = None

    def __enter__(self) -> CharmSession:
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except OSError:
                pass
            self._conn = None

    def _connect(self) -> http.client.HTTPSConnection:
        if self._conn is None:
            self._conn = http.client.HTTPSConnection(self.host, timeout=self.timeout)
        return self._conn

    def fetch(self, url: str) -> str:
        u = urllib.parse.urlparse(url)
        if u.scheme.lower() != "https" or u.netloc.lower().split(":")[0] != self.host:
            return fetch(url)

        req_path = u.path or "/"
        if u.query:
            req_path += "?" + u.query

        last: BaseException | None = None
        for attempt in range(2):
            try:
                conn = self._connect()
                conn.request(
                    "GET",
                    req_path,
                    headers={
                        "Host": u.netloc,
                        "User-Agent": UA,
                        "Accept-Encoding": "identity",
                        "Connection": "keep-alive",
                    },
                )
                resp = conn.getresponse()
                body = resp.read()
                st = resp.status
                if st in (301, 302, 303, 307, 308):
                    self.close()
                    loc = resp.getheader("Location")
                    if loc:
                        return fetch(urllib.parse.urljoin(url, loc))
                    raise urllib.error.HTTPError(
                        url, st, resp.reason, resp.headers, BytesIO(body)
                    )
                if st >= 400:
                    self.close()
                    raise urllib.error.HTTPError(
                        url, st, resp.reason, resp.headers, BytesIO(body)
                    )
                return body.decode("utf-8", errors="replace")
            except urllib.error.HTTPError:
                raise
            except (http.client.HTTPException, OSError, TimeoutError) as e:
                last = e
                self.close()
                if attempt == 0:
                    continue
                raise urllib.error.URLError(str(e)) from e

        assert last is not None
        raise urllib.error.URLError(str(last)) from last


def titles_from_html(page_url: str, html: str) -> list[str]:
    page_u = urllib.parse.urlparse(page_url)
    base_path = page_u.path
    if not base_path.endswith("/"):
        base_path += "/"
    seen: set[str] = set()
    titles: list[str] = []
    for _q, href, text in A_RE.findall(html):
        abs_u = urllib.parse.urljoin(page_url, href)
        pu = urllib.parse.urlparse(abs_u)
        if pu.netloc.lower() != page_u.netloc.lower():
            continue
        path = pu.path
        if not path.endswith("/"):
            path += "/"
        if not path.startswith(base_path) or path == base_path:
            continue
        t = re.sub(r"\s+", " ", text.strip())
        if len(t) < 2:
            continue
        k = t.lower()
        if k in seen:
            continue
        seen.add(k)
        titles.append(t)
    titles.sort(key=str.lower)
    return titles


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("url", help="Full URL to the expanded section root on lemon-manuals.la")
    p.add_argument(
        "--compact",
        action="store_true",
        help="Single-line JSON (easier to paste into some tools)",
    )
    args = p.parse_args()
    html = fetch(args.url)
    titles = titles_from_html(args.url, html)
    out = {"sourceUrl": args.url, "titles": titles}
    if args.compact:
        print(json.dumps(out, separators=(",", ":")))
    else:
        print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
