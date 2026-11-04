#!/usr/bin/env python3
"""Build the Intel Bob Research Archive static site.

Reads projects.json, converts each project's .docx to HTML with mammoth,
extracts hyperlinks as a references list, copies original files for download,
and writes everything to dist/.

Usage:  .venv/bin/python build.py        (or: python3 build.py, if mammoth is installed)
"""
import html, json, os, re, shutil, sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import mammoth

import v2

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
MANIFEST = ROOT / "projects.json"

STYLE_MAP = """
p[style-name='Title'] => h1.doc-title:fresh
p[style-name='Subtitle'] => p.doc-subtitle:fresh
p[style-name='Caption'] => p.caption:fresh
p[style-name='Quote'] => blockquote > p:fresh
p[style-name='Intense Quote'] => blockquote.intense > p:fresh
p[style-name='List Bullet'] => ul > li:fresh
p[style-name='List Number'] => ol > li:fresh
p[style-name='TOC Heading'] => h2.toc-heading:fresh
p[style-name^='toc '] => p.word-toc:fresh
p[style-name^='TOC '] => p.word-toc:fresh
r[style-name='Strong'] => strong
"""

def esc(s):
    return html.escape(str(s), quote=True)

def slugify(s):
    s = re.sub(r"[^\w\s-]", "", s.lower(), flags=re.U)
    return re.sub(r"[\s_-]+", "-", s).strip("-")[:60] or "section"

def human_size(n):
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"

def fmt_date(iso):
    d = datetime.fromisoformat(iso)
    return d.strftime("%b %-d, %Y")

def page(title, body, depth=0, desc=""):
    pre = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="stylesheet" href="{pre}assets/style.css">
<script>(function(){{try{{var t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t;}}catch(e){{}}}})();</script>
</head>
<body>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="{pre}index.html"><span class="logo" aria-hidden="true">◉</span> Intel Bob Research Archive</a>
    <button class="theme-toggle" type="button" aria-label="Toggle light or dark theme" title="Toggle theme">◐</button>
  </div>
