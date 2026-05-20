"""Apply the DR4-layer + per-survey-radius edits to spec_z_analysis.ipynb.

Rewrites the source of named cells in place (outputs are cleared for the edited
cells; the notebook is re-executed afterwards). Idempotent: re-running just
re-sets the same sources.
"""
import json
import os

NB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spec_z_analysis.ipynb")

# ----------------------------------------------------------------------
# New cell sources, keyed by cell id.
# ----------------------------------------------------------------------
EDITS = {}

EDITS["setup-constants"] = '''\
"""EMPOWER survey constants.

TIERS, KARMA_IZ_HB_HA, KMOS_BANDS, LINES_AA, OH_FORESTS_UM
    Selection windows and instrumental constants. Tier centres are taken from the
    EMPOWER proposal; ``dz`` is a "search half-width" used only for inventory
    counts — it is wider than the KARMA per-target window because we want to
    see what surveys deliver near each tier.

COSMO
    FlatLambdaCDM(H0=70, Om0=0.30) — used only for comoving-distance plots.

FIELD_CENTRES
    (RA, Dec) in degrees adopted for sky views; ASTRODEEP/MUSE coverage is
    smaller than the COSMOS box, so a wider 1.5 deg half-side is used for
    COSMOS only.

SPECZ_MATCH_RADII / BASE_MATCH_RADIUS
    Per-survey positional cross-match tolerances — the central knob for tuning
    matches to each survey's astrometric accuracy (see below).
"""

COSMO = FlatLambdaCDM(H0=70.0, Om0=0.30)

TIERS = {
    "T1 (z~0.75)": dict(zc=0.75, dz=0.10, color="#1f77b4"),
    "T2 (z~1.6)":  dict(zc=1.60, dz=0.20, color="#2ca02c"),
    "T3 (z~2.3)":  dict(zc=2.30, dz=0.20, color="#d62728"),
}

KARMA_IZ_HB_HA = (0.60, 0.6325)

KMOS_BANDS = {
    "IZ":  (0.78, 1.08),
    "YJ":  (1.025, 1.345),
    "H":   (1.460, 1.850),
    "HK":  (1.480, 2.450),
    "K":   (1.950, 2.450),
}

LINES_AA = {
    "H$\\\\beta$":     4861.33,
    "[OIII]5007":      5006.84,
    "H$\\\\alpha$":    6562.80,
    "[NII]6584":       6583.45,
}

# Approximate OH-forest envelopes (microns).  Used for visual context; for
# per-target sky-line filtering use a real OH sky spectrum.
OH_FORESTS_UM = [
    (0.86, 0.88), (0.92, 0.94), (1.08, 1.12), (1.18, 1.22),
    (1.27, 1.32), (1.42, 1.50), (1.55, 1.63), (1.73, 1.78),
    (1.83, 1.92),
]

FIELD_CENTRES = {
    "COSMOS":  dict(ra=150.116321, dec=+2.20583, half_deg=1.50),
    "GOODS-S": dict(ra= 53.123,    dec=-27.81,   half_deg=0.45),
}

# === Cross-match radii (arcsec), tunable PER SURVEY =========================
# The positional tolerance for calling two catalogue entries "the same source".
# Set per survey so it tracks each survey's astrometric accuracy: JWST NIRSpec
# (DJA, JADES) is tied to Gaia/NIRCam at sub-pixel level, ground-based slit/IFU
# surveys (VANDELS, MUSE) are looser, and AAOmega fibres (DEVILS) looser still.
# These radii drive BOTH (a) de-duplication of a survey against higher-priority
# layers in the unified compilation and (b) matching a survey onto a base
# catalogue (Khostovan, ASTRODEEP). Dial a value here when a survey's astrometry
# warrants it — every count downstream follows from this single dict.
SPECZ_MATCH_RADII = {
    "JADES-DR4": 0.5,   # JWST NIRSpec, target coords (Gaia/NIRCam-tied)
    "DJA":       0.5,   # JWST NIRSpec MSA, homogenised re-reduction
    "VANDELS":   0.75,  # VIMOS multi-slit, ground-based
    "MUSE-Wide": 0.75,  # MUSE IFU, emission-line centroid
    "MUSE-UDF":  0.75,  # MUSE IFU, emission-line centroid
    "DEVILS":    1.0,   # AAT/AAOmega 2" fibres, ground-based
}
BASE_MATCH_RADIUS = 1.0   # arcsec; fallback when a survey is absent from the dict

# GOODS-S spec-z layers in PRIORITY order (first wins in dedup) and their colours.
# JADES DR4 is placed ABOVE DJA so its rigorously-graded A/B/C redshifts override
# DJA's homogenised z_best wherever the two overlap.
GS_SURVEYS = ("JADES-DR4", "DJA", "VANDELS", "MUSE-Wide", "MUSE-UDF")
GS_PALETTE = {"JADES-DR4": "#9467bd", "DJA": "#1f77b4", "VANDELS": "#2ca02c",
              "MUSE-Wide": "#d62728", "MUSE-UDF": "#ff7f0e"}

# Output paths
HERE         = os.getcwd()
REPO_ROOT    = os.path.abspath(os.path.join(HERE, ".."))
SPEC_DIR     = os.path.join(REPO_ROOT, "catalogues")
FIG_DIR      = os.path.join(HERE, "figures", "specz_analysis")
os.makedirs(FIG_DIR, exist_ok=True)
'''

