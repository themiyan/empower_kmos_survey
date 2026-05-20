# LEGA-C Passive Galaxies

> Based on Borghi et al. (2022) https://iopscience.iop.org/article/10.3847/1538-4357/ac3240 where DR2 was used

> **Note on spectra:** the original LEGA-C DR2/DR3 rest-frame spectra (large HDF5
> files) are **not included** in this repository. Re-fetch them from the public
> LEGA-C data release (van der Wel et al. 2016, 2021) if needed; the catalogues
> below are sufficient for the passive-galaxy selection.

## Directory: `1_Catalogs/`

### Contents

| File/Folder | Description |
|-------------|-------------|
| `LEGAC_DR2+COSMOS15.fits` | Cross-match of LEGA-C DR2 × COSMOS2015 |
| `LEGAC_DR2+COSMOS15+BORGHI22.fits` | Same as above, with passive-galaxy classification flags and absorption indices (see below) |
| `B22.dat` | Borghi et al. (2022) bona-fide passive sample table |
| `RADEC_LEGAC_bonafide.dat` | RA/DEC of the bona-fide passive sample |
| `legac_dr3/legac_dr3_final.fits` | LEGA-C DR3 catalogue |
| `legac_dr3/legac_dr3_view.ecsv` | LEGA-C DR3 working view (ECSV) |
| `explore.ipynb` | Explore the catalogue and reproduce part of Figure 1 of Borghi et al. (2022) |
| `selection.ipynb` | Passive-galaxy selection workflow |

---

### Passive Flags

The extended catalog (`LEGAC_DR2+COSMOS15+BORGHI22.fits`) includes three boolean masks:

| Flag | Selection Stage | Size | Criteria |
|:----:|-----------------|------|---------|
| `parent` | **parent sample** | 1622 | LEGA-C flags: `flag_z`, `flagspec`, `flagPXF == 0`; finite *z* ≠ 0; finite NUV, *r*, *J* values |
| `photo_pass` | **photometric passive** | 658 | NUV*rJ* color cut from Ilbert et al. (2013) 
| `spectrophoto_pass` | **spectro-photometric passive** | 485 | NUV*rJ* color cut + EW([O II]) ≤ 5 Å; preliminary check of EW([O II]) |
| `passive` | **bona-fide passive** | 350 | Final classification after visual inspection for residual emission |



### Absorption indices 

The extended catalog (`LEGAC_DR2+COSMOS15+BORGHI22.fits`) includes also the measurements of absorption features made with the `exact` method of pyLick and used in Borghi et al. (2022). The column names are formatted as:

- `exact_<index_name>` and `exact_<index_name>_err`, for measurements and associated uncertainties made on the original spectra;
- `exactMIL_<index_name>` and `exactMIL_<index_name>_err`, on the spectra convolved to the MILES resolution.

Where `<index_name>` has the same naming convention as in pyLick: https://pylick.readthedocs.io/user_guide/Indices/


## Directory: `2_Stacks/`
### Contents
| File/Folder | Description |
|-------------|-------------|
| `composite_350_passive.dat` / `.pdf` | Composite spectrum (data + figure) of the 350 bona-fide passive galaxies |
| `composite_not350.dat` / `.pdf` | Composite spectrum (data + figure) of the spectro-photometric passive but not bona-fide sample |

## Directory: `3_PassiveSelection/`
### Contents
| File/Folder | Description |
|-------------|-------------|
| `priorities.ipynb` | Notebook assigning KMOS observing priorities to the passive sample |

## Other files
| File | Description |
|------|-------------|
| `passive_selection_recap.png` | Summary figure of the passive-galaxy selection |