</header>
{body}
<footer class="site-footer"><div class="wrap">Intel Bob Research Archive · built {datetime.now().strftime('%b %-d, %Y %H:%M')} (America/Los_Angeles)</div></footer>
<script src="{pre}assets/theme.js"></script>
</body>
</html>"""

def convert_doc(docx_path, out_dir):
    """Return (html, warnings, image_count)."""
    img_dir = out_dir / "img"
    counter = {"n": 0}

    def save_image(image):
        counter["n"] += 1
        ext = (image.content_type or "image/png").split("/")[-1].replace("jpeg", "jpg").replace("x-emf", "emf")
        name = f"image-{counter['n']}.{ext}"
        img_dir.mkdir(parents=True, exist_ok=True)
        with image.open() as src, open(img_dir / name, "wb") as dst:
            shutil.copyfileobj(src, dst)
        attrs = {"src": f"img/{name}", "loading": "lazy"}
        if image.alt_text:
            attrs["alt"] = image.alt_text
        else:
            attrs["alt"] = f"Figure {counter['n']}"
        return attrs

    with open(docx_path, "rb") as f:
        result = mammoth.convert_to_html(
            f, style_map=STYLE_MAP, convert_image=mammoth.images.img_element(save_image)
        )
    warnings = [m.message for m in result.messages if m.type in ("warning", "error")]
    return result.value, warnings, counter["n"]

A_RE = re.compile(r'<a\s+([^>]*?)href="([^"]+)"([^>]*)>(.*?)</a>', re.S | re.I)
H_RE = re.compile(r"<(h[1-4])([^>]*)>(.*?)</\1>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")

URL_RE = re.compile(r'https?://[^\s<>"\']+')

def autolink(body):
    """Turn bare URLs in text (outside existing <a>) into hyperlinks."""
    out, in_a = [], 0
    for part in re.split(r"(<[^>]+>)", body):
        if part.startswith("<"):
            low = part.lower()
            if low.startswith("<a ") or low == "<a>":
                in_a += 1
            elif low.startswith("</a"):
                in_a = max(0, in_a - 1)
            out.append(part)
        elif in_a or "http" not in part:
            out.append(part)
        else:
            def rep(m):
                url = m.group(0)
                trail = ""
                while url and url[-1] in ".,;:)]}":
                    trail = url[-1] + trail; url = url[:-1]
                return f'<a href="{url}">{url}</a>{trail}'
            out.append(URL_RE.sub(rep, part))
    return "".join(out)

def postprocess(body):
    """Open external links in new tab, add heading ids, wrap tables. Returns (body, toc, links)."""
    links, seen = [], {}
    body = autolink(body)

    def fix_a(m):
        pre_attrs, href, post_attrs, inner = m.groups()
        text = html.unescape(TAG_RE.sub("", inner)).strip()
        if href.startswith(("http://", "https://")):
            key = html.unescape(href)
            if key not in seen:
                seen[key] = len(links)
                links.append({"url": key, "text": text, "domain": urlparse(key).netloc.replace("www.", "")})
            elif text and len(text) > len(links[seen[key]]["text"]) and not text.startswith("http"):
                pass
            return f'<a {pre_attrs}href="{href}"{post_attrs} target="_blank" rel="noopener noreferrer">{inner}</a>'
        return m.group(0)

    body = A_RE.sub(fix_a, body)

    toc, used = [], set()

    def fix_h(m):
        tag, attrs, inner = m.groups()
        text = html.unescape(TAG_RE.sub("", inner)).strip()
        if not text:
            return m.group(0)
        hid = slugify(text)
        base, i = hid, 2
        while hid in used:
            hid = f"{base}-{i}"; i += 1
        used.add(hid)
        if tag.lower() in ("h1", "h2") and "doc-title" not in attrs and "toc-heading" not in attrs:
            toc.append((tag.lower(), text, hid))
        # keep any mammoth bookmark anchors inside
        return f'<{tag}{attrs} id="{hid}">{inner}</{tag}>'

    body = H_RE.sub(fix_h, body)
    body = re.sub(r"<table(\s[^>]*)?>", lambda m: '<div class="table-wrap">' + m.group(0), body).replace("</table>", "</table></div>")
    # mammoth nests tables in tables occasionally; fine either way
    return body, toc, links

def model_body(p):
    """HTML body for an interactive-model entry (no .docx): description, what to explore, static tables."""
    parts = ["<h2>About this model</h2>"] + [f"<p>{esc(t)}</p>" for t in p.get("description", [])]
    if p.get("explore"):
        parts.append("<h2>What you can explore</h2><ul>" + "".join(f"<li>{esc(t)}</li>" for t in p["explore"]) + "</ul>")
    if p.get("tables"):
        parts.append("<h2>Static summary</h2>")
        if p.get("table_note"):
            parts.append(f'<p class="caption-note">{esc(p["table_note"])}</p>')
        for t in p["tables"]:
            head = "".join(f"<th>{esc(c)}</th>" for c in t["columns"])
            rows = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in t["rows"])
            parts.append(f'<h3>{esc(t["title"])}</h3><table class="model-table"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>')
    if p.get("sources"):
        parts.append("<h2>Sources cited in the model</h2><ul>" + "".join(
            f'<li><a href="{esc(x["href"])}">{esc(x["title"])}</a> ({esc(x["site"])})</li>' for x in p["sources"]) + "</ul>")
    parts.append(f'<h2>Open the model</h2><p>The live, interactive version is a Grok Bot page: '
                 f'<a href="{esc(p["model_url"])}">{esc(p["title"])}</a>. {esc(p.get("sign_in_note", ""))} '
                 f'This archive page is a static summary only; it does not re-implement the model.</p>')
    return "\n".join(parts)

def build():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    src_dir = Path(manifest.get("source_dir", "/workspace"))
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "assets").mkdir(parents=True)
    for f in SRC.glob("*"):
        if f.is_file():
            shutil.copy2(f, DIST / "assets" / f.name)
    v2.copy_assets(SRC / "v2", DIST / "v2")
    files_dir = DIST / "files"
    files_dir.mkdir()

    report, cards = [], []
    by_slug = {q["slug"]: q for q in manifest["projects"]}
    for p in manifest["projects"]:
        slug = p["slug"]
        out_dir = DIST / "projects" / slug
        out_dir.mkdir(parents=True)
        is_model = p.get("type") == "model"
        doc_path = src_dir / p["doc"] if p.get("doc") else None
        if not is_model and (doc_path is None or not doc_path.exists()):
            print(f"!! missing {doc_path}, skipping {slug}", file=sys.stderr)
            report.append((slug, "MISSING", []))
            continue

        downloads = []
        for rel in ([p["doc"]] if p.get("doc") else []) + p.get("related_files", []):
            fp = src_dir / rel
            if not fp.exists():
                print(f"!! missing related file {fp}", file=sys.stderr)
                continue
            shutil.copy2(fp, files_dir / fp.name)
            downloads.append({"name": fp.name, "href": f"files/{fp.name}", "size": human_size(fp.stat().st_size),
                              "ext": fp.suffix.lstrip(".").upper()})

        if is_model:
            raw, warnings, n_img = model_body(p), [], 0
        else:
            raw, warnings, n_img = convert_doc(doc_path, out_dir)
        body, toc, links = postprocess(raw)
        related = [by_slug[r] for r in p.get("related_projects", []) if r in by_slug]

        dl_html = "".join(
            f'<a class="dl" href="../../{d["href"]}" download><span class="ext ext-{d["ext"].lower()}">{d["ext"]}</span>{esc(d["name"])} <small>{d["size"]}</small></a>'
            for d in downloads)
        tags_html = "".join(f'<a class="tag" href="../../index.html?tag={esc(t)}">{esc(t)}</a>' for t in p["tags"])
        stats_html = "".join(f"<li>{esc(s)}</li>" for s in p.get("stats", []))
        toc_html = "".join(
            f'<li class="toc-{lvl}"><a href="#{hid}">{esc(text)}</a></li>' for lvl, text, hid in toc)
        toc_html += f'<li class="toc-h2"><a href="#references">Extracted links ({len(links)})</a></li>' if links else ""
        refs_html = "".join(
            f'<li><a href="{esc(l["url"])}" target="_blank" rel="noopener noreferrer">{esc(l["text"] if l["text"] and l["text"] != l["url"] else l["url"])}</a>'
            f' <span class="domain">{esc(l["domain"])}</span></li>' for l in links)
        refs_block = (f'<section class="refs" id="references"><h2>Extracted links <span class="count">{len(links)}</span></h2>'
                      f'<p class="muted">Every unique external hyperlink found in the document, in order of first appearance.</p>'
                      f'<input class="ref-filter" type="search" placeholder="Filter links…" aria-label="Filter links">'
                      f'<ol class="ref-list">{refs_html}</ol></section>') if links else ""

        disclaimer_html = f'<p class="disclaimer" role="note"><strong>⚠ {esc(p["disclaimer"])}</strong></p>' if p.get("disclaimer") else ""
        model_html = (f'<div class="model-cta"><a class="btn-primary" href="{esc(p["model_url"])}" target="_blank" rel="noopener noreferrer">Open interactive model ↗</a>'
                      f'<p class="muted signin">{esc(p.get("sign_in_note", ""))}</p></div>') if p.get("model_url") else ""
        related_html = ('<p class="related">Related: ' + " · ".join(
            f'<a href="../{esc(r["slug"])}/index.html">{esc(r["title"])}</a>' for r in related) + "</p>") if related else ""
        detail = f"""