EDITS["loaders-code"] = '''\
"""Catalogue loaders. Each returns an `astropy.table.Table`."""
from astropy.utils.data import download_file

DJA_URL = ("https://zenodo.org/records/15472354/files/"
           "dja_msaexp_emission_lines_v4.4.csv.gz")


def _path(*parts):
    return os.path.join(SPEC_DIR, *parts)


def load_dja_nirspec():
    """DJA NIRSpec v4.4 (Brammer / Heintz, Zenodo 15472354).

    Returns the full table; downstream code restricts to the field box.
    """
    path = download_file(DJA_URL, cache=True)
    return Table.read(path, format="csv")


def load_khostovan_cosmos():
    """Khostovan et al. 2026 (ApJS 282, 6) COSMOS spec-z compilation, unique table."""
    p = _path("cosmos_khostovan25", "specz_compilation_COSMOS_DR1.1_unique.fits")
    return Table.read(p)


def load_devils_d10():
    """DEVILS DR1 D10 (Davies et al. 2025) — rows with a real DEVILS spec-z."""
    return Table.read(_path("devils_dr1", "devils_dr1_d10_devils_specz.fits"))


def load_astrodeep_phys():
    """ASTRODEEP-GS43 (Merlin+21) physical-properties table."""
    return Table.read(_path("astrodeep_gs43", "astrodeep_gs43_phys.fits"))


def load_astrodeep_phot():
    """ASTRODEEP-GS43 (Merlin+21) photometric table (carries RA/Dec)."""
    return Table.read(_path("astrodeep_gs43", "astrodeep_gs43_phot.fits"))


def load_muse_wide():
    """MUSE-Wide DR1 emission-line objects (Urrutia+19)."""
    return Table.read(_path("muse_wide_dr1", "muse_wide_dr1_emobj.fits"))


def load_muse_udf():
    """AMUSED MUSE-UDF DR2 main (Bacon+23)."""
    return Table.read(_path("amused_museudf_dr2", "amused_museudf_dr2_dr2_main.fits"))


def load_vandels_cdfs():
    """VANDELS DR4 CDFS spectra (Garilli+21)."""
    return Table.read(_path("vandels_dr4_cdfs", "vandels_dr4_cdfs_cdfs.fits"))


def load_jades_dr4():
    """JADES DR4 NIRSpec combined catalogue (Curtis-Lake+25 / Scholtz+25), HDU 1.

    Returns the 5,190-row 'Obs_info' target table. Best redshift is ``z_Spec``
    with byte-string quality flag ``z_Spec_flag`` ('A'..'E'); ``Field`` is
    b"GS"/b"GN". Pulled from https://jades.herts.ac.uk/DR4/ (not yet on VizieR).
    """
    return Table.read(_path("jades_dr4", "Combined_DR4_external_v1.2.1.fits"), hdu=1)
'''

