"""V2 view: minimal, dark, uppercase design (Paul's default web design system).

Generated into dist/v2/ by build.py. Shares dist/files/ (downloads) and
dist/projects/<slug>/img/ (document images) with the original view.
"""
import html, json, shutil
from datetime import datetime
from pathlib import Path

def esc(s):
    return html.escape(str(s), quote=True)

def short_summary(p):
    if p.get("short_summary"):
        return p["short_summary"]
    import re
    parts = re.split(r"(?<=[.!?])\s+", p["summary"].strip())
    return " ".join(parts[:2])

def page(title, body, depth, desc=""):
    pre = "../" * depth          # relative path to dist/v2/
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#000000">
<meta name="color-scheme" content="dark">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="preload" href="{pre}assets/fonts/Barlow-Bold.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{pre}assets/fonts/Barlow-Regular.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{pre}assets/v2.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="nav">
  <div class="container nav-inner">
    <a class="brand" href="{pre}index.html">Intel Bob <span>Research Archive</span></a>
    <a class="nav-link" href="{pre}../index.html">Classic view</a>
  </div>
</header>
{body}
<footer class="footer">
  <div class="container footer-inner">
    <span>Intel Bob Research Archive © 2026</span>
    <span>Built {datetime.now().strftime('%b %-d, %Y %H:%M')} PT</span>
  </div>
</footer>
</body>
</html>"""

def detail(p, body, toc, links, downloads, depth=2, related=()):
    slug = p["slug"]
    # images live with the original view; downloads are shared
    body = body.replace('src="img/', f'src="../../../projects/{slug}/img/')
    tags = "".join(f"<li>{esc(t)}</li>" for t in p["tags"])
    stats = "".join(f"<li>{esc(s)}</li>" for s in p.get("stats", []))
    dls = "".join(
        f'<a class="btn" href="../../../{d["href"]}" download>Download {esc(d["ext"])}'
        f'<span class="btn-sub">{esc(d["name"])} · {esc(d["size"])}</span><span class="arrow" aria-hidden="true">↓</span></a>'
        for d in downloads)
    disc = (f'<p class="disclaimer" role="note"><span aria-hidden="true">⚠</span> {esc(p["disclaimer"])}</p>'
            if p.get("disclaimer") else "")
    if p.get("model_url"):
        dls = (f'<a class="btn btn-white" href="{esc(p["model_url"])}" target="_blank" rel="noopener noreferrer">'
               f'Open interactive model<span class="arrow" aria-hidden="true">↗</span></a>') + dls
    signin = f'<p class="signin">{esc(p["sign_in_note"])}</p>' if p.get("sign_in_note") else ""
    rel = ("<p class=\"related\"><span>Related</span>" + "".join(
        f'<a href="../{esc(r["slug"])}/index.html">{esc(r["title"])} →</a>' for r in related) + "</p>") if related else ""
    toc_items = "".join(f'<li class="lvl-{lvl}"><a href="#{hid}">{esc(text)}</a></li>' for lvl, text, hid in toc)
    if links:
        toc_items += f'<li class="lvl-h1"><a href="#links">Links ({len(links)})</a></li>'
    toc_html = (f'<details class="contents"><summary>Contents</summary><ol>{toc_items}</ol></details>'
                if toc_items else "")
    refs = ""
    if links:
        items = "".join(
            f'<li><a href="{esc(l["url"])}" target="_blank" rel="noopener noreferrer">'
            f'{esc(l["text"] if l["text"] and l["text"] != l["url"] else l["url"])}</a>'
            f'<span class="domain">{esc(l["domain"])}</span></li>' for l in links)
        refs = (f'<section class="links" id="links"><h2>Links <span class="count">{len(links)}</span></h2>'
                f'<p class="note">Every unique external link in the document, in order of first appearance.</p>'
                f'<label class="sr" for="lf">Filter links</label>'
                f'<input id="lf" class="input" type="search" placeholder="Filter links" autocomplete="off">'
                f'<ol class="link-list">{items}</ol></section>')
    main = f"""
<main id="main" class="container">
  <a class="back" href="../../index.html"><span aria-hidden="true">←</span> All reports</a>
  <header class="report-head">
    <p class="eyebrow"><time datetime="{esc(p['date'])}">{esc(fmt_date(p['date']))}</time></p>
    <h1>{esc(p['title'])}</h1>
    {disc}
    <ul class="tags">{tags}</ul>
    <p class="lede">{esc(p['summary'])}</p>
    <ul class="stats">{stats}</ul>
    <div class="actions">{dls}</div>
    {signin}
    {rel}
  </header>
  {toc_html}
  <article class="doc">{body}</article>
  {refs}
</main>
<script src="../../assets/v2.js"></script>"""
    return page(p["title"] + " · Intel Bob Research Archive", main, depth, p["summary"])

def fmt_date(iso):
    return datetime.fromisoformat(iso).strftime("%b %-d, %Y")

def index(manifest, cards):
    rows = []
    for c in sorted(cards, key=lambda c: c["date"], reverse=True):
        search = " ".join([c.get("disclaimer", ""), c["title"], c["summary"], " ".join(c["tags"]), " ".join(c.get("stats", []))]).lower()
        rows.append(f"""
  <li class="banner" data-search="{esc(search)}">
    <div class="banner-meta">
      <time datetime="{esc(c['date'])}">{esc(c['date_label'])}</time>
      <span class="banner-tags">{esc(' · '.join(c['tags']))}</span>
    </div>
    <div class="banner-body">
      <h2><a href="projects/{esc(c['slug'])}/index.html">{esc(c['title'])}</a></h2>
      <p>{esc(short_summary(c))}</p>
      {f'<p class="disclaimer">⚠ {esc(c["disclaimer"])}</p>' if c.get("disclaimer") else ""}
    </div>
    <span class="banner-go" aria-hidden="true">→</span>
  </li>""")
    main = f"""
<main id="main" class="container">
  <section class="hero">
    <p class="eyebrow">Intel Bob · {len(cards)} reports</p>
    <h1>Research Archive</h1>
    <p class="lede">Satellite communications, government directories, telecom strategy and financial analysis, newest first.</p>
    <div class="search">
      <label class="sr" for="q">Search reports</label>
      <input id="q" class="input" type="search" placeholder="Search reports" autocomplete="off">
      <span id="count" class="count-line" aria-live="polite"></span>
    </div>
  </section>
  <ol class="banners" id="banners">{''.join(rows)}
  </ol>
  <p class="empty" id="empty" hidden>No reports match your search.</p>
</main>
<script src="assets/v2.js"></script>"""
    return page(manifest["site_title"], main, 0, manifest.get("site_subtitle", ""))

def copy_assets(src_v2: Path, dist_v2: Path):
    assets = dist_v2 / "assets"
    if assets.exists():
        shutil.rmtree(assets)
    shutil.copytree(src_v2, assets)
