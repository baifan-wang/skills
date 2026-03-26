---
name: autodock
description: Automated molecular docking workflow with AutoDock Vina. Use when users want to dock ligands to protein receptors, run virtual screening, prepare PDB files for docking, extract residues, or perform structure-based drug design. Supports multiple ligand formats (SMILES, SDF, MOL2, PDB, CDX), automatic receptor preparation, parallel docking execution, and result visualization. Trigger for any docking-related task, PDB file preparation, or when working with protein-ligand complexes.
license: MIT license
metadata:
    skill-author: Claude Code User
---

# AutoDock: Automated Molecular Docking Workflow

## Overview

This skill provides a comprehensive automated pipeline for molecular docking using AutoDock Vina. It integrates multiple tools for:

- **Protein structure preparation**: Remove water/metals, add hydrogens, preserve specific ligands
- **Residue extraction**: Extract specific residues or small molecules from PDB files
- **Molecular docking**: Run AutoDock Vina with parallel execution
- **Result analysis**: Energy rankings, visualization scripts, and summary reports

**Core Capabilities:**
- Convert ligand formats (SMILES, SDF, MOL, MOL2, CDX, PDB) to PDBQT
- Prepare protein receptors with hydrogen addition
- Define docking pocket using center.pdb or manual coordinates
- Run parallel docking with multi-core support
- Generate energy bar charts and PyMOL visualization scripts
- Create detailed docking result summaries

**Key Distinction:** This skill automates the ENTIRE docking workflow from raw ligand/protein files to final analysis, not just individual steps.

## When to Use This Skill

This skill should be used when:

- "Dock these molecules to this protein" or "run molecular docking"
- "Prepare this PDB file for docking" (add hydrogens, remove water/metals)
- "Extract residues X, Y, Z from this PDB file"
- "Define the binding pocket" or "set up docking parameters"
- "Run virtual screening" or "screen compound library"
- Structure-based drug design workflows
- Protein-ligand binding analysis
- Creating visualization for docking results

## Required Dependencies

### External Software
- **AutoDock Vina**: For molecular docking
- **OpenBabel**: For format conversion (obabel)
- **MGLTools**: For receptor/ligand preparation (prepare_ligand4.py, prepare_receptor4.py)

### Python Packages
- rdkit
- numpy
- pandas
- matplotlib

### Configuration
Before first use, update paths in `autovina.py`:
```python
VINA_EXE_PATH = "C:\\apps\\vina.exe"
OPENBABEL_PATH = "C:\\OpenBabel-3.1.1\\obabel.exe"
MGL_PATH = "C:\\Program Files (x86)\\MGLTools-1.5.7\\"
```

## Core Workflows

### Workflow 1: Complete Docking Pipeline

**Use Case:** Full docking workflow from raw files to results

**Step 1: Prepare Working Directory**
```
working_directory/
├── receptor.pdb          # Protein receptor file
├── center.pdb            # Optional: reference for binding pocket center
├── conf.txt              # Optional: docking parameters (auto-created)
└── ligands/              # Directory containing ligand files
    ├── compound1.sdf
    ├── compound2.smiles
    └── ...
```

**Step 2: Run AutoVina**
```bash
python autovina.py
```

The script will:
1. Auto-create `conf.txt` if not present
2. Extract center coordinates from `center.pdb` if present
3. Convert all ligands to PDBQT format
4. Prepare the receptor
5. Run parallel docking
6. Generate results and visualizations

**Output Structure:**
```
working_directory/
├── results/                    # Docking results
│   ├── ligand1_docked.pdbqt
│   ├── ligand2_docked.pdbqt
│   └── ...
├── docking_energies.png        # Energy bar chart
├── docking_results.pml         # PyMOL script
└── docking_summary.txt         # Results summary
```

### Workflow 2: Extract Residues/Binding Pocket

**Use Case:** Extract specific residues or ligands from a PDB file for docking center

**Extract by residue name and number:**
```bash
python extract_residues.py input.pdb "A ASN96 ALA35 B GLU97" -o center.pdb
```

**Extract by single-letter amino acid codes:**
```bash
python extract_residues.py input.pdb "A N96 A35 B E97" -o center.pdb
```

**Extract by residue numbers only:**
```bash
python extract_residues.py input.pdb "A 96 35 B 97" -o center.pdb
```

**Extract a small molecule/ligand:**
```bash
python extract_residues.py input.pdb "A ACJ" -o center.pdb
```

**Input Format:**
- Chain ID + residue specifications (space-separated)
- Chain ID: Single letter (A-Z)
- Residue specs:
  - `ASN96` - 3-letter code + sequence number
  - `N96` - Single-letter amino acid + sequence number
  - `96` - Sequence number only
  - `ACJ` - Small molecule residue name (3-letter)

### Workflow 3: Prepare PDB Files

**Use Case:** Process PDB file before docking (add hydrogens, remove contaminants)

```bash
python process_pdb.py input.pdb -o receptor.pdb --add-hydrogens --tool openbabel
```

**Common Options:**
- `--add-hydrogens`: Add hydrogen atoms to the structure
- `--tool`: Hydrogen addition tool (`auto`, `pdb2pqr`, `openbabel`)
- `--output`: Output file path (default: `[input]_processed.pdb`)

**Automatic Processing:**
- Removes water molecules (HOH, WAT, H2O)
- Removes metal ions (based on element column)
- Preserves specified hetero atoms (e.g., `--keep-fad`)

**Keep cofactors:**
```bash
python process_pdb.py input.pdb -o receptor.pdb --add-hydrogens --keep-fad
```

### Workflow 4: Configure Docking Parameters