EDITS["cosmos-dja-xmatch"] = '''\
"""Cross-match DJA -> Khostovan and classify each DJA source.

The match radius is DJA-specific (SPECZ_MATCH_RADII["DJA"]), reflecting JWST
NIRSpec's sub-pixel astrometry rather than a blanket 1".

Categories:
    matched  : DJA source has *any* Khostovan entry within the DJA radius
    new      : DJA source has no Khostovan counterpart within the DJA radius
    upgrade  : matched, Khostovan entry has flag < 3 (low / no confidence)
"""
r_dja = match_radius("DJA")
xm_dja = blind_xmatch(
    dja_cos["ra"], dja_cos["dec"], ra, dec, radius_arcsec=r_dja,
)
khost_flag_d = flag[xm_dja.idx]
khost_z_d    = z[xm_dja.idx]
matched      = xm_dja.matched
secure_d     = (dja_cos["grade"] == 3) & (dja_cos["z_best"] > 0)

new_to_base  = secure_d & ~matched
upgrade      = secure_d & matched & ~np.isin(khost_flag_d, [3, 4])
agree_pool   = secure_d & matched &  np.isin(khost_flag_d, [3, 4])

print(f"DJA grade=3 sources in COSMOS  : {secure_d.sum():,}  "
      f"(match radius = {r_dja}\\u2033)")
print(f"  NEW   (no Khostovan match)   : {new_to_base.sum():>5,}")
print(f"  UPGRADE (Khostovan flag < 3) : {upgrade.sum():>5,}")
print(f"  agree-test pool (flag \\u2265 3)   : {agree_pool.sum():>5,}")
print()
print(xm_dja.note)
'''

EDITS["cosmos-devils"] = '''\
"""Cross-match DEVILS DR1 D10 -> Khostovan and report new-vs-known.

DEVILS is shallower (Y < 21.2) and overlaps the central COSMOS sub-region only.
Its main contribution is at z < 1 — most overlap with Khostovan is expected.
The match radius is DEVILS-specific (AAOmega 2" fibres -> looser tolerance).
"""
devils = load_devils_d10()
clean = devils[(devils["starFlag"] == 0)
               & (devils["artefactFlag"] == 0)
               & (devils["mask"] == 0)
               & (devils["DEVILS_z"] > 0)]
r_dev = match_radius("DEVILS")
xm_dev = blind_xmatch(
    clean["RAcen"], clean["DECcen"], ra, dec, radius_arcsec=r_dev,
)
m_sec = clean["DEVILS_prob"] >= 0.8

print(f"DEVILS clean spec-z              : {len(clean):,}  "
      f"(match radius = {r_dev}\\u2033)")
print(f"  DEVILS_prob \\u2265 0.8              : {m_sec.sum():,}")
print(f"     NEW to Khostovan            : {(m_sec & ~xm_dev.matched).sum():,}")
print(f"     in Khostovan                : {(m_sec &  xm_dev.matched).sum():,}")
print()
print("Per-tier DEVILS_prob\\u22650.8 sources NEW to Khostovan:")
for name in TIERS:
    n_new = (m_sec & ~xm_dev.matched & tier_mask(clean["DEVILS_z"], name)).sum()
    print(f"  {name:<14s}{n_new:>5,}")
print()
print(xm_dev.note)
'''

EDITS["gs-load-surveys"] = '''\
"""Load the five spec-z layers and report per-survey counts."""
dja_gs   = tab_dja[((tab_dja["ra"]  > 52.8) & (tab_dja["ra"]  < 53.5) &
                    (tab_dja["dec"] > -28.1) & (tab_dja["dec"] < -27.5))]
muse_wide = load_muse_wide()
muse_udf  = load_muse_udf()
vandels   = load_vandels_cdfs()
jades_dr4 = load_jades_dr4()

# JADES DR4 carries byte-string columns — decode before comparing.
def _decode(col):
    return np.array([s.decode() if isinstance(s, (bytes, bytearray)) else str(s)
                     for s in np.asarray(col)])
dr4_flag  = _decode(jades_dr4["z_Spec_flag"])
dr4_field = _decode(jades_dr4["Field"])
dr4_z     = np.asarray(jades_dr4["z_Spec"], dtype=float)
# GOODS-S, robust (A/B/C), valid redshift
dr4_gs_abc = ((dr4_field == "GS") & np.isin(dr4_flag, ["A", "B", "C"])
              & np.isfinite(dr4_z) & (dr4_z > 0))

print(f"JADES DR4 (combined)    : {len(jades_dr4):,}  "
      f"(GOODS-S A/B/C: {dr4_gs_abc.sum():,})")
print(f"DJA (GOODS-S box)       : {len(dja_gs):,}  "
      f"(grade=3: {((dja_gs['grade'] == 3) & (dja_gs['z_best'] > 0)).sum():,})")
print(f"MUSE-Wide DR1           : {len(muse_wide):,}  "
      f"(Conf\\u22652: {(muse_wide['Conf']  >= 2).sum():,})")
print(f"AMUSED MUSE-UDF DR2     : {len(muse_udf):,}  "
      f"(z>0: {(muse_udf['z']  > 0).sum():,})")
print(f"VANDELS DR4 CDFS        : {len(vandels):,}  "
      f"(q_zsp\\u22653: {(vandels['q_zsp'] >= 3).sum():,})")
'''

