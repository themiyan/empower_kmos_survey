"""Add the LATIS (Newman+25) COSMOS layer to spec_z_analysis.ipynb.

Operates on the CURRENT notebook cell sources (targeted edits) so it preserves
any hand-edits already in the notebook. Idempotent. Re-execute the notebook
afterwards to refresh outputs.
"""
import json
import os

NB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spec_z_analysis.ipynb")


def code_cell(cid, src):
    return {"cell_type": "code", "execution_count": None, "id": cid,
            "metadata": {}, "outputs": [], "source": src.splitlines(keepends=True)}


LOAD_LATIS = '''

def load_latis():
    """LATIS DR1 (Newman et al. 2025, ApJS 281, 32) spec-z catalogue.

    Magellan/IMACS multi-slit, R~1000. Fields D1, D2 (= COSMOS), D4. Columns:
    name, field (b"D1"/b"D2"/b"D4"), RA, Dec, z, zqual (0-4; secure >= 3),
    isstar, isqso, badredux, rmag, u-g, g-r, comments.
    """
    return Table.read(_path("latis", "latis_zspec.fits"))
'''

COSMOS_LATIS = '''\
"""Cross-match LATIS (Newman+25) D2/COSMOS secure redshifts -> Khostovan.

LATIS (Magellan/IMACS multi-slit, R~1000) was built to map the z~2-3 IGM, so it
is dense exactly in the otherwise-sparse EMPOWER tier 3. Only the D2 field
overlaps COSMOS. We keep secure galaxy redshifts (zqual>=3, not flagged as star
or bad reduction) and ask which are new to Khostovan. The match radius is
LATIS-specific (ground-based multi-slit -> SPECZ_MATCH_RADII["LATIS"]).
"""
latis = load_latis()
lat_field = np.array([s.decode() if isinstance(s, (bytes, bytearray)) else str(s)
                      for s in np.asarray(latis["field"])])
lat_z = np.asarray(latis["z"], dtype=float)
lat_d2 = (np.char.startswith(lat_field, "D2")
          & (np.asarray(latis["zqual"]) >= 3) & (lat_z > 0)
          & (np.asarray(latis["isstar"]) == 0) & (np.asarray(latis["badredux"]) == 0))

r_lat  = match_radius("LATIS")
xm_lat = blind_xmatch(latis["RA"][lat_d2], latis["Dec"][lat_d2], ra, dec,
                      radius_arcsec=r_lat)
lat_kflag = flag[xm_lat.idx]
lat_new   = ~xm_lat.matched                              # no Khostovan within radius
lat_upg   = xm_lat.matched & ~np.isin(lat_kflag, [3, 4]) # matched but Khostovan flag<3
lat_zz    = lat_z[lat_d2]

print(f"LATIS D2/COSMOS secure galaxies : {lat_d2.sum():,}  (match radius = {r_lat}\\u2033)")
print(f"  NEW to Khostovan              : {lat_new.sum():,}")
print(f"  UPGRADE (Khostovan flag < 3)  : {lat_upg.sum():,}")
print()
print("Per-tier LATIS D2 secure (NEW / upgrade to Khostovan):")
for name in TIERS:
    intier = tier_mask(lat_zz, name)
    print(f"  {name:<14s} total={int(intier.sum()):>4}  "
          f"NEW={int((intier & lat_new).sum()):>4}  "
          f"upgrade={int((intier & lat_upg).sum()):>4}")
print()
print(xm_lat.note)
'''

FIG5 = '''\
"""Figure 5 — Final COSMOS per-tier inventory.

Per tier: secure (flag>=3) Khostovan sources [left axis] and the NEW-to-Khostovan
contributions [right axis] from DJA grade=3, DEVILS prob>=0.8, and LATIS D2
secure. LATIS dominates the otherwise-sparse tier 3. Add-on targets need a
COSMOS2020 mass crossmatch before entering the EMPOWER pool (follow-up notebook).
"""
fig, ax = plt.subplots(figsize=(9.8, 4.5))
names = list(TIERS.keys()) + ["KARMA IZ H\\u03b2+H\\u03b1"]

def _new_per(zarr, newmask):
    out = [(newmask & tier_mask(zarr, n)).sum() for n in TIERS]
    out.append((newmask & (zarr > KARMA_IZ_HB_HA[0])
                & (zarr < KARMA_IZ_HB_HA[1])).sum())
    return out

khostovan_in = [(is_secure & tier_mask(z, n)).sum() for n in TIERS]
khostovan_in.append((is_secure & (z > KARMA_IZ_HB_HA[0])
                     & (z < KARMA_IZ_HB_HA[1])).sum())
dja_new    = _new_per(np.asarray(dja_cos["z_best"]), secure_d & ~matched)
devils_new = _new_per(np.asarray(clean["DEVILS_z"]), m_sec & ~xm_dev.matched)
latis_new  = _new_per(lat_zz, lat_new)

xs = np.arange(len(names)); w = 0.2
ax2 = ax.twinx()
b0 = ax.bar(xs - 1.5*w, khostovan_in, w, color="#1f77b4",
            label="Khostovan flag\\u22653", alpha=0.85)
b1 = ax2.bar(xs - 0.5*w, dja_new,    w, color="#2ca02c",
             label="DJA grade=3 NEW", alpha=0.85)
b2 = ax2.bar(xs + 0.5*w, devils_new, w, color="#d62728",
             label="DEVILS prob\\u22650.8 NEW", alpha=0.85)
b3 = ax2.bar(xs + 1.5*w, latis_new,  w, color="#9467bd",
             label="LATIS D2 secure NEW", alpha=0.85)

for arr, off, axx in [(khostovan_in, -1.5*w, ax), (dja_new, -0.5*w, ax2),
                      (devils_new, 0.5*w, ax2), (latis_new, 1.5*w, ax2)]:
    for i, n in enumerate(arr):
        if n > 0:
            axx.text(xs[i] + off, n, f"{int(n):,}", ha="center",
                     va="bottom", fontsize=7)

ax.set_xticks(xs); ax.set_xticklabels(names)
ax.set_ylabel("N (Khostovan flag \\u2265 3)", color="#1f77b4")
ax2.set_ylabel("N NEW to Khostovan (add-ons)", color="0.20")
ax.tick_params(axis="y", colors="#1f77b4")
ax.set_title("COSMOS — spec-z budget per EMPOWER tier "
             "(baseline + add-on contributions)")
hs = [b0, b1, b2, b3]
ax.legend(hs, [h.get_label() for h in hs], loc="upper right", fontsize=8)
fig.tight_layout()
save_fig(fig, "fig05_cosmos_summary")
plt.show()
'''

