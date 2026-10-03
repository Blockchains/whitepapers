#!/usr/bin/env python3
"""Build the whitepaper index from blockchainlab.com (links only — PDFs are NOT re-hosted).

Sources (all public): every sitemap listed in https://blockchainlab.com/robots.txt (PDF <loc>s and
/research/corpus/papers/* records) and the library page https://blockchainlab.com/pdf (<article> cards:
h2 = project, h3 = title/subtitle). Year comes from the corpus record's JSON-LD datePublished when a record
links the same PDF; otherwise from an explicit year in the filename (marked "filename"); otherwise blank.
Writes index.json, index.csv and README.md. Python 3 stdlib only."""
import csv, html, json, re, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import unquote, urljoin

BASE = "https://blockchainlab.com"
UA = "Mozilla/5.0 (X11; Linux x86_64) WhitepaperIndex/1.0 (+https://github.com/Blockchains/whitepapers)"


def get(url, method="GET", n=3_000_000):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.getcode(), r.headers.get("content-type", ""), (r.read(n) if method == "GET" else b"")
    except urllib.error.HTTPError as e:
        return e.code, "", b""
    except Exception:
        return None, "", b""


def text(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def main():
    _, _, robots = get(BASE + "/robots.txt")
    sitemaps = re.findall(r"(?im)^sitemap:\s*(\S+)", robots.decode("utf-8", "replace")) or [BASE + "/sitemap.xml"]
    locs = []
    for sm in sitemaps:
        _, _, b = get(sm)
        locs += re.findall(r"<loc>([^<]+)</loc>", b.decode("utf-8", "replace"))
    pdfs = {u for u in locs if re.search(r"/pdf/[^/]+\.pdf$", u, re.I)}
    records = sorted({u for u in locs if "/research/corpus/papers/" in u})
    # library page cards
    _, _, page = get(BASE + "/pdf")
    page = page.decode("utf-8", "replace")
    cards = {}
    for art in re.findall(r"<article\b.*?</article>", page, re.S):
        m = re.search(r'href="(/pdf/[^"]+\.pdf)"', art)
        if m:
            cards[urljoin(BASE, m.group(1))] = {"project": text((re.search(r"<h2[^>]*>(.*?)</h2>", art, re.S) or [None, ""])[1]),
                                               "subtitle": text((re.search(r"<h3[^>]*>(.*?)</h3>", art, re.S) or [None, ""])[1])}
    for li in re.findall(r"<li\b[^>]*>(?:(?!</li>).)*?href=\"/pdf/.*?</li>", page, re.S):
        m = re.search(r'<a href="(/pdf/[^"]+\.pdf)">(.*?)</a>', li, re.S)
        if m:
            u = urljoin(BASE, m.group(1))
            note = text((re.search(r'<p class="mt-1[^"]*">(.*?)</p>', li, re.S) or [None, ""])[1])
            cards.setdefault(u, {"project": text(m.group(2)), "subtitle": note})
    for a in re.findall(r'href="(/pdf/[^"]+\.pdf)"', page):
        pdfs.add(urljoin(BASE, a))
    # corpus records -> year/title/authors by PDF
    def rec(u):
        _, _, b = get(u)
        s = b.decode("utf-8", "replace")
        out = []
        for j in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try:
                d = json.loads(j)
            except Exception:
                continue
            if d.get("@type") == "ScholarlyArticle":
                for p in set(re.findall(r'href="(/pdf/[^"]+\.pdf)"', s)):
                    out.append((urljoin(BASE, p), {"year": str(d.get("datePublished") or "")[:4], "record": u,
                                                   "headline": d.get("headline", ""),
                                                   "authors": ", ".join(a.get("name", "") for a in d.get("author", []) if isinstance(a, dict))}))
        return out
    meta = {}
    with ThreadPoolExecutor(8) as ex:
        for lst in ex.map(rec, records):
            for p, m in lst:
                meta.setdefault(p, m)
    def check(u):
        code, ctype, _ = get(u, method="HEAD")
        return u, code, ctype
    with ThreadPoolExecutor(8) as ex:
        status = {u: (c, t) for u, c, t in ex.map(check, sorted(pdfs))}
    rows = []
    for u in sorted(pdfs, key=lambda x: unquote(x).lower()):
        fn = unquote(u.rsplit("/", 1)[1])
        c, m = cards.get(u, {}), meta.get(u, {})
        project = c.get("project") or (m.get("headline") or "")
        title = m.get("headline") or " — ".join(x for x in (c.get("project"), c.get("subtitle")) if x) or fn
        year, ysrc = m.get("year", ""), "corpus record" if m.get("year") else ""
        if not year:
            fy = re.match(r"(20[0-2]\d|199\d)-\d\d", fn) or re.search(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-_]?(20[0-2]\d)(?!\d)", fn)
            if fy:
                year, ysrc = fy.group(1), "filename"  # only dated filenames (YYYY-MM… or Mon2016)
        rows.append({"title": title, "project": project, "year": year, "year_source": ysrc, "authors": m.get("authors", ""),
                     "file": fn, "url": u, "corpus_record": m.get("record", ""), "http_status": status[u][0],
                     "is_pdf": "pdf" in (status[u][1] or "").lower()})
    json.dump({"source": BASE + "/pdf", "count": len(rows), "papers": rows}, open("index.json", "w"), indent=1, ensure_ascii=False)
    with open("index.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    md = lambda s: str(s).replace("|", "\\|")
    lines = ["# Whitepapers — Blockchain Lab archive index", "",
             f"An index of the {len(rows)} historic whitepapers in the [Blockchain Lab PDF library](https://blockchainlab.com/pdf).",
             "**PDFs are not re-hosted here** — every link points at the original file on blockchainlab.com.", "",
             "Generated by [`scripts/build_index.py`](scripts/build_index.py) from blockchainlab.com's sitemaps and `/pdf` page; "
             "refreshed weekly by [`.github/workflows/refresh-index.yml`](.github/workflows/refresh-index.yml). Machine-readable: "
             "[`index.json`](index.json), [`index.csv`](index.csv).", "",
             "Year: from the site's corpus record (JSON-LD `datePublished`) where one exists, else an explicit year in the filename (marked †), else blank.", "",
             "| # | Title | Project | Year | Link |", "|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        y = r["year"] + (" †" if r["year_source"] == "filename" else "")
        rec_link = f" · [record]({r['corpus_record']})" if r["corpus_record"] else ""
        bad = "" if r["http_status"] == 200 else f" ⚠️ HTTP {r['http_status']}"
        lines.append(f"| {i} | {md(r['title'])} | {md(r['project'])} | {y} | [PDF]({r['url']}){rec_link}{bad} |")
    lines += ["", "Rights in each paper remain with its authors/publishers. This repository only lists links."]
    open("README.md", "w").write("\n".join(lines) + "\n")
    print(f"{len(rows)} papers; with year {sum(1 for r in rows if r['year'])}; non-200 {sum(1 for r in rows if r['http_status'] != 200)}")


if __name__ == "__main__":
    main()