EDITS["gs-build"] = '''\
"""Build the unified GOODS-S spec-z table with priority-ordered, per-survey dedup.

Layers are stacked in GS_SURVEYS priority order (JADES-DR4 first, then DJA, then
the optical/IFU surveys) and reduced to ONE entry per physical source by a greedy
pass: walking the stacked rows in priority order, a row is kept only if no
already-kept row sits within *its own* survey's match radius (SPECZ_MATCH_RADII).
This collapses BOTH cross-survey duplicates AND intra-survey duplicates — the
latter matters because DJA NIRSpec is per-spectrum (multiple gratings/visits per
source), so ~8,800 of its 9,647 grade=3 rows are repeat observations of the same
object. JWST layers dedup tightly (0.5") and ground-based layers looser.
"""

def _make_layer(ra, dec, z, qual, survey):
    """Build a Table with the standard schema for one spec-z layer."""
    out = Table()
    out["ra"]     = np.asarray(ra,   dtype=float)
    out["dec"]    = np.asarray(dec,  dtype=float)
    out["z"]      = np.asarray(z,    dtype=float)
    out["qual"]   = np.asarray(qual, dtype=float)
    out["survey"] = np.array([survey] * len(out), dtype="U16")
    return out


def dedup_layers(layers, priority, radii):
    """Greedy unique-source dedup over layers stacked in priority order.

    A row j is kept iff no earlier (= higher-priority, or same-survey-earlier)
    KEPT row lies within ``radii[survey_j]`` of it. Implemented with a KD-tree on
    a local tangent-plane projection (arcsec); valid because GOODS-S spans < 0.5
    deg so planar distance ~ angular separation.
    """
    from scipy.spatial import cKDTree
    stacked = vstack([layers[k] for k in priority], join_type="outer")
    ra  = np.asarray(stacked["ra"],  dtype=float)
    dec = np.asarray(stacked["dec"], dtype=float)
    surv = np.asarray(stacked["survey"])
    dec0 = float(np.median(dec))
    xy = np.column_stack([ra * np.cos(np.radians(dec0)) * 3600.0, dec * 3600.0])
    tree = cKDTree(xy)
    rad = np.array([radii.get(s, BASE_MATCH_RADIUS) for s in surv])
    keep = np.zeros(len(stacked), dtype=bool)
    for j in range(len(stacked)):
        neigh = tree.query_ball_point(xy[j], rad[j])
        if any((k < j) and keep[k] for k in neigh):
            continue
        keep[j] = True
    return stacked[keep]


# Per-survey secure-redshift masks
sec_dja = (dja_gs["grade"] == 3) & (dja_gs["z_best"] > 0)
sec_van = (vandels["q_zsp"] >= 3) & (vandels["zsp"] > 0)
sec_mw  = (muse_wide["Conf"] >= 2) & (muse_wide["z"] > 0)
sec_mu  = muse_udf["z"] > 0

# JADES DR4 quality A/B/C -> numeric qual 3/2/1
_qmap    = {"A": 3.0, "B": 2.0, "C": 1.0}
dr4_qual = np.array([_qmap.get(f, 0.0) for f in dr4_flag])

gs_layers = {
    "JADES-DR4": _make_layer(jades_dr4["RA_TARG"][dr4_gs_abc],
                             jades_dr4["Dec_TARG"][dr4_gs_abc],
                             dr4_z[dr4_gs_abc], dr4_qual[dr4_gs_abc], "JADES-DR4"),
    "DJA":       _make_layer(dja_gs["ra"][sec_dja], dja_gs["dec"][sec_dja],
                             dja_gs["z_best"][sec_dja],
                             np.full(sec_dja.sum(), 3), "DJA"),
    "VANDELS":   _make_layer(vandels["RAJ2000"][sec_van], vandels["DEJ2000"][sec_van],
                             vandels["zsp"][sec_van], vandels["q_zsp"][sec_van], "VANDELS"),
    "MUSE-Wide": _make_layer(muse_wide["RAJ2000"][sec_mw], muse_wide["DEJ2000"][sec_mw],
                             muse_wide["z"][sec_mw], muse_wide["Conf"][sec_mw], "MUSE-Wide"),
    "MUSE-UDF":  _make_layer(muse_udf["RAJ2000"][sec_mu], muse_udf["DEJ2000"][sec_mu],
                             muse_udf["z"][sec_mu], np.full(sec_mu.sum(), 3), "MUSE-UDF"),
}

gs_specz = dedup_layers(gs_layers, GS_SURVEYS, SPECZ_MATCH_RADII)
print(f"Unified GOODS-S spec-z (per-survey dedup): {len(gs_specz):,}")
for s in GS_SURVEYS:
    print(f"  {s:<10s} {(gs_specz['survey'] == s).sum():>5,}  "
          f"(dedup r = {SPECZ_MATCH_RADII[s]}\\u2033)")
'''

EDITS["gs-fig6"] = '''\
"""Figure 6 — GOODS-S unified spec-z sky map + redshift distribution.

Panel (a): per-survey sky distribution over the ASTRODEEP photometric source list.
Panel (b): per-survey redshift distribution. The complementary roles of the five
layers are visible: MUSE-Wide/UDF dominate at z < 1 (and inside the KARMA window),
while JADES DR4 / DJA dominate at z > 1.5.
"""
fig = plt.figure(figsize=(13.5, 5.4))
gs   = gridspec.GridSpec(1, 2, width_ratios=[1.0, 1.4])
palette = GS_PALETTE

# (a) sky
ax = fig.add_subplot(gs[0, 0])
ax.scatter(astrodeep["RA"], astrodeep["Dec"], s=0.6, c="0.88",
           alpha=0.4, edgecolors="none", label=f"ASTRODEEP (N={len(astrodeep):,})")
for s in GS_SURVEYS:
    m = gs_specz["survey"] == s
    ax.scatter(gs_specz["ra"][m], gs_specz["dec"][m], s=3, c=palette[s], alpha=0.7,
               edgecolors="none", label=f"{s} (N={m.sum():,})")
ax.set_aspect("equal")
ax.invert_xaxis()
ax.set_xlabel("RA [deg]"); ax.set_ylabel("Dec [deg]")
ax.set_title("(a) GOODS-S sky coverage per survey")
ax.legend(loc="lower left", fontsize=7)

# (b) z dist
ax = fig.add_subplot(gs[0, 1])
bins = np.arange(0.0, 6.0, 0.04)
for s in GS_SURVEYS:
    m = gs_specz["survey"] == s
    ax.hist(gs_specz["z"][m], bins=bins, histtype="step", lw=1.4, color=palette[s],
            label=f"{s} ({m.sum():,})")
shade_tier_windows(ax)
ax.set_yscale("log")
ax.set_xlim(0, 5.5)
ax.set_xlabel("Redshift"); ax.set_ylabel("N per \\u0394z=0.04")
ax.set_title("(b) per-survey z distribution")
ax.legend(fontsize=8)
fig.tight_layout()
save_fig(fig, "fig06_gs_unified")
plt.show()
'''

