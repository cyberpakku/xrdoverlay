# xrdoverlay — execution plan

> Build a single-page HTML XRD comparison tool hosted on GitHub Pages. Standards loaded from a data-driven `manifest.json` so adding new compounds never touches HTML. PWA (offline + add-to-home-screen). Mobile + desktop responsive.

---

## Roles & UX targets

- **You (sole admin):** edit `manifest.json`, the `standards/` folder, and tag categories via the GitHub web UI. No admin affordances inside the app itself.
- **Students:** consume only. Open the URL, pick a standard, load their data, read the chart. Zero edit / upload-to-repo capability surfaced.
- **Mobile is the primary design target**, full feature parity. Desktop is a reflow of the same UI (controls in a side panel). Verify mobile first, then desktop.

## Paths

- **Plan source / reference (this document, twinned):**
  `/home/cyberpakku0x/Projects/xrdoverlay/PLAN.md` and `/home/cyberpakku0x/.claude/plans/make-the-best-plan-dynamic-widget.md`.
- **Actual app repo target (where the tool is built and pushed to GitHub from):**
  `/home/cyberpakku0x/Projects/xrdoverlay/` (sibling of `2perovski/`).

## v1 polish (from review)

The following polish items are part of v1 (not deferred):

- **A. Friendly error messages.** Parser failures, manifest fetch failures, and standard fetch failures display a clear human-readable line in the UI, never silently leave the chart blank.
- **B. Demo data button.** Ship `samples/demo.xy` (a small representative experimental scan). "Load demo data" button on first visit primes the chart end-to-end so the student sees how the tool works before uploading her own file.
- **C. Status feedback line.** After every operation: "Loaded 2670 points, 10-80°", "Background subtracted (degree 6, converged in 14 iterations)", "Shift applied: +0.12°". Reassuring and quietly educational.
- **D. Reset-to-defaults button.** One click clears shift, BG, axes, normalization back to defaults. Experimental data and selected standard are preserved.
- **Reset / clear cache button.** Tucked in a footer or settings drawer; when clicked, unregisters the Service Worker and clears `caches.*` so a stuck client can recover from any stale state. Confirms with a small "are you sure" then reloads the page.

## Deferred but tracked

- **K. Replace Plotly (~3 MB) with uPlot (~50 KB).** Only after observing real users on real devices. Chart code is isolated, so this is a contained swap (~100 lines) when/if mobile load times become a measurable problem.

---

## TASK LIST (execute in order)

### Phase A — Local build (I do all of this; you run no GitHub-side commands yet)

1. **Create local repo skeleton** at `/home/cyberpakku0x/Projects/xrdoverlay/` (sibling of `2perovski/`). Do NOT `git init` yet; the local folder stays a plain directory until Phase B.
2. **pymatgen** is installed in the `dft-tools` conda env (`pymatgen 2026.5.4`, alongside the existing `ase` and `spglib`). Scripts that touch pymatgen run with `~/miniforge3/envs/dft-tools/bin/python3`; everything else continues to use the `science` env.
3. **Write `service-worker.js`** (see §C) with initial `CACHE = 'xrdoverlay-v1'`.
4. **Write empty `manifest.json`**: `{ "standards": [] }`. It will be populated by `add_standard.py` in step 6.
5. **Write `scripts/add_standard.py`** (see §G for the full spec).
6. **Bootstrap the 4 standards** by running `add_standard.py` once per CIF:
   - `python scripts/add_standard.py --cif /home/cyberpakku0x/Projects/2perovski/XRD/standards/La2FeMnO6/ICSD_CollCode37296.cif --tags perovskite`
   - `python scripts/add_standard.py --cif /home/cyberpakku0x/Projects/2perovski/XRD/standards/La2NiMnO6/ICSD_CollCode49838.cif --tags perovskite`
   - `python scripts/add_standard.py --cif /home/cyberpakku0x/Projects/2perovski/XRD/standards/Y2NiMnO6/ICSD_CollCode258417.cif --tags perovskite`
   - `python scripts/add_standard.py --cif /home/cyberpakku0x/Projects/2perovski/XRD/standards/Gd2NiMnO6/ICSD_CollCode217340.cif --tags perovskite --label "Gd₂NiMnO₆"` (label override because CIF formula is `Gd1 Mn0.7 Ni0.3 O3`).
   - Each call writes one CSV, appends one manifest entry (with top 15 hkl-labeled peaks), and bumps the SW cache version.