GAP_MD = '''\
### 2.2 COSMOS — what is missing from Khostovan?

Three recent surveys cover material the Khostovan compilation does not yet
absorb:

* **DJA NIRSpec v4.4** (Brammer / Heintz) — re-reduced JWST NIRSpec MSA / IFU
  data, JADES-dominated. High-S/N grating redshifts for faint compact targets.
* **DEVILS DR1 D10** (Davies+25) — AAT/AAOmega Y < 21.2 survey covering the
  central \\u2248 1.5 deg\\u00b2 of COSMOS; mostly z < 1.
* **LATIS** (Newman+25) — Magellan/IMACS multi-slit IGM-tomography survey; its
  D2 field overlaps COSMOS and is dense at z \\u2248 2-3, i.e. exactly the
  sparse EMPOWER tier 3.

Each cross-match uses that survey's own radius from `SPECZ_MATCH_RADII` (see the
top-of-notebook caveat: these are blind positional matches, for counting gaps
not confirming identities).
'''


def main():
    with open(NB) as f:
        nb = json.load(f)
    by_id = {c.get("id"): c for c in nb["cells"]}
    done = []

    # 1. setup-constants: add LATIS radius (string insert after DEVILS line).
    c = by_id["setup-constants"]
    src = "".join(c["source"])
    if '"LATIS"' not in src:
        anchor = '    "DEVILS":    1.0,   # AAT/AAOmega 2" fibres, ground-based\n'
        ins = anchor + '    "LATIS":     0.75,  # Magellan/IMACS multi-slit, ground-based\n'
        assert anchor in src, "DEVILS anchor not found in setup-constants"
        src = src.replace(anchor, ins)
        c["source"] = src.splitlines(keepends=True)
        c["outputs"] = []; c["execution_count"] = None
        done.append("setup-constants")

    # 2. loaders-code: append load_latis().
    c = by_id["loaders-code"]
    src = "".join(c["source"])
    if "def load_latis(" not in src:
        src = src.rstrip("\n") + "\n" + LOAD_LATIS
        c["source"] = src.splitlines(keepends=True)
        c["outputs"] = []; c["execution_count"] = None
        done.append("loaders-code")

    # 3. cosmos-gap-md: refresh prose.
    by_id["cosmos-gap-md"]["source"] = GAP_MD.splitlines(keepends=True)
    done.append("cosmos-gap-md")

    # 4. cosmos-fig5-summary: replace with LATIS-aware version.
    c = by_id["cosmos-fig5-summary"]
    c["source"] = FIG5.splitlines(keepends=True)
    c["outputs"] = []; c["execution_count"] = None
    done.append("cosmos-fig5-summary")

    # 5. insert cosmos-latis cell after cosmos-devils (if absent).
    if "cosmos-latis" not in by_id:
        idx = next(i for i, cc in enumerate(nb["cells"])
                   if cc.get("id") == "cosmos-devils")
        nb["cells"].insert(idx + 1, code_cell("cosmos-latis", COSMOS_LATIS))
        done.append("cosmos-latis (inserted)")
    else:
        by_id["cosmos-latis"]["source"] = COSMOS_LATIS.splitlines(keepends=True)
        by_id["cosmos-latis"]["outputs"] = []
        by_id["cosmos-latis"]["execution_count"] = None
        done.append("cosmos-latis (updated)")

    with open(NB, "w") as f:
        json.dump(nb, f, indent=1)
    print("Applied:", done)


if __name__ == "__main__":
    main()
