# Intel Bob Research Archive

A static site that stores and displays every research project Intel Bob produced for Paul.

```
research-site/
├── projects.json     # manifest: one entry per project (edit this to add projects)
├── build.py          # regenerates dist/ from projects.json + the .docx files in /workspace
├── serve.sh          # rebuild + start local server + public tunnel (prints URL)
├── src/              # site assets: style.css, app.js (search/filter/sort), detail.js, theme.js
└── dist/             # build output (do not edit by hand; it is wiped on every build)
```

## Build

```bash
cd /workspace/research-site
.venv/bin/python build.py        # venv already has mammoth + python-docx
# fresh machine: python3 -m venv .venv && .venv/bin/pip install mammoth python-docx
```

The build converts each `.docx` to HTML with mammoth (headings, tables, lists, bold/italic,
embedded images, hyperlinks), auto-links bare URLs, builds a contents sidebar from H1/H2, extracts
every unique external link into a filterable "Extracted links" list, and copies the original
files into `dist/files/` for download. It prints link/image/warning counts per project.

## Add a project

1. Save the Word doc (and any related .xlsx/.csv/.pdf) in `/workspace` (subfolders are fine).
2. Add an entry to the `projects` array in `projects.json`:

```json
{
  "slug": "my-new-project",                    // URL: projects/my-new-project/
  "title": "My New Project",
  "date": "2026-11-02T10:00",                  // used for newest/oldest sorting
  "tags": ["LEO Satellite", "Financial"],      // reuse existing tags where possible
  "summary": "Two or three sentences shown on the card and the detail page.",
  "stats": ["12 pages", "40 references"],      // short key-stat pills
  "doc": "My_New_Project.docx",                // path relative to source_dir (/workspace)
  "related_files": ["My_New_Project.xlsx"],    // optional extra downloads
  "short_summary": "One or two sentences for the v2 banner."  // optional; falls back to the first 2 sentences of summary
}
```

3. Run `./serve.sh` (or just `.venv/bin/python build.py` if the server is already running;
   the server serves `dist/` live, so a rebuild is picked up immediately).

## Interactive models (no .docx)

Entries with `"type": "model"` have no document. Instead they use `model_url` (the Grok Bot page, shown as
the primary "Open interactive model" button), `disclaimer` (shown on the card, banner and detail page),
`sign_in_note`, `description` (paragraphs), `explore` (bullets), optional static `tables`
(`title`, `columns`, `rows`, copied from the model's source data, never invented), `table_note`, and `sources`.
Any entry can list `related_projects` (slugs) to cross-link detail pages in both views.

## Views

- `/` classic view: cards, tag filter, search, sort, light/dark (`src/*.css|js`).
- `/v2/` minimal view following Paul's default web design system (the house style guide at
  `/home/box/style-guides/spacex-style-guide.canvas.tsx`): black canvas, #F0F0FA text, uppercase Barlow
  headings, full-width stacked report banners, 720px reading measure. Source: `v2.py` (HTML) and
  `src/v2/` (CSS, JS, bundled Barlow woff2 under the SIL OFL, see `src/v2/fonts/Barlow-OFL.txt`).
  v2 detail pages reuse the downloads in `dist/files/` and images in `dist/projects/<slug>/img/`.
- `shots.py <base-url>`: headless screenshots of v2 into `shots/` (Playwright + system Chrome).

## Hosting

- Local: `python3 -m http.server <port> --bind 127.0.0.1 --directory dist` (port stored in `.port`).
- Public: `tunnel-tools/tunnelto expose http://127.0.0.1:<port>` (tunnel.to anonymous quick tunnel,
  outbound HTTPS only, no account). The URL is random and changes whenever the tunnel restarts;
  anonymous tunnels are capped at 512 MiB of traffic. Cloudflare quick tunnels do not work on this
  machine because outbound port 7844 is blocked.
- Logs: `server.log`, `tunnelto.log`.

## GitHub Pages

The permanent public site is [https://pbouagno.github.io/research-archive/](https://pbouagno.github.io/research-archive/) (classic view) and [https://pbouagno.github.io/research-archive/v2/](https://pbouagno.github.io/research-archive/v2/) (minimal view).

`.github/workflows/pages.yml` deploys the prebuilt `dist/` directory to GitHub Pages on every push to `main`. The Pages source is GitHub Actions (`actions/configure-pages`, `actions/upload-pages-artifact`, `actions/deploy-pages`). `dist/.nojekyll` stops Jekyll from processing the upload; `build.py` writes that file back on every build because the build deletes `dist/` first. The upload step includes hidden files so `.nojekyll` is part of the artifact.

Internal links, stylesheets, scripts, images, downloads, and `projects.json` use paths relative to each page. The classic index inlines the catalog in the page (the same JSON is also written to `dist/projects.json`). Nothing points at the domain root, so both views and the detail pages work from the `/research-archive/` subpath.

### Update the published site

Rebuild on the machine that has the source documents. `build.py` reads them from `/workspace` and will not run in GitHub Actions, because those files are not in this repository. Then commit the new `dist/` and push to `main`:

```bash
.venv/bin/python build.py
git add dist
git commit -m "Update published archive"
git push origin main
```

The workflow publishes that `dist/` as-is.
