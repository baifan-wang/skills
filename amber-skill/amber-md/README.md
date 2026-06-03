# Amber MD Simulation Skill

Amber 分子动力学模拟全流程助手。Claude 直接执行体系构建（antechamber/parmchk2/tleap）和轨迹分析（cpptraj + Python 绘图），用户自行运行计算密集的模拟步骤（pmemd.cuda/pmemd.MPI）。

## Supported Systems

- Protein-ligand complexes
- Protein-only systems
- Protein-protein complexes

## Prerequisites

- AmberTools 26+ (`antechamber`, `parmchk2`, `tleap`, `cpptraj`)
- Amber 26+ (`pmemd.cuda` or `pmemd.MPI` or `sander`)
- Python 3.7+ with `pandas`, `numpy`, `matplotlib`
- Perl (for `process_mdout.perl`)

## Workflow

| Stage | Description | Executor |
|-------|-------------|----------|
| 0 | Information collection | Interactive |
| 1 | System building (antechamber/tleap) | Claude |
| 2 | MD simulation (min/heat/equil/production) | User |
| 3 | Trajectory analysis + plotting | Claude |
| 4 | Troubleshooting | Guided |

### Stage 0 — Information Collection

Ask user: input files, system type, compute resources (GPU/CPU), scheduler (bash/Slurm/PBS), simulation length (default 1 ns), analysis requirements.

**Defaults**: ff19SB + TIP3P + GAFF2, Langevin thermostat (ntt=3, gamma_ln=2.0), 1 ns production.

### Stage 1 — System Building

1. Small molecule parameterization: `antechamber` + `parmchk2` (ask for net charge first)
2. LEaP system assembly: write `leap.in`, run `tleap -f leap.in`

**Critical**: `comp_dry.top` **must** be saved before `solvateoct`. Wrong order causes `Number of atoms in NetCDF file does not match topology` errors during analysis.

For MM-PBSA, also save `protein.top` and `ligand.top` separately.

### Stage 2 — MD Simulation

Generate control files and run script:
- `min1.in` / `min2.in` / `min3.in` — Three-stage energy minimization
- `heat.in` — Heating 0K→300K (50 ps, NVT)
- `density.in` — Density equilibration (50 ps, NPT)
- `product.in` — Production (1 ns, NPT, NetCDF trajectory)
- `run.sh` — Batch execution script

User runs simulation. GPU (RTX 5090): ~5 min/ns. CPU: ~5 h/ns.

### Stage 3 — Trajectory Analysis

| Module | Tool | Output |
|--------|------|--------|
| Thermodynamics | `process_mdout.perl` + matplotlib | T/P/E time series |
| RMSD / RMSF / Rg | cpptraj + matplotlib | Stability metrics |
| SASA / DSSP | cpptraj + matplotlib | Surface area, secondary structure |
| H-bonds | cpptraj | H-bond count/occupancy |
| Distance matrix | cpptraj + matplotlib | Cα distance heatmap |
| Clustering | cpptraj k-means/hieragglo | Representative conformations |
| PCA | cpptraj (two-step) | Principal components |
| Free energy landscape | matplotlib | ΔG = −RT ln(P/Pmax) |
| MM-PBSA/GBSA | MMPBSA.py | Binding free energy (**complexes only**) |

## Directory Structure

```
workdir/
├── prep/                  # System building outputs
│   ├── leap.in
│   ├── ligand.prepin / ligand.frcmod
│   ├── comp_oct.top / comp_oct.crd  (solvated — for simulation)
│   ├── comp_dry.top / comp_dry.crd  (vacuum — for analysis)
│   ├── protein.top / protein.crd    (for MM-PBSA)
│   └── ligand.top / ligand.crd      (for MM-PBSA)
├── md/                    # Simulation inputs
│   ├── min1.in / min2.in / min3.in
│   ├── heat.in / density.in / product.in
│   └── run.sh
└── analysis/              # Analysis scripts and outputs
    ├── strip/
    ├── physical/
    ├── rmsd/
    ├── sasa/
    ├── hbond/
    ├── distmat/
    ├── cluster/
    ├── pca/
    ├── fel/
    └── mmpbsa/
```

## Important Rules

### LEaP: Save dry topology before solvation