<main class="wrap detail">
  <nav class="crumbs"><a href="../../index.html">← All projects</a></nav>
  <header class="detail-head">
    <time datetime="{esc(p['date'])}">{fmt_date(p['date'])}</time>
    <h1>{esc(p['title'])}</h1>
    <div class="tags">{tags_html}</div>
    {disclaimer_html}
    <p class="summary">{esc(p['summary'])}</p>
    <ul class="stats">{stats_html}</ul>
    {model_html}
    <div class="downloads">{dl_html}</div>
    {related_html}
  </header>
  <div class="detail-grid">
    <aside class="toc"><details open><summary>Contents</summary><ol>{toc_html}</ol></details></aside>
    <div class="content-col">
      <article class="doc">{body}</article>
      {refs_block}
    </div>
  </div>
</main>
<script src="../../assets/detail.js"></script>"""
        (out_dir / "index.html").write_text(page(p["title"] + " · Intel Bob Research Archive", detail, depth=2, desc=p["summary"]), encoding="utf-8")

        v2_dir = DIST / "v2" / "projects" / slug
        v2_dir.mkdir(parents=True, exist_ok=True)
        (v2_dir / "index.html").write_text(v2.detail(p, body, toc, links, downloads, related=related), encoding="utf-8")

        cards.append({**p, "url": f"projects/{slug}/index.html", "downloads": downloads,
                      "related_titles": [{"slug": r["slug"], "title": r["title"]} for r in related],
                      "date_label": fmt_date(p["date"]), "links_found": len(links), "images": n_img})
        report.append((slug, f"ok · {len(links)} links · {n_img} images · {len(warnings)} warnings", warnings))

    data = {"title": manifest["site_title"], "subtitle": manifest.get("site_subtitle", ""), "projects": cards}
    (DIST / "projects.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    all_tags = sorted({t for c in cards for t in c["tags"]})
    noscript = "".join(f'<li><a href="{esc(c["url"])}">{esc(c["title"])}</a> ({c["date_label"]})</li>' for c in sorted(cards, key=lambda c: c["date"], reverse=True))
    index_body = f"""
<main class="wrap">
  <section class="hero">
    <h1>{esc(manifest['site_title'])}</h1>
    <p>{esc(manifest.get('site_subtitle',''))}</p>
  </section>
  <section class="controls" aria-label="Search and filter">
    <input id="q" type="search" placeholder="Search titles, summaries, stats…" aria-label="Search projects" autocomplete="off">
    <button id="sort" type="button" class="btn" aria-label="Toggle sort order">Newest first ↓</button>
  </section>
  <div id="tagbar" class="tagbar" role="group" aria-label="Filter by tag"></div>
  <p id="count" class="muted" aria-live="polite"></p>
  <section id="cards" class="cards"><noscript><ul>{noscript}</ul></noscript></section>
</main>
<script id="data" type="application/json">{json.dumps(data, ensure_ascii=False).replace('</', '<\\/')}</script>
<script src="assets/app.js"></script>"""
    (DIST / "index.html").write_text(page(manifest["site_title"], index_body, depth=0, desc=manifest.get("site_subtitle", "")), encoding="utf-8")

    (DIST / "v2" / "index.html").write_text(v2.index(manifest, cards), encoding="utf-8")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")  # GitHub Pages: serve files as-is, no Jekyll

    print(f"Built {len(cards)} projects (classic view at /, v2 view at /v2/) into {DIST} ({len(all_tags)} tags)")
    for slug, status, warnings in report:
        print(f"  {slug}: {status}")
        for w in sorted(set(warnings))[:8]:
            print(f"      - {w}")

if __name__ == "__main__":
    build()