EDITS["gs-fig7"] = '''\
"""Figure 7 — Photo-z performance check: DJA spec-z vs ASTRODEEP photo-z.

ASTRODEEP photo-z systematically underestimates DJA spec-z at z > 1
(median \\u0394z/(1+z) ~ +0.46). The implication for EMPOWER is that *tier-2 and
tier-3 candidates selected on photo-z alone* are unreliable until a true
spec-z is in hand for them. Uses the DJA-specific match radius.
"""
xm = blind_xmatch(dja_gs["ra"], dja_gs["dec"],
                  astrodeep["RA"], astrodeep["Dec"], radius_arcsec=match_radius("DJA"))
sec = (dja_gs["grade"] == 3) & (dja_gs["z_best"] > 0)
ok  = sec & xm.matched & (astrodeep["zphot"][xm.idx] > 0)
zd  = np.asarray(dja_gs["z_best"][ok])
zp  = np.asarray(astrodeep["zphot"][xm.idx[ok]])
dz  = (zd - zp) / (1.0 + zp)
tag = np.asarray(astrodeep["has_tag"])[xm.idx[ok]]

fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4))

ax = axes[0]
bins = np.linspace(-1.5, 1.5, 121)
ax.hist(np.clip(dz[tag],  bins[0], bins[-1]), bins=bins, histtype="step",
        lw=1.3, color="#1f77b4", label=f"prior spec-z tag ({tag.sum():,})")
ax.hist(np.clip(dz[~tag], bins[0], bins[-1]), bins=bins, histtype="step",
        lw=1.3, color="#d62728", label=f"photo-z only ({(~tag).sum():,})")
ax.set_xlabel("(z_DJA \\u2212 z_phot) / (1 + z_phot)")
ax.set_ylabel("N pairs")
ax.set_title(f"(a) Photo-z residual against DJA spec-z  ({len(zd):,} pairs)")
ax.set_yscale("log")
ax.legend(fontsize=8)

ax = axes[1]
zmx = max(zd.max(), zp.max(), 4.0)
ax.scatter(zp[~tag], zd[~tag], s=4, c="#d62728", alpha=0.35, edgecolors="none",
           label="photo-z only")
ax.scatter(zp[tag],  zd[tag],  s=4, c="#1f77b4", alpha=0.35, edgecolors="none",
           label="prior spec-z tag")
ax.plot([0, zmx], [0, zmx], ls=":", c="k", lw=1)
ax.set_xlabel("z (ASTRODEEP photo-z)")
ax.set_ylabel("z (DJA spec-z, grade=3)")
ax.set_xlim(0, zmx); ax.set_ylim(0, zmx)
ax.set_aspect("equal", adjustable="box")
ax.set_title("(b) DJA vs ASTRODEEP zphot")
ax.legend(fontsize=8, loc="upper left")

fig.tight_layout()
save_fig(fig, "fig07_gs_photoz_check")
plt.show()
print(f"median \\u0394z/(1+z) = {np.median(dz):+.3f}, "
      f"NMAD = {1.4826*np.median(np.abs(dz - np.median(dz))):.3f}")
print(xm.note)
'''