```tleap
comp = combine { protein ligand }
saveamberparm comp comp_dry.top comp_dry.crd   # ← BEFORE solvateoct
saveamberparm protein protein.top protein.crd  # ← for MM-PBSA
saveamberparm ligand ligand.top ligand.crd     # ← for MM-PBSA
solvateoct comp TIP3PBOX 10.0                  # ← AFTER dry saves
```

### cpptraj: Always use `comment="#"` when reading output data

All cpptraj output files have `#` comment headers. Use `pd.read_csv(..., comment="#", header=None)` or manually skip `#` lines when reading.

### cpptraj: Paths are relative to analysis subdirectory

```
# analysis/strip/strip.in
parm ../../prep/comp_dry.top
trajin ../../md/product.nc

# analysis/rmsd/rmsd.in
parm ../../prep/comp_dry.top
trajin ../strip/strip.nc
```

### PCA: Must run in two steps

Step 1: `matrix covar` + `diagmatrix` + `run` → generates `evecs.dat`
Step 2: `projection evecs evecs.dat out proj.dat @CA beg 1 end 2` + `run`

`diagmatrix` is an analysis command (executed after `run`); `projection` checks for eigenvector data at parse time. Same invocation = empty dataset error.

### Clustering: repout in main command

```cpptraj
cluster C0 kmeans clusters 5 randompoint maxit 500 rms @CA sieve 10 \
  repout rep repframe \
  out cnumvtime.dat summary summary.dat info info.dat
```

Do NOT write `cluster C0 repout rep repframe` as a separate command — it overwrites the previous `C0` definition.

### DSSP: Wide-format matrix

cpptraj `secstruct` outputs a wide matrix (col 0 = frame, cols 1-N = per-residue integer SS codes). Parse with `dssp_raw.iloc[:, 1:].values`. SS code mapping: 0=None, 1=Para, 2=Anti, 3=3-10, 4=Alpha, 5=Pi, 6=Turn, 7=Bend.

### MM-PBSA/GBSA: Complexes only

MM-PBSA computes ΔG_binding = G_complex − G_receptor − G_ligand. Requires two independent components. Not applicable to standalone protein systems.

### RMSF: Use line+dot plot, not bar chart

```python
axes[1].plot(rmsf[0], rmsf[1], marker='o', linewidth=1.0, markersize=4, color='steelblue')
```

### evecs.dat: Manual parsing required

Format: header line → dimension line → per-mode: "index eigenvalue" → component lines → "****" separator. Cannot use `pd.read_csv` directly.

### DENSITY may have only 1 column

`process_mdout.perl` outputs vary in column count. Check `data.shape[1]` before accessing column index.

## Data Format Quick Reference

| File | Format | Read Method |
|------|--------|-------------|
| `*.dat` (cpptraj output) | `#` header + whitespace | `pd.read_csv(..., comment="#", header=None)` |
| `evecs.dat` | Custom (header + `****` separators) | Manual line-by-line parse |
| `dssp.dat` | Wide matrix (frame × residues) | `pd.read_csv` → `iloc[:, 1:]` |
| `summary.*` (perl output) | Whitespace, variable columns | Check `shape[1]` before indexing |
| `mmgbsa.dat` (MMPBSA.py) | Space-delimited summary stats | `re.match()` for term extraction |
| `proj.dat` (cpptraj) | `#Frame Mode1 Mode2` | `pd.read_csv(..., comment="#")` |
| `cnumvtime.dat` | `#Frame C0` | `pd.read_csv(..., comment="#")` |
| `summary.dat` (cluster) | `#Cluster Frames Frac ...` | `pd.read_csv(..., comment="#", header=None, names=[...])` |

## Troubleshooting

See `references/troubleshooting.md` for detailed error-resolution guide covering:

- antechamber atom type / bond parameter issues
- LEaP charge / residue / bond warnings
- Energy minimization non-convergence / NaN
- SHAKE failure / vlimit exceeded / energy drift
- cpptraj topology-trajectory atom count mismatch
- PCA empty eigenvector dataset
- Clustering algorithm not recognized
- H-bond analysis returning no data
- Python DataFrame column/index errors from cpptraj output formats

## References

- `references/force-fields.md` — Force field selection guide
- `references/input-templates.md` — All `.in` file templates with parameter explanations
- `references/analysis.md` — Complete cpptraj commands and Python plotting code
- `references/troubleshooting.md` — Error diagnosis and solutions
- `scripts/process_mdout.perl` — Thermodynamic data extraction script