7. **Validate computed patterns vs ICSD precomputed xy.** For each of the 4 standards, plot the freshly computed `xrdoverlay/standards/<compound>.csv` next to the ICSD `2perovski/XRD/standards/<compound>/powderpattern_xy_collCode#*.csv`. If peak positions match but peak shapes look noticeably different, tune the `--fwhm` default and re-bootstrap.
8. **Copy demo experimental scan** from `2perovski/XRD/samples/` into `xrdoverlay/samples/demo.xy` for the "Load demo data" button (v1 polish item B).
9. **Write `manifest.webmanifest`** (see §B).
10. **Download `plotly.min.js`** locally into the repo (bundle for offline-first). Latest stable from cdn.plot.ly.
11. **Generate `icons/icon-192.png` and `icons/icon-512.png`** — deterministic `XO` mark on accent-color background, rendered from SVG or HTML canvas via a one-shot Python/PIL script in `2perovski/coding/`. Do NOT use emoji / symbol glyphs.
12. **Write `index.html`** — see §D for structure; §E for JS modules to inline. Implementation must include all v1 polish items A–D and the reset-cache button.
13. **Write `README.md`** (see §F).
14. **Local smoke test**: `cd ~/Projects/xrdoverlay && python -m http.server 8000`, open `http://localhost:8000`, verify each item in the Verification section.

### Verification gate (mandatory)

**STOP at the end of Phase A.** Do not proceed to Phase B without explicit user sign-off.

