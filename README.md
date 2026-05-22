# xrdoverlay

Single-page tool for overlaying an experimental powder XRD pattern against
a small library of reference standards. Mobile- and desktop-friendly.
Works offline after first load (PWA).

**Live:** _will be `https://<user>.github.io/xrdoverlay/` once GitHub Pages is enabled_

---

## For the student (using the app)

1. Open the URL on your phone or laptop.
2. Pick a reference standard from the dropdown.
3. Click **Choose file** or drag your XRD scan onto the drop zone.
   - Supported formats: `.ASC`, `.txt`, `.xy`, `.csv` (auto-detects delimiter and skips the Rigaku error column), and `.rasx` (Rigaku SmartLab archive — unpacked in the browser; no other app needed).
   - Or click **Load demo** to see the tool work with a sample experimental file.
4. Compare. Use the **2θ shift** slider to align peaks if your sample is uniformly offset.
5. Optional: enable **Background subtraction**, switch **Y scale** to log, zoom into a 2θ range, or save a PNG.

On a phone, you can **Add to Home Screen** to install it as an app — it then works fully offline.

---

## For the admin (adding a new standard)

The `add_standard.py` script does everything: parses a CIF, computes the powder pattern, writes the CSV, appends to `manifest.json`, and bumps the service-worker cache version.

```bash
~/miniforge3/envs/dft-tools/bin/python3 scripts/add_standard.py \
    --cif /path/to/foo.cif \
    --tags perovskite \
    --source "ICSD <id>"
```

Or, to use a precomputed / measured xy pattern instead of computing from CIF:

```bash
~/miniforge3/envs/dft-tools/bin/python3 scripts/add_standard.py \
    --cif foo.cif --xy foo_measured.csv --tags perovskite
```

Options worth knowing:

- `--compound NAME`      override the auto-derived compound key.
- `--label LABEL`        override the auto-derived Unicode-subscripted display label (e.g. `"La₂NiMnO₆"`).
- `--wavelength 1.5406`  X-ray wavelength in Å (default: Cu Kα1). Use 1.5418 for the doublet-weighted average.
- `--two-theta 5,90`     computed 2θ range.
- `--step 0.02`          grid step.
- `--fwhm 0.05`          Gaussian peak FWHM.
- `--dry-run`            print what would change, write nothing.

After the script finishes, it prints the exact `git add ... && git commit ... && git push` line — copy and run it to deploy.

### From a browser (no terminal)

For tiny edits to an existing entry (typo, tag change), edit `manifest.json` directly in the GitHub web UI and commit. **Bump the `CACHE` constant in `service-worker.js`** in the same commit so users actually receive the change.

---

## Repository layout

```
xrdoverlay/
├── index.html              # the app
├── manifest.json           # standards registry (populated by add_standard.py)
├── manifest.webmanifest    # PWA app manifest
├── service-worker.js       # offline cache
├── plotly.min.js           # bundled charting library
├── standards/
│   └── <Compound>.csv      # 2θ, intensity per standard
├── samples/
│   └── demo.xy             # bundled demo experimental scan
├── icons/
│   ├── icon-192.png
│   └── icon-512.png
└── scripts/
    └── add_standard.py     # CIF → xy + manifest update
```

---

## Privacy

Everything runs client-side in your browser. No data is sent to any server.
The standards are loaded from this GitHub Pages site; your experimental
files never leave your device.

---

## Notes

- Cu Kα radiation is assumed throughout (d-spacing hover, default wavelength). If you measure with a different source, peak positions in the computed standards will not match your data and you'll need to add a separate standard at the right wavelength.
- The synthetic standards use a single Gaussian peak profile with constant FWHM 0.05°. This is adequate for visual contaminant ID but not for Rietveld-quality work.
- ModPoly background subtraction is the same algorithm used in the project's `coding/xrd_bgsub.py`.

---

## Dependencies

- **Browser:** any modern Chromium, Firefox, or Safari (mobile or desktop).
- **`add_standard.py`:** Python 3.10+ with `pymatgen` and `numpy`. Use the `dft-tools` conda env where pymatgen is installed.