**Default conf.txt:**
```
center_x = 0.0
center_y = 0.0
center_z = 0.0
size_x = 16.5
size_y = 16.5
size_z = 16.5
exhaustiveness = 8
num_modes = 10
energy_range = 4
```

**Parameter Guide:**
| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| `center_x/y/z` | Pocket center coordinates | From center.pdb or manual |
| `size_x/y/z` | Search box size (Angstroms) | 10-30 |
| `exhaustiveness` | Search thoroughness | 1-32 (higher = more thorough) |
| `num_modes` | Max output conformations | 1-20 |
| `energy_range` | Energy range for output modes | 3-7 kcal/mol |

**Tip:** Place a reference structure (ligand or key residues) as `center.pdb` in the working directory. The center coordinates will be automatically calculated from its atom coordinates.

## Supported Ligand Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| SMILES | `.smi`, `.smiles` | Tab-separated: `SMILES name` |
| Structure Data | `.sdf`, `.sd` | Can contain multiple molecules |
| MDL Mol | `.mol` | Single molecule |
| Tripos Mol2 | `.mol2` | 3D structure |
| ChemDraw | `.cdx` | Requires OpenBabel |
| PDB | `.pdb` | 3D coordinates |
| PDBQT | `.pdbqt` | AutoDock format (no conversion needed) |

**SMILES file format:**
```
CC(=O)Oc1ccccc1C(=O)O aspirin
CN1C=NC2=C1C(=O)N(C(=O)N2C)C caffeine
```

## Result Interpretation

### Energy Scores

Docking energy (kcal/mol) indicates binding strength:
- **Lower (more negative)** = Stronger predicted binding
- **Common range:** -12 to -2 kcal/mol
- **Good hit:** Typically < -7 kcal/mol

### Output Files

**docking_summary.txt:**
```
Rank  Molecule Name                   Docking Energy (kcal/mol)
--------------------------------------------------
1     compound_x                      -10.50
2     compound_y                      -9.23
3     compound_z                      -8.45
...
```

**PyMOL Visualization:**
```bash
pymol docking_results.pml
```
This loads receptor and top poses with color-coded ligands.

## Advanced Usage

### Batch Virtual Screening

1. Place all ligand files in `ligands/` directory
2. Prepare `receptor.pdb`
3. Create `center.pdb` or set coordinates in `conf.txt`
4. Run `python autovina.py`

### Custom Grid Box Size

For larger binding sites:
```
size_x = 25.0
size_y = 25.0
size_z = 25.0
```

For highly targeted docking:
```
size_x = 12.0
size_y = 12.0
size_z = 12.0
```

### Fixing Windows Vina Output Issues

The pipeline automatically fixes common Windows Vina output problems:
- Binary character contamination
- Missing ENDMDL markers
- Encoding issues

## Troubleshooting

### Common Issues

**"No ligand files found"**
- Check `ligands/` directory exists and contains supported file types
- Verify file extensions are correct

**"Receptor preparation failed"**
- Check MGLTools path configuration
- Ensure receptor.pdb has proper ATOM records
- Try re-processing with `process_pdb.py` to fix formatting

**"Low docking scores (weak binding)"**
- Verify binding pocket coordinates are correct
- Increase `exhaustiveness` parameter
- Check ligand 3D structure quality

**"OpenBabel conversion failed"**
- Install OpenBabel and verify path
- For CDX files, ensure OpenBabel was compiled with CDX support

### Performance Tips

1. **Use GPU if available** (Vina-GPU variant)
2. **Parallel processing** is automatic - utilizes all CPU cores
3. **Pre-filter large libraries** by drug-likeness before docking
4. **Increase exhaustiveness** for difficult targets (costs more time)

## Best Practices

1. **Validate structures** before docking (check for missing residues)
2. **Define pocket accurately** using known ligand positions or key residues
3. **Use appropriate box size** - not too large (slow) or small (misses poses)
4. **Review top poses visually** in PyMOL or similar
5. **Combine with experimental validation** for lead candidates
6. **Consider protein flexibility** for flexible binding sites (ensemble docking)

## File Structure Reference

```
autodock/
├── autovina.py           # Main docking automation script
├── extract_residues.py   # Extract residues/ligands from PDB
├── process_pdb.py        # PDB file preprocessing
└── pdb_utils.py          # Shared utility functions
```

## Integration Example

Complete workflow example:

```bash
# 1. Extract binding site reference
python extract_residues.py 3NKS.pdb "A ACJ" -o center.pdb

# 2. Extract key active site residues (optional, for visualization)
python extract_residues.py 3NKS.pdb "A LEU56 HIS106" -o active_site.pdb

# 3. Prepare receptor (add hydrogens, keep FAD cofactor)
python process_pdb.py 3NKS.pdb -o receptor.pdb --add-hydrogens --keep-fad

# 4. Place ligands in ligands/ directory
mkdir -p ligands
# Copy or create ligand files

# 5. Run docking
python autovina.py

# 6. View results
# - docking_summary.txt for energy ranking
# - docking_energies.png for visualization
# - docking_results.pml for PyMOL
```

## Citations

When using this pipeline, cite:

**AutoDock Vina:**
```
Trott, O., & Olson, A. J. (2010). AutoDock Vina: improving the speed and accuracy of docking with a new scoring function, efficient optimization, and multithreading. Journal of computational chemistry, 31(2), 455-461.
```

**MGLTools:**
```
Morris, G. M., et al. (2009). AutoDock4 and AutoDockTools4: Automated docking with selective receptor flexibility. Journal of computational chemistry, 30(16), 2785-2791.
```