User workflow at this gate:
1. I report what is built and what local URL to open.
2. User tests locally on desktop + mobile (Wi-Fi to laptop's IP for phone access).
3. If issues, user writes them into `xrdoverlay/corrections-vN.md` and tells me "read corrections-vN".
4. I read, give brief verdicts (table format like the v1 corrections review), apply approved corrections, re-run smoke test.
5. Loop steps 3-4 until user says "looks good, push it".

### Phase B — GitHub-side actions (user-driven; I provide step-by-step instructions)

15. **Create public GitHub repo `xrdoverlay`** (user does this in the browser at github.com; I provide the exact click path).
16. **Initialize local git, push initial commit** — I provide the exact terminal commands; user runs them.
17. **Enable Pages** (Settings → Pages → Source = main, root). I provide the exact click path.
18. **Mobile smoke test** on phone at `<user>.github.io/xrdoverlay/` over mobile data. Confirm Add-to-Home-Screen and end-to-end PWA install.

---

## Critical paths

| Repo file | Project source / reference |
|---|---|
| `xrdoverlay/standards/La2FeMnO6.csv` | `/home/cyberpakku0x/Projects/2perovski/XRD/standards/La2FeMnO6/powderpattern_xy_collCode#37296.csv` |
| `xrdoverlay/standards/La2NiMnO6.csv` | `/home/cyberpakku0x/Projects/2perovski/XRD/standards/La2NiMnO6/powderpattern_xy_collCode#49838.csv` |
| `xrdoverlay/standards/Y2NiMnO6.csv` | `/home/cyberpakku0x/Projects/2perovski/XRD/standards/Y2NiMnO6/powderpattern_xy_collCode#258417.csv` |
| `xrdoverlay/standards/Gd2NiMnO6.csv` | `/home/cyberpakku0x/Projects/2perovski/XRD/standards/Gd2NiMnO6/powderpattern_xy_collCode#217340.csv` |
| ModPoly reference (Python → port to JS) | `/home/cyberpakku0x/Projects/2perovski/coding/xrd_bgsub.py` |
| Delimiter sniff reference | `/home/cyberpakku0x/Projects/2perovski/coding/xrd_plot.py` |
| Project context | `/home/cyberpakku0x/Projects/2perovski/CLAUDE.md`, `2perovski/XRD/xrdnotes.md` |

---

## §A — `manifest.json` schema (populated by `add_standard.py`)

`manifest.json` is created by `add_standard.py`, not by hand. The HTML reads it on load and uses every field. Below is the schema each entry should contain, with an example entry showing all fields populated:

```json
{
  "standards": [
    {
      "compound": "La2NiMnO6",
      "file": "standards/La2NiMnO6.csv",
      "space_group": "P 1 21/n 1",
      "lattice_params": { "a": 5.5207, "b": 5.4755, "c": 7.8122,
                          "alpha": 90, "beta": 89.787, "gamma": 90 },
      "display_label": "La₂NiMnO₆",
      "tags": ["perovskite"],
      "wavelength": 1.5406,
      "peaks": [
        { "2theta": 32.48, "hkl": "112", "I": 100.0 },
        { "2theta": 32.51, "hkl": "020", "I":  98.8 },
        ... (top ~15 by intensity)
      ],
      "formula_cif": "La2 Ni1 Mn1 O6",
      "source": "ICSD 49838"
    }
  ]
}
```

Field meaning:
- `compound` (required): URL-safe key; also the filename stem in `standards/`.
- `file` (required): path to the xy CSV, relative to the repo root.
- `space_group` (required): Hermann–Mauguin symbol, as in the CIF.
- `lattice_params` (required): six lattice constants, uncertainty parens stripped.
- `display_label` (required): the pretty Unicode-subscripted name shown in the UI.
- `tags` (required, may be empty): for the tag-chip filter and grouping.
- `wavelength` (required): Å, the radiation used when computing the pattern.
- `peaks` (optional): top ~15 reflections with `(h k l)` and normalized intensity. Provided when `add_standard.py` computes the xy from a CIF; absent when `--xy PATH` overrides with a precomputed/measured pattern. The HTML uses this for hover-time `(h k l)` labels.
- `formula_cif` (optional): the raw CIF `_chemical_formula_sum`. Always carried when present so the app never silently misrepresents a disordered solid-solution (e.g. `Gd1 Mn0.7 Ni0.3 O3`) as an ordered double perovskite.
- `source` (optional): free-form provenance string (e.g. `"ICSD 49838"`).

The Gd v1 standard specifically: its CIF formula is `Gd1 Mn0.7 Ni0.3 O3` (disordered solid solution). The `display_label` is kept as `Gd₂NiMnO₆` for student familiarity, but `formula_cif` preserves the true composition.

---

## §B — `manifest.webmanifest`

```json
{
  "name": "XRD Overlay",
  "short_name": "xrdoverlay",
  "start_url": "./",
  "scope": "./",
  "display": "standalone",
  "orientation": "any",
  "theme_color": "#1F4E79",
  "background_color": "#ffffff",
  "icons": [
    { "src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable" },
    { "src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable" }
  ]
}
```

Reference in `index.html` via `<link rel="manifest" href="manifest.webmanifest">`.

---

## §C — `service-worker.js`

**Cache versioning rule (mandatory).** The `CACHE` constant MUST be incremented (e.g. `v1` → `v2`) on any change to any of the cached assets:

- `index.html`
- `manifest.json`
- `manifest.webmanifest`
- `plotly.min.js`
- `icons/*`
- `standards/*.csv`

Without a bump, deployed users keep being served the stale cache and never see the new content. This is also enforceable via a small build-time hash check in a follow-up; for v1 it is a manual discipline.

```js
const CACHE = 'xrdoverlay-v1';   // bump version on ANY change to assets listed above
const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './manifest.webmanifest',
  './plotly.min.js',
  './icons/icon-192.png',
  './icons/icon-512.png',
  // standards: read from manifest.json at install time
];

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await cache.addAll(ASSETS);
    // Then fetch manifest, cache each standard
    try {
      const m = await fetch('./manifest.json').then(r => r.json());
      const stdUrls = m.standards.map(s => './' + s.file);
      await cache.addAll(stdUrls);
    } catch (err) { /* manifest may be missing on very first install */ }
    self.skipWaiting();
  })());
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)));
    self.clients.claim();
  })());
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith((async () => {
    const cached = await caches.match(e.request);
    if (cached) {
      // Cache-first, revalidate in background
      fetch(e.request).then(resp => {
        if (resp.ok) caches.open(CACHE).then(c => c.put(e.request, resp));
      }).catch(() => {});
      return cached;
    }
    try {
      const resp = await fetch(e.request);
      if (resp.ok) {
        const c = await caches.open(CACHE);
        c.put(e.request, resp.clone());
      }
      return resp;
    } catch {
      return new Response('Offline and not cached', { status: 503 });
    }
  })());
});
```

Register in `index.html` at the end of `<body>`:
```html
<script>
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./service-worker.js');
  }
</script>
```

---

## §D — `index.html` skeleton

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>XRD Overlay</title>
  <link rel="manifest" href="manifest.webmanifest">
  <meta name="theme-color" content="#1F4E79">
  <link rel="apple-touch-icon" href="icons/icon-192.png">
  <style>
    /* CSS variables for theming */
    :root {
      --bg: #ffffff; --fg: #1a1a1a; --muted: #666; --panel: #f5f7fa;
      --accent: #1F4E79; --line-exp: #1F77B4; --line-std: #000000;
      --border: #d0d7de;
    }
    [data-theme="dark"] {
      --bg: #0f1419; --fg: #e6e6e6; --muted: #999; --panel: #1a1f2e;
      --accent: #4a9eff; --line-exp: #58a6ff; --line-std: #e6e6e6;
      --border: #30363d;
    }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
           background: var(--bg); color: var(--fg); }
    /* Mobile-first responsive grid */
    .app { display: grid; gap: 16px; padding: 16px; max-width: 1400px; margin: 0 auto; }
    @media (min-width: 700px) {
      .app { grid-template-columns: 320px 1fr; }
    }
    .panel { background: var(--panel); border: 1px solid var(--border);
             border-radius: 12px; padding: 16px; }
    .chart-wrap { background: var(--panel); border: 1px solid var(--border);
                  border-radius: 12px; padding: 8px; min-height: 400px; }
    .row { display: flex; align-items: center; gap: 8px; margin: 8px 0; }
    .row label { flex: 0 0 auto; min-width: 90px; color: var(--muted); font-size: 0.9em; }
    input[type="range"] { flex: 1; }
    input[type="number"] { width: 80px; }
    button { background: var(--accent); color: white; border: none;
             padding: 10px 16px; border-radius: 8px; cursor: pointer; font-size: 0.95em; }
    button:hover { filter: brightness(1.1); }
    .chip { display: inline-block; padding: 4px 10px; margin: 2px;
            background: var(--bg); border: 1px solid var(--border);
            border-radius: 999px; font-size: 0.85em; cursor: pointer; }
    .chip.active { background: var(--accent); color: white; }
    .drop-zone { border: 2px dashed var(--border); border-radius: 8px;
                 padding: 20px; text-align: center; color: var(--muted); }
    .drop-zone.over { border-color: var(--accent); background: rgba(31,78,121,0.05); }
    summary { cursor: pointer; padding: 8px 0; font-weight: 500; }
    .info { font-size: 0.85em; color: var(--muted); }
  </style>
