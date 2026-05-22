#!/usr/bin/env python3
"""
add_standard.py — register a new reference standard in xrdoverlay.

Defaults: compute the powder XRD pattern from a CIF via pymatgen +
Gaussian convolution. Override with --xy PATH to drop in a precomputed
or measured pattern instead.

Examples:

    # Default: compute pattern from CIF
    python scripts/add_standard.py \\
        --cif ../2perovski/XRD/standards/La2NiMnO6/ICSD_CollCode49838.cif \\
        --tags perovskite

    # Override with a precomputed xy CSV (no --compute-xy bookkeeping)
    python scripts/add_standard.py \\
        --cif foo.cif --xy foo_measured.csv --tags perovskite

    # Dry run
    python scripts/add_standard.py --cif foo.cif --tags perovskite --dry-run

Requires: pymatgen (conda install -c conda-forge pymatgen).
Run with the env that has it, e.g.
    ~/miniforge3/envs/dft-tools/bin/python3 scripts/add_standard.py ...
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np


# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
STANDARDS_DIR = REPO_ROOT / "standards"
MANIFEST = REPO_ROOT / "manifest.json"
SERVICE_WORKER = REPO_ROOT / "service-worker.js"

SUBSCRIPT = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


# ---------------------------------------------------------------------------
# CIF parsing (light regex layer for metadata fields not exposed cleanly
# by pymatgen). pymatgen does the heavy lifting for structure + XRD.
# ---------------------------------------------------------------------------

def strip_uncertainty(s: str) -> str:
    """Strip ICSD-style uncertainty parens: '5.5207(3)' -> '5.5207'."""
    return re.sub(r"\(\d+\)", "", s).strip()


def parse_cif_metadata(cif_path: Path) -> dict:
    """Pull formula, space group, lattice params from raw CIF text.

    Returns a dict with keys: formula_cif, space_group, lattice_params.
    Raises KeyError with the missing field if a required tag isn't found.
    """
    text = cif_path.read_text(encoding="utf-8", errors="replace")
    md: dict = {}

    # Formula
    m = re.search(r"_chemical_formula_sum\s+['\"]?([^'\"\n]+)['\"]?", text)
    if m:
        md["formula_cif"] = m.group(1).strip()

    # Space group (try H-M, then alt forms)
    for tag in (
        r"_symmetry_space_group_name_H-M",
        r"_space_group_name_H-M_alt",
        r"_space_group.name_H-M_alt",
        r"_space_group_name_Hall",
    ):
        m = re.search(rf"{tag}\s+['\"]?([^'\"\n]+)['\"]?", text)
        if m:
            md["space_group"] = m.group(1).strip()
            break
    if "space_group" not in md:
        raise KeyError("space_group (_symmetry_space_group_name_H-M)")

    # Lattice params (a, b, c, alpha, beta, gamma)
    lat: dict = {}
    for key, tag in (
        ("a",     "_cell_length_a"),
        ("b",     "_cell_length_b"),
        ("c",     "_cell_length_c"),
        ("alpha", "_cell_angle_alpha"),
        ("beta",  "_cell_angle_beta"),
        ("gamma", "_cell_angle_gamma"),
    ):
        m = re.search(rf"{tag}\s+([\d.\-]+(?:\(\d+\))?)", text)
        if not m:
            raise KeyError(f"lattice_params.{key} ({tag})")
        lat[key] = float(strip_uncertainty(m.group(1)))
    md["lattice_params"] = lat

    if "formula_cif" not in md:
        md["formula_cif"] = ""   # optional, don't raise

    return md


# ---------------------------------------------------------------------------
# Compound key + display label derivation
# ---------------------------------------------------------------------------

def derive_compound_key(formula_cif: str, cif_path: Path) -> str:
    """Make a clean compound key from the CIF formula or filename.

    Strategy:
      1. If the CIF formula is a clean integer stoichiometric expression
         (e.g. 'La2 Ni1 Mn1 O6'), strip the spaces -> 'La2Ni1Mn1O6'.
         Drop trailing '1' subscripts when unambiguous -> 'La2NiMnO6'.
      2. Otherwise fall back to the CIF filename stem (e.g.
         'ICSD_CollCode49838' -> the user should supply --label).
    """
    if not formula_cif:
        return cif_path.stem
    # Reject if any element coefficient is non-integer
    tokens = formula_cif.split()
    out = []
    for tok in tokens:
        m = re.match(r"^([A-Z][a-z]?)([\d.]+)?$", tok)
        if not m:
            # Falls back to filename stem on weird formulae
            return cif_path.stem
        el, n = m.group(1), m.group(2)
        if n is None or n == "1":
            out.append(el)
        else:
            try:
                ni = float(n)
                if ni.is_integer():
                    out.append(f"{el}{int(ni)}")
                else:
                    # Non-integer coefficient -> ambiguous, defer to user
                    return cif_path.stem
            except ValueError:
                return cif_path.stem
    return "".join(out)


def derive_display_label(compound: str) -> str:
    """'La2NiMnO6' -> 'La₂NiMnO₆': subscript trailing digit runs."""
    return re.sub(
        r"(\d+)",
        lambda m: m.group(1).translate(SUBSCRIPT),
        compound,
    )


# ---------------------------------------------------------------------------
# Pattern computation (default) and validation (--xy override)
# ---------------------------------------------------------------------------

def compute_pattern(cif_path: Path, wavelength: float,
                    two_theta_range: tuple[float, float],
                    step: float, fwhm: float) -> tuple[np.ndarray, np.ndarray, list]:
    """Use pymatgen + Gaussian convolution to synthesize an xy pattern.

    Returns (two_theta_grid, intensity_grid, peaks_meta).
    peaks_meta is a list of dicts: [{2theta, hkl, I}, ...] for the top 15
    peaks by intensity (intensity normalized so max = 100 in-range).
    """
    from pymatgen.io.cif import CifParser
    from pymatgen.analysis.diffraction.xrd import XRDCalculator

    # `occupancy_tolerance` lets pymatgen accept ICSD CIFs with sites
    # whose summed occupancies slightly exceed 1.0 due to rounded
    # disorder values (common in our B-site Ni/Mn solid solutions:
    # 0.414 + 0.610 = 1.024). Default tolerance is 1.0 (strict).
    parser = CifParser(str(cif_path), occupancy_tolerance=1.5)
    structures = parser.parse_structures(primitive=False)
    if not structures:
        raise RuntimeError(f"pymatgen could not extract any structure from {cif_path}")
    structure = structures[0]
    calc = XRDCalculator(wavelength=wavelength)
    pat = calc.get_pattern(structure, two_theta_range=two_theta_range)

    # Continuous grid + Gaussian convolution
    tt_min, tt_max = two_theta_range
    grid = np.arange(tt_min, tt_max + step / 2, step)
    sigma = fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    intensity = np.zeros_like(grid)
    for tt_i, I_i in zip(pat.x, pat.y):
        intensity += I_i * np.exp(-((grid - tt_i) ** 2) / (2.0 * sigma ** 2))

    # Normalize so max = 100 in-range
    max_in = intensity.max()
    if max_in > 0:
        intensity = intensity / max_in * 100.0

    # Top 15 peaks with hkl
    order = np.argsort(pat.y)[::-1]
    top = order[:15]
    peaks_meta = []
    for idx in top:
        hkls = pat.hkls[idx]
        # pymatgen returns list of {hkl, multiplicity} dicts
        hkl_first = hkls[0]["hkl"] if hkls else (0, 0, 0)
        hkl_str = "".join(
            str(c) if c >= 0 else f"-{abs(c)}"
            for c in hkl_first
        )
        peaks_meta.append({
            "2theta": float(round(pat.x[idx], 4)),
            "hkl": hkl_str,
            "I": float(round(pat.y[idx], 2)),
        })
    return grid, intensity, peaks_meta


def validate_xy_csv(xy_path: Path) -> np.ndarray:
    """Verify a precomputed xy CSV is 2-col comma-separated numeric.

    Raises ValueError on failure with a clear message.
    Returns the data as an Nx2 array.
    """
    text = xy_path.read_text()
    rows = []
    for ln, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        if line.startswith(("#", "!")):
            continue
        if "," not in line:
            raise ValueError(
                f"{xy_path}: line {ln} is not comma-separated: {line!r}"
            )
        parts = line.split(",")
        if len(parts) < 2:
            raise ValueError(
                f"{xy_path}: line {ln} has fewer than 2 columns"
            )
        try:
            x, y = float(parts[0]), float(parts[1])
        except ValueError:
            raise ValueError(
                f"{xy_path}: line {ln} is not numeric: {line!r}"
            )
        rows.append((x, y))
    if not rows:
        raise ValueError(f"{xy_path}: no data rows")
    return np.array(rows)


# ---------------------------------------------------------------------------
# Manifest + service-worker manipulation
# ---------------------------------------------------------------------------

def load_manifest() -> dict:
    if not MANIFEST.exists():
        return {"standards": []}
    with MANIFEST.open() as f:
        return json.load(f)


def save_manifest(m: dict) -> None:
    with MANIFEST.open("w") as f:
        json.dump(m, f, indent=2, ensure_ascii=False)
        f.write("\n")


def upsert_entry(manifest: dict, entry: dict) -> str:
    """Insert or replace an entry by compound key. Returns 'inserted' or 'replaced'."""
    standards = manifest.setdefault("standards", [])
    for i, s in enumerate(standards):
        if s.get("compound") == entry["compound"]:
            standards[i] = entry
            return "replaced"
    standards.append(entry)
    return "inserted"


def bump_sw_cache_version() -> tuple[str, str]:
    """Bump the PATCH component of CACHE = 'xrdoverlay-vMAJOR.MINOR.PATCH'.

    Adding a standard is an asset-only change, so it never touches MAJOR or
    MINOR. Bump those by hand in service-worker.js when a real feature ships
    (MINOR) or a redesign happens (MAJOR). Also keep index.html's
    <span id="version"> in sync when MAJOR/MINOR change.
    """
    text = SERVICE_WORKER.read_text()
    m = re.search(
        r"const\s+CACHE\s*=\s*'(xrdoverlay-v(\d+)\.(\d+)\.(\d+))'", text
    )
    if not m:
        raise RuntimeError(
            f"Could not find a semver CACHE constant (xrdoverlay-vMAJOR.MINOR.PATCH) "
            f"in {SERVICE_WORKER}"
        )
    old_name, major, minor, patch = m.group(1), m.group(2), m.group(3), m.group(4)
    new_name = f"xrdoverlay-v{major}.{minor}.{int(patch) + 1}"
    new_text = text.replace(f"'{old_name}'", f"'{new_name}'", 1)
    SERVICE_WORKER.write_text(new_text)
    return old_name, new_name


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Register a new XRD standard (CIF -> xy pattern + manifest entry).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--cif", required=True, type=Path, help="path to the CIF file")
    p.add_argument("--xy", type=Path, default=None,
                   help="optional precomputed xy CSV; overrides CIF-based computation")
    p.add_argument("--label", default=None,
                   help="display label override (e.g. 'La₂NiMnO₆')")
    p.add_argument("--compound", default=None,
                   help="compound key override (default: derived from CIF formula)")
    p.add_argument("--tags", nargs="*", default=[], help="manifest tags")
    p.add_argument("--wavelength", type=float, default=1.5406,
                   help="X-ray wavelength in Å (Cu Kα default)")
    p.add_argument("--two-theta", default="5,90", metavar="MIN,MAX",
                   help="2θ range for the computed pattern")
    p.add_argument("--step", type=float, default=0.02,
                   help="2θ grid step in deg")
    p.add_argument("--fwhm", type=float, default=0.15,
                   help="Gaussian peak FWHM in deg")
    p.add_argument("--source", default=None,
                   help="provenance string (auto-inferred from "
                        "'ICSD_CollCode<n>.cif' filename if omitted)")
    p.add_argument("--dry-run", action="store_true",
                   help="print what would change but do not write files")
    args = p.parse_args(argv)

    # Validate inputs
    if not args.cif.exists():
        p.error(f"CIF not found: {args.cif}")
    if args.xy is not None and not args.xy.exists():
        p.error(f"xy CSV not found: {args.xy}")

    try:
        tt_min, tt_max = (float(s) for s in args.two_theta.split(","))
    except ValueError:
        p.error(f"--two-theta expects 'MIN,MAX', got {args.two_theta!r}")

    print(f"[info] CIF: {args.cif}")
    try:
        meta = parse_cif_metadata(args.cif)
    except KeyError as e:
        print(f"[error] missing required CIF field: {e.args[0]}", file=sys.stderr)
        return 2
    print(f"[info] space group: {meta['space_group']}")
    print(f"[info] lattice: {meta['lattice_params']}")
    if meta.get("formula_cif"):
        print(f"[info] formula_cif: {meta['formula_cif']}")

    # Compound key + label
    compound = args.compound or derive_compound_key(meta.get("formula_cif", ""), args.cif)
    display_label = args.label or derive_display_label(compound)
    print(f"[info] compound key: {compound}")
    print(f"[info] display label: {display_label}")

    # Compute (default) or take precomputed
    if args.xy is None:
        print(f"[info] computing pattern via pymatgen (λ={args.wavelength} Å, "
              f"2θ {tt_min}-{tt_max}, step {args.step}, FWHM {args.fwhm})")
        try:
            grid, intensity, peaks = compute_pattern(
                args.cif, args.wavelength, (tt_min, tt_max), args.step, args.fwhm)
        except ImportError:
            print("[error] pymatgen is not available in this Python environment.",
                  file=sys.stderr)
            print("        Try:  ~/miniforge3/envs/dft-tools/bin/python3 "
                  "scripts/add_standard.py ...", file=sys.stderr)
            return 3
        n_points = len(grid)
        print(f"[info] generated {n_points} points, top peak at "
              f"{peaks[0]['2theta']:.3f}° (hkl={peaks[0]['hkl']})")
    else:
        print(f"[info] using precomputed xy: {args.xy}")
        data = validate_xy_csv(args.xy)
        grid, intensity = data[:, 0], data[:, 1]
        peaks = []
        n_points = len(grid)

    # Build manifest entry
    entry = {
        "compound": compound,
        "file": f"standards/{compound}.csv",
        "space_group": meta["space_group"],
        "lattice_params": {
            "a":     round(meta["lattice_params"]["a"],     6),
            "b":     round(meta["lattice_params"]["b"],     6),
            "c":     round(meta["lattice_params"]["c"],     6),
            "alpha": round(meta["lattice_params"]["alpha"], 4),
            "beta":  round(meta["lattice_params"]["beta"],  4),
            "gamma": round(meta["lattice_params"]["gamma"], 4),
        },
        "display_label": display_label,
        "tags": list(args.tags),
        "wavelength": args.wavelength,
    }
    if peaks:
        entry["peaks"] = peaks
    if meta.get("formula_cif"):
        entry["formula_cif"] = meta["formula_cif"]

    # --source: explicit > auto-inferred from ICSD_CollCode<n>.cif
    source = args.source
    if source is None:
        m_icsd = re.search(r"ICSD_CollCode(\d+)", args.cif.name, flags=re.IGNORECASE)
        if m_icsd:
            source = f"ICSD {m_icsd.group(1)}"
    if source:
        entry["source"] = source

    # ----- Output -----
    target_csv = STANDARDS_DIR / f"{compound}.csv"
    target_csv_existed = target_csv.exists()
    manifest = load_manifest()
    manifest_action = "would-insert"
    for s in manifest.get("standards", []):
        if s.get("compound") == compound:
            manifest_action = "would-replace"
            break

    print()
    print("=" * 64)
    print(f"  Compound:        {compound}")
    print(f"  Display label:   {display_label}")
    print(f"  CSV target:      standards/{compound}.csv  "
          f"({'OVERWRITES existing' if target_csv_existed else 'new file'})")
    print(f"  Manifest action: {manifest_action.replace('would-', '')}")
    print(f"  Wavelength:      {args.wavelength} Å")
    print(f"  Tags:            {args.tags}")
    if peaks:
        print(f"  Top peaks:       {len(peaks)} (with hkl labels)")
    print("=" * 64)

    if args.dry_run:
        print("\n[dry-run] No files written.")
        return 0

    if target_csv_existed:
        print(f"[WARN] standards/{compound}.csv already exists — OVERWRITING.")
    if manifest_action == "would-replace":
        print(f"[WARN] manifest entry for {compound!r} already exists — REPLACING.")

    # Write the xy CSV — always strict 2-col, never copy extraneous columns.
    STANDARDS_DIR.mkdir(parents=True, exist_ok=True)
    with target_csv.open("w") as f:
        for x, y in zip(grid, intensity):
            f.write(f"{x:.5f},{y:.5f}\n")

    # Upsert manifest
    upsert_entry(manifest, entry)
    save_manifest(manifest)

    # Bump SW cache version
    sw_old, sw_new = bump_sw_cache_version()

    print(f"  standards/{compound}.csv   ({n_points} points written)")
    print(f"  manifest.json              ({manifest_action.replace('would-', '')})")
    print(f"  service-worker.js          (CACHE: {sw_old} -> {sw_new})")
    print()
    print("To deploy, run:")
    print(f"    cd {REPO_ROOT} && \\")
    print(f"    git add standards/{compound}.csv manifest.json service-worker.js && \\")
    print(f"    git commit -m \"Add {compound} standard\" && \\")
    print("    git push")
    return 0


if __name__ == "__main__":
    sys.exit(main())
