# LEGA-C Passive Galaxies

> Based on Borghi et al. (2022) https://iopscience.iop.org/article/10.3847/1538-4357/ac3240 where DR2 was used

## Directory: `1_Catalogs/`

### Contents

| File/Folder | Description |
|-------------|-------------|
| `legac_dr2_spectra/` | Original LEGA-C DR2 spectra |
| `legac_dr2_cat.fits` / `.ascii` | LEGA-C DR2 catalog (1988 spectra, 1922 unique sources) |
| `LEGAC-DR2+COSMOS15.fits` | Cross-match of LEGA-C DR2 × COSMOS2015 |
| `LEGAC-DR2+COSMOS15+BORGHI22.fits` | Same as above, with passive galaxy classification flags (see below) |
| `RADEC_LEGAC_bonafide.dat` | RA/DEC of bona-fide passive sample |
| `explore.ipynb` | Jupyter notebook to explore the catalog and reproduce part of Figure 1 of Borghi et al. (2022) |

---

### Passive Flags

The extended catalog (`+BORGHI22.fits`) includes three boolean masks:

| Flag | Selection Stage | Size | Criteria |
|:----:|-----------------|------|---------|
| `parent` | **parent sample** | 1622 | LEGA-C flags: `flag_z`, `flagspec`, `flagPXF == 0`; finite *z* ≠ 0; finite NUV, *r*, *J* values |
| `photo_pass` | **photometric passive** | 658 | NUV*rJ* color cut from Ilbert et al. (2013) 
| `spectrophoto_pass` | **spectro-photometric passive** | 485 | NUV*rJ* color cut + EW([O II]) ≤ 5 Å; preliminary check of EW([O II]) |
| `passive` | **bona-fide passive** | 350 | Final classification after visual inspection for residual emission |



### Absorption indices 

The extended catalog (`+BORGHI22.fits`) includes also the measurements of absorption features made with the `exact` method of pyLick and used in Borghi et al. (2022). The column names are formatted as:

- `exact_<index_name>` and `exact_<index_name>_err`, for measurements and associated uncertainties made on the original spectra;
- `exactMIL_<index_name>` and `exactMIL_<index_name>_err`, on the spectra convolved to the MILES resolution.

Where `<index_name>` has the same naming convention as in pyLick: https://pylick.readthedocs.io/user_guide/Indices/


## Directory: `2_Spectra/`
### Contents
| File/Folder | Description |
|-------------|-------------|
| `composite_350_passive.dat` | Composite spectrum of 350 bona-fide passive galaxies |
| `composite_not350.dat` | Composite spectrum of the spectro-photometric passive but not bona-fide |