</head>
<body>
  <div class="app">

    <aside class="panel">
      <h2 style="margin: 0 0 12px">XRD Overlay</h2>

      <!-- Standard selection -->
      <input type="search" id="search" placeholder="Search compound..." style="width: 100%; padding: 8px; margin-bottom: 8px;">
      <div id="tag-chips"></div>
      <select id="std-select" size="6" style="width: 100%; margin: 8px 0;"></select>
      <div id="std-info" class="info"></div>

      <!-- Experimental input -->
      <div class="drop-zone" id="drop">
        Drop your XRD file here
        <br><br>
        <button id="file-btn">or pick file</button>
        <input type="file" id="file-input" style="display:none" accept=".ASC,.asc,.txt,.xy,.csv,.dat">
      </div>
      <div id="exp-info" class="info"></div>

      <!-- Core controls -->
      <div class="row">
        <label>2θ shift</label>
        <input type="range" id="shift" min="-0.5" max="0.5" step="0.01" value="0">
        <input type="number" id="shift-num" min="-0.5" max="0.5" step="0.01" value="0">
      </div>

      <details>
        <summary>Background subtraction</summary>
        <div class="row">
          <label>Enable</label>
          <input type="checkbox" id="bg-on">
        </div>
        <div class="row">
          <label>Degree</label>
          <input type="range" id="bg-deg" min="4" max="10" step="1" value="6">
          <span id="bg-deg-val">6</span>
        </div>
      </details>

      <details>
        <summary>Axes</summary>
        <div class="row">
          <label>Y scale</label>
          <select id="y-scale"><option value="linear">linear</option><option value="log">log</option></select>
        </div>
        <div class="row">
          <label>X min</label>
          <input type="number" id="xmin" value="10" step="1">
          <label>X max</label>
          <input type="number" id="xmax" value="70" step="1">
        </div>
        <div class="row">
          <button data-preset="10-30">10-30</button>
          <button data-preset="10-70">10-70</button>
          <button data-preset="full">full</button>
        </div>
      </details>

      <div class="row" style="margin-top: 16px">
        <button id="save-png">Save PNG</button>
        <button id="theme-toggle">🌙</button>
      </div>
    </aside>

    <main class="chart-wrap">
      <div id="chart" style="width: 100%; height: 600px;"></div>
    </main>

  </div>

  <script src="plotly.min.js"></script>
  <script>
    // §E — application logic goes here (see plan §E)
  </script>
  <script>
    if ('serviceWorker' in navigator) navigator.serviceWorker.register('./service-worker.js');
  </script>