EDITS["gs-summary"] = '''\
"""Per-tier verified-spec-z inventory in GOODS-S.

For each ASTRODEEP source we ask whether a member of the unified ``gs_specz``
sits within the matched survey's OWN radius (SPECZ_MATCH_RADII). We then count,
per EMPOWER tier:

* candidates   — ASTRODEEP zphot inside the tier and log M*>=10
* verified-z   — same, AND a unified spec-z within the per-survey radius
* still photoz — candidates with no spec-z match
"""
# Nearest gs_specz neighbour for every ASTRODEEP source; accept the match only if
# the separation is below the matched survey's own radius.
xm_gs = blind_xmatch(astrodeep["RA"], astrodeep["Dec"],
                     gs_specz["ra"], gs_specz["dec"], radius_arcsec=BASE_MATCH_RADIUS)
nn_survey   = np.asarray(gs_specz["survey"])[xm_gs.idx]
nn_radius   = np.array([match_radius(s) for s in nn_survey])
has_gsspecz = xm_gs.sep_arcsec < nn_radius
sp_survey   = np.where(has_gsspecz, nn_survey, "")

print("EMPOWER GOODS-S candidates (M*>=1e10, ASTRODEEP zphot inside tier):")
print(f"  {'tier':<14s}{'cands':>7s}{'verified':>9s}{'still photoz':>14s}"
      f"  surveys contributing")
for name in TIERS:
    m = tier_mask(astrodeep["zphot"], name) & (astrodeep["logM"] >= 10)
    n_cand = int(m.sum())
    n_ver  = int((m & has_gsspecz).sum())
    s_in   = sp_survey[m & has_gsspecz]
    bd = ", ".join(f"{s}:{(s_in==s).sum()}"
                   for s in GS_SURVEYS if (s_in==s).any())
    print(f"  {name:<14s}{n_cand:>7,}{n_ver:>9,}{n_cand-n_ver:>14,}  {bd}")

# gs_specz entries with no ASTRODEEP counterpart (no mass yet)
xm_inv     = blind_xmatch(gs_specz["ra"], gs_specz["dec"],
                          astrodeep["RA"], astrodeep["Dec"], radius_arcsec=BASE_MATCH_RADIUS)
inv_radius = np.array([match_radius(s) for s in np.asarray(gs_specz["survey"])])
gs_new     = ~(xm_inv.sep_arcsec < inv_radius)
print(f"\\ngs_specz entries NOT in ASTRODEEP : {gs_new.sum():,}")
for s in GS_SURVEYS:
    print(f"   {s:<10s} {((gs_specz['survey'] == s) & gs_new).sum():>5,}")
'''

# ----------------------------------------------------------------------
# Append a match_radius() helper to setup-helpers (keep its existing body).
# ----------------------------------------------------------------------
HELPER_SNIPPET = '''

def match_radius(survey):
    """Per-survey positional match radius (arcsec); see SPECZ_MATCH_RADII."""
    return SPECZ_MATCH_RADII.get(survey, BASE_MATCH_RADIUS)
'''


def main():
    with open(NB) as f:
        nb = json.load(f)

    edited = []
    for cell in nb["cells"]:
        cid = cell.get("id")
        if cid == "setup-helpers":
            src = "".join(cell["source"])
            if "def match_radius(" not in src:
                src = src + HELPER_SNIPPET
            cell["source"] = src.splitlines(keepends=True)
            cell["outputs"] = []
            cell["execution_count"] = None
            edited.append(cid)
        elif cid in EDITS and EDITS[cid] is not None:
            cell["source"] = EDITS[cid].splitlines(keepends=True)
            cell["outputs"] = []
            cell["execution_count"] = None
            edited.append(cid)

    with open(NB, "w") as f:
        json.dump(nb, f, indent=1)
    print("Edited cells:", edited)
    missing = [k for k in EDITS if k not in edited and EDITS[k] is not None]
    if missing:
        print("WARNING — these target ids were not found:", missing)


if __name__ == "__main__":
    main()