</body>
</html>
```

---

## §E — JS application logic (inline in `index.html`)

### State

```js
const state = {
  standards: [],          // manifest entries
  selected: null,         // current standard compound
  stdData: null,          // {x: [], y: []} loaded for the selected std
  expRaw: null,           // {x: [], y: []} as parsed from file
  shift: 0,
  bgOn: false,
  bgDeg: 6,
  yScale: 'linear',
  xmin: 10, xmax: 70,
  tagsActive: new Set(),
  searchQuery: '',
  theme: matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light',
};
```

### Manifest + standard loading

```js
async function loadManifest() {
  const r = await fetch('./manifest.json');
  state.standards = (await r.json()).standards;
}
async function loadStandard(entry) {
  const r = await fetch('./' + entry.file);
  const txt = await r.text();
  return parseXRD(txt);   // returns {x:[], y:[]}
}
```

### File-format auto-detection (port from `xrd_plot.py`)

Handles all input formats observed in the project:
- Comma-delimited 2-column TXT (lab `.txt`, ICSD xy `.csv`)
- Whitespace-delimited 3-column ASC (Rigaku, third column = sigma, ignored)
- Whitespace-delimited 2-column XY
- Tab-delimited 7-column ICSD table (only if ICSD-table header detected)
- Blank lines, comment lines (`#` or `!`), stray header lines

The parser splits on any of `,`, `\t`, or whitespace, then takes the first two numeric columns from each data line — except for ICSD-table-header lines, where it explicitly uses columns 4 (2θ) and 7 (intensity).

```js
function parseXRD(text) {
  const raw = text.split(/\r?\n/).map(l => l.trim());
  // Drop blank lines and comments
  const lines = raw.filter(l => l && !l.startsWith('#') && !l.startsWith('!'));
  if (!lines.length) return { x: [], y: [] };

  // ICSD table header detection: "H K L 2THETA D-VALUE MULT INTENSITY"
  const first = lines[0].toLowerCase();
  let startIdx = 0, isICSDtable = false;
  if (first.includes('2theta') && first.includes('h') && first.includes('k')) {
    startIdx = 1;
    isICSDtable = true;
  }

  const x = [], y = [];
  const splitter = /[,\t\s]+/;
  for (let i = startIdx; i < lines.length; i++) {
    const parts = lines[i].split(splitter).filter(Boolean);
    if (parts.length < 2) continue;
    let xv, yv;
    if (isICSDtable) {
      xv = parseFloat(parts[3]);   // 2THETA (col 4, 0-indexed = 3)
      yv = parseFloat(parts[6]);   // INTENSITY (col 7, 0-indexed = 6)
    } else {
      xv = parseFloat(parts[0]);
      yv = parseFloat(parts[1]);
    }
    if (Number.isFinite(xv) && Number.isFinite(yv)) {
      x.push(xv);
      y.push(yv);
    }
  }
  return { x, y };
}
```

### ModPoly background subtraction (port from `xrd_bgsub.py`)

```js
function modpolySubtract(x, y, degree = 6, maxIter = 100, tol = 1e-4) {
  const n = x.length;
  if (!n) return y.slice();
  // Normalize x to [-1, 1]
  const xMin = Math.min(...x), xMax = Math.max(...x);
  const xN = x.map(v => 2 * (v - xMin) / (xMax - xMin) - 1);
  const span = Math.max(...y) - Math.min(...y);

  let yCur = y.slice();
  let coeffs = polyfit(xN, yCur, degree);
  for (let it = 0; it < maxIter; it++) {
    const yFit = xN.map(v => polyval(coeffs, v));
    const yNew = yCur.map((yi, i) => Math.min(yi, yFit[i]));
    const maxDiff = Math.max(...yNew.map((v, i) => Math.abs(v - yCur[i])));
    yCur = yNew;
    coeffs = polyfit(xN, yCur, degree);
    if (maxDiff < tol * span) break;
  }
  const baseline = xN.map(v => polyval(coeffs, v));
  return y.map((yi, i) => Math.max(0, yi - baseline[i]));
}

// polyfit via normal equations (Vandermonde + linear solve)
function polyfit(x, y, deg) {
  const m = deg + 1, n = x.length;
  const A = Array.from({ length: n }, () => new Array(m));
  for (let i = 0; i < n; i++) {
    A[i][0] = 1;
    for (let j = 1; j < m; j++) A[i][j] = A[i][j-1] * x[i];
  }
  // Solve A^T A coeffs = A^T y
  const AtA = Array.from({ length: m }, () => new Array(m).fill(0));
  const Aty = new Array(m).fill(0);
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < m; j++) {
      for (let k = 0; k <= j; k++) AtA[j][k] += A[i][j] * A[i][k];
      Aty[j] += A[i][j] * y[i];
    }
  }
  for (let j = 0; j < m; j++) for (let k = j+1; k < m; k++) AtA[j][k] = AtA[k][j];
  return gaussianSolve(AtA, Aty);
}
function polyval(c, x) { let s = c[c.length-1]; for (let i = c.length-2; i >= 0; i--) s = s*x + c[i]; return s; }
function gaussianSolve(A, b) {
  const n = b.length;
  const M = A.map((r, i) => [...r, b[i]]);
  for (let i = 0; i < n; i++) {
    let piv = i;
    for (let k = i+1; k < n; k++) if (Math.abs(M[k][i]) > Math.abs(M[piv][i])) piv = k;
    [M[i], M[piv]] = [M[piv], M[i]];
    for (let k = i+1; k < n; k++) {
      const f = M[k][i] / M[i][i];
      for (let j = i; j <= n; j++) M[k][j] -= f * M[i][j];
    }
  }
  const x = new Array(n);
  for (let i = n-1; i >= 0; i--) {
    let s = M[i][n];
    for (let j = i+1; j < n; j++) s -= M[i][j] * x[j];
    x[i] = s / M[i][i];
  }
  return x;
}
```

### Normalization (over visible 2θ range)

```js
function normalizeInRange(x, y, xmin, xmax) {
  let max = 0;
  for (let i = 0; i < x.length; i++) if (x[i] >= xmin && x[i] <= xmax && y[i] > max) max = y[i];
  if (max === 0) return y.slice();
  return y.map(v => v / max * 100);
}
```

### d-spacing helper (Cu Kα 1.5406 Å) for hover

```js
const LAMBDA_CU_KA = 1.5406;
function dSpacing(twoTheta) { return LAMBDA_CU_KA / (2 * Math.sin(twoTheta * Math.PI / 360)); }
```

### Plotly render

**Two intentional behaviors to be aware of:**

1. **Normalization is computed over the visible x-range** with the *shifted* experimental x-values. This means changing the 2θ shift can slightly change the normalization scaling when peaks move into or out of the selected x-window. This is acceptable for visual alignment, but it is intentional, not a bug. The standard is normalized over the same window for an apples-to-apples comparison.
2. **Log-scale rendering masks zero/negative y values.** Standard CSVs contain many zero-intensity rows; Plotly's log axis can hide or mishandle them. Before rendering on log scale, the per-trace y array is mapped so that any value `≤ 0` becomes `null`. This is done only on the plotted trace data; the parsed source arrays are never mutated.

```js
function render() {
  const traces = [];
  if (state.expRaw) {
    let { x, y } = state.expRaw;
    x = x.map(v => v + state.shift);
    if (state.bgOn) y = modpolySubtract(x, y, state.bgDeg);
    let yN = normalizeInRange(x, y, state.xmin, state.xmax);
    if (state.yScale === 'log') yN = yN.map(v => v > 0 ? v : null);
    traces.push({
      x, y: yN, mode: 'lines', type: 'scattergl', name: 'Experimental',
      line: { color: cssVar('--line-exp'), width: 1.5 },
      hovertemplate: '2θ %{x:.3f}°<br>I %{y:.1f}<br>d %{customdata:.3f} Å<extra></extra>',
      customdata: x.map(dSpacing),
    });
  }
  if (state.stdData) {
    const { x, y } = state.stdData;
    let yN = normalizeInRange(x, y, state.xmin, state.xmax);
    if (state.yScale === 'log') yN = yN.map(v => v > 0 ? v : null);
    traces.push({
      x, y: yN, mode: 'lines', type: 'scattergl', name: state.selected,
      line: { color: cssVar('--line-std'), width: 1.5 },
      hovertemplate: '2θ %{x:.3f}°<br>I %{y:.1f}<br>d %{customdata:.3f} Å<extra></extra>',
      customdata: x.map(dSpacing),
    });
  }
  Plotly.react('chart', traces, {
    margin: { l: 60, r: 20, t: 30, b: 50 },
    xaxis: { title: '2θ (degrees)', range: [state.xmin, state.xmax],
             color: cssVar('--fg'), gridcolor: cssVar('--border') },
    yaxis: { title: 'Intensity (normalized)', type: state.yScale, autorange: true,
             color: cssVar('--fg'), gridcolor: cssVar('--border') },
    paper_bgcolor: cssVar('--panel'),
    plot_bgcolor: cssVar('--panel'),
    font: { color: cssVar('--fg') },
    legend: { x: 0.99, y: 0.99, xanchor: 'right' },
  }, { responsive: true, displaylogo: false });
}
function cssVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
```

### Wiring (drag-drop, file pick, controls, theme, presets)

Standard event-handler wiring — bind:
- `#file-input change` and `#file-btn click` → file picker → parseXRD → state.expRaw → render
- `#drop dragover/drop` events with `.over` class toggle → same parse pipeline
- `#std-select change` → loadStandard → state.stdData → render
- `#shift` + `#shift-num` two-way bind → state.shift → render
- `#bg-on`, `#bg-deg` → state.bgOn / bgDeg → render
- `#y-scale` → state.yScale → render
- `#xmin`, `#xmax`, `[data-preset]` → state.xmin/xmax → render
- `#save-png` → `Plotly.downloadImage('chart', {format:'png', filename:'xrd-overlay'})`
- `#theme-toggle` → toggle `data-theme` attr on `<html>` → re-render
- `#search` → filter visible options in `#std-select`
- Tag chips → toggle `state.tagsActive` → filter `#std-select`

---

## §F — `README.md`

```markdown
# xrdoverlay

Single-page XRD comparison tool. Overlays an experimental powder pattern against
ICSD reference standards. Mobile + desktop friendly. Works offline after first load.

Live: https://<user>.github.io/xrdoverlay/

## Add a new standard

1. Drop your standard's xy CSV (2 columns: 2theta, intensity, comma-delimited)
   into `standards/<Compound>.csv`. Use a plain ASCII filename.
2. Edit `manifest.json` and append a new object to the `standards` array:

   ```json
   {
     "compound": "Sr2NiMnO6",
     "file": "standards/Sr2NiMnO6.csv",
     "space_group": "Pm-3m",
     "lattice_params": { "a": 3.85, "b": 3.85, "c": 3.85,
                         "alpha": 90, "beta": 90, "gamma": 90 },
     "display_label": "Sr₂NiMnO₆",
     "tags": ["perovskite"]
   }
   ```

3. Commit. Reload the tool to see the new compound in the dropdown.

## Deploy

Settings → Pages → Source: main branch, root folder. Done.
```

---

## §G — `scripts/add_standard.py` (automation subroutine)

Adds a new standard to the tool from a CIF (and optionally a precomputed xy CSV) in one command, without any manual editing of `manifest.json`.

**Default behavior: compute the xy pattern from the CIF via pymatgen.** The `--xy` flag becomes the override for the rare case where you already have a measured or third-party precomputed pattern you'd rather use.

**CLI:**

```
python scripts/add_standard.py --cif PATH \
    [--xy PATH] \
    [--wavelength 1.5406] [--two-theta 5,90] [--step 0.02] [--fwhm 0.05] \
    [--tags TAG ...] [--label LABEL] \
    [--dry-run]
```

**Pipeline:**

1. Parse the CIF with pymatgen `Structure.from_file(...)`. Also pull, via a thin regex layer over the raw CIF text:
   - `_chemical_formula_sum` → `formula_cif`
   - `_symmetry_space_group_name_H-M` (or `_space_group_name_H-M_alt`) → `space_group`
   - `_cell_length_{a,b,c}` and `_cell_angle_{alpha,beta,gamma}` → `lattice_params`. **Strip uncertainty notation** (`5.5207(3)` → `5.5207`).
2. Derive the `compound` key from the formula, stripping spaces and adjusting integer subscripts (e.g. `Gd1 Mn0.7 Ni0.3 O3` → fall back to `--label` or CLI-prompted name when the formula isn't a clean stoichiometric tag).
3. Derive `display_label` from the compound name by Unicode-subscripting trailing digits (`La2NiMnO6` → `La₂NiMnO₆`). `--label` overrides.
4. **Generate the xy pattern (default path):**
   - Use `pymatgen.analysis.diffraction.xrd.XRDCalculator(wavelength=<arg>)`.
   - `calc.get_pattern(structure, two_theta_range=(min, max))` → peak list `(2θ, I, hkl)`.
   - Convolve to a continuous pattern over `arange(min, max+step, step)` using a Gaussian with the requested FWHM:
     - `sigma = fwhm / 2.355`
     - `intensity(2θ) = Σ_i I_i * exp(-((2θ - 2θ_i)² / (2 σ²)))`
   - Normalize so the in-range max = 100.
   - Write to `standards/<compound>.csv` as 2-column comma-separated `2theta,intensity`.
   - Also capture the **top ~15 peaks** by intensity into a `peaks: [{2theta, hkl, I}]` array for the manifest entry — enables hover-time `(h k l)` labels in the UI (originally suggestion F).
5. **Override path (`--xy PATH`):** validate the provided xy is 2-column comma-separated, no header. Copy it verbatim to `standards/<compound>.csv`. In this path, no `peaks` array is generated (we don't have the hkl info without the CIF computation).
6. Append a new entry to `manifest.json`. Schema (one optional field added vs base schema: `wavelength`, and the new optional `peaks` array):
   ```json
   {
     "compound": "...", "file": "standards/<compound>.csv",
     "space_group": "...", "lattice_params": { ... },
     "display_label": "...", "tags": [...],
     "wavelength": 1.5406,
     "peaks": [{ "2theta": 32.48, "hkl": "112", "I": 100 }, ...],
     "formula_cif": "...",  "source": "..."
   }
   ```
7. If a manifest entry for this `compound` already exists: **overwrite the entry and the CSV; print a clear WARNING line.** Do not silently overwrite. Do not error out.
8. Bump the `CACHE` constant in `service-worker.js` automatically (parse the trailing integer in `xrdoverlay-vN` and increment).
9. Print a summary block (and stop):
   - What was written / overwritten.
   - The new manifest entry as JSON.
   - The new `CACHE` value.
   - **The exact `git add ... && git commit ... && git push` line for the user to copy.** Do NOT execute it.

**`--dry-run` flag:** runs the entire pipeline but writes nothing. Prints what would change. Useful for sanity-checking a new CIF before committing.

**Example tail of the script's output:**

```
Standard "Sr2NiMnO6" added (computed from CIF).
  standards/Sr2NiMnO6.csv   (written, was new; 4250 points, 5-90° at step 0.02°)
  manifest.json             (appended 1 entry; wavelength 1.5406 Å, FWHM 0.05°)
                            (+ top 15 peaks with hkl)
  service-worker.js         (CACHE: xrdoverlay-v3 -> xrdoverlay-v4)

To deploy, run:
    cd /home/cyberpakku0x/Projects/xrdoverlay && \
    git add standards/Sr2NiMnO6.csv manifest.json service-worker.js && \
    git commit -m "Add Sr2NiMnO6 standard (computed from CIF, Cu Kα)" && \
    git push
```

**Hard rules:**
- Never auto-commit, never auto-push. The script only writes files.
- Overwrite + WARN on existing compound; never silently replace.
- For CIFs that don't follow ICSD shape (missing the metadata fields above), error out cleanly with the missing field name. Don't try to handle every CIF dialect.
- pymatgen must be available in the active Python environment (`conda install -c conda-forge pymatgen` if not present). Document in `README.md`.

**Bootstrap for v1's four standards:** during initial repo creation, run `add_standard.py --cif ...` for each of the 4 ICSD CIFs in `2perovski/XRD/standards/<compound>/`. The script computes the xy patterns fresh. As part of the verification gate, visually compare each computed pattern against the corresponding ICSD `powderpattern_xy_collCode#*.csv` — if appearance differs noticeably (peak shape mismatch from FWHM choice), tune `--fwhm` until visually consistent.

---

## Verification (local + remote)

Local (`python -m http.server 8000` in `xrdoverlay/`):

1. Dropdown lists 4 standards with subscript labels (La₂NiMnO₆, etc.).
2. "perovskite" tag chip filters (all visible, no-op).
3. Load `/home/cyberpakku0x/Projects/2perovski/XRD/samples/166-3094.ASC` → blue experimental line appears.
4. Load `/home/cyberpakku0x/Projects/2perovski/XRD/samples/La2NiMnO6_LOT1_calc1.txt` → ditto.
5. Load `/home/cyberpakku0x/Projects/2perovski/XRD/samples/La2FeMnO6_LOT1_ann1.xy` → ditto.
6. 2θ shift slider visibly aligns peaks; numeric input accepts 0.01° precision.
7. BG enabled flattens baseline; degree slider 4→10 visibly changes fit smoothness.
8. Y log toggle reveals small peaks; X-axis presets switch ranges; sliders smooth.
9. Save PNG downloads a file.
10. Theme toggle works; auto mode follows OS.
11. Stop server, reload — SW still serves the app (offline check).
12. DevTools → Application → Manifest shows installable; "Add to Home Screen" available.
13. Real-data check: select La₂NiMnO₆, load `La2NiMnO6_LOT1_calc1_0049.txt`, confirm main peak at ~32.5° aligns with black line and the ~31.5° La2NiO4 residual is visible in the experimental.

Remote (after push + Pages enable, ~1 min build wait):

14. Open `<user>.github.io/xrdoverlay/` on phone over mobile data. Repeat 1, 3, 6, 7, 9, 12.

---

## Deferred to v2 (do NOT implement now)

- Empirical ModPoly vs exponential BG comparison.
- Peak-list (ICSD `_table_` CSV) ingestion (skipped per user).
- Multiple simultaneous experimental files.
- Multiple simultaneous standards overlay.
- Residual plot below main chart.
- Savitzky-Golay smoothing.
- Contaminant overlays / vertical 2θ markers (explicitly removed per user).
- URL hash state persistence for sharing views.
- Auto cache-bump on `manifest.json` change (currently manual SW version bump).
