# PDB Format Reference

## PDB Line Format

Standard ATOM/HETATM record format:

| Column | Field | Description |
|--------|-------|-------------|
| 1-6 | Record name | ATOM or HETATM |
| 7-11 | Atom serial number | Integer |
| 13-16 | Atom name | Chemical symbol + position |
| 17 | Alternate location indicator | A-Z or blank |
| 18-20 | Residue name | 3-letter code |
| 22 | Chain identifier | A-Z or blank |
| 23-26 | Residue sequence number | Integer |
| 27 | Insertion code | A-Z or blank |
| 31-38 | X coordinate | Float (Angstroms) |
| 39-46 | Y coordinate | Float (Angstroms) |
| 47-54 | Z coordinate | Float (Angstroms) |
| 55-60 | Occupancy | Float (default 1.0) |
| 61-66 | Temperature factor | Float |
| 77-78 | Element symbol | Right-justified |
| 79-80 | Charge | Optional |

## Residue Name Codes

### Standard Amino Acids

| 3-Letter | 1-Letter | Name |
|----------|----------|------|
| ALA | A | Alanine |
| ARG | R | Arginine |
| ASN | N | Asparagine |
| ASP | D | Aspartic acid |
| CYS | C | Cysteine |
| GLN | Q | Glutamine |
| GLU | E | Glutamic acid |
| GLY | G | Glycine |
| HIS | H | Histidine |
| ILE | I | Isoleucine |
| LEU | L | Leucine |
| LYS | K | Lysine |
| MET | M | Methionine |
| PHE | F | Phenylalanine |
| PRO | P | Proline |
| SER | S | Serine |
| THR | T | Threonine |
| TRP | W | Tryptophan |
| TYR | Y | Tyrosine |
| VAL | V | Valine |

### Non-Standard Amino Acids

| 3-Letter | Maps To | Notes |
|----------|---------|-------|
| ASH | D | Protonated Asp |
| GLH | E | Protonated Glu |
| HID/HIE/HIP | H | Histidine tautomers |
| LYN | K | Neutral Lys |
| CYM | C | Cysteine anion |
| CYX | C | Disulfide-bonded Cys |

### Water Residue Names

- HOH (most common)
- WAT
- H2O
- WAT1, HOH1 (numbered variants)

### Common Cofactors and Ligands

| Name | Full Name |
|------|-----------|
| FAD | Flavin-adenine dinucleotide |
| NAD | Nicotinamide-adenine-dinucleotide |
| NAD | Nicotinamide-adenine-dinucleotide phosphate |
| HEM | Heme |
| ATP | Adenosine triphosphate |
| ADP | Adenosine diphosphate |

## Element Symbols for Metals

Common metal ions in PDB files:
- ZN - Zinc
- CU - Copper
- FE - Iron
- MG - Magnesium
- CA - Calcium
- MN - Manganese
- CO - Cobalt
- NI - Nickel
- K - Potassium
- NA - Sodium

Full list in `pdb_utils.py`: `METAL_ELEMENTS`

## Common PDB Issues and Fixes

### Missing Hydrogens

Problem: X-ray crystallography typically doesn't resolve hydrogen atoms.

Solution: Use `process_pdb.py --add-hydrogens` with OpenBabel or pdb2pqr.

### Chain ID Missing

Problem: Some PDB files have blank chain IDs.

Solution: Default chain 'A' is assumed by `extract_residues.py`.

### Insertion Codes

Problem: Residue 96A and 96 are different positions.

Solution: Specify insertion codes explicitly: `A 96A` or `ASN96A`.

### Alternate Locations

Problem: Same atom has multiple positions (A/B/C indicators).

Solution: Usually first alt-loc (A or blank) is used.

### Hetero Atoms

Problem: Cofactors, ligands, metals labeled as HETATM.

Solution: Use appropriate extraction methods; preserve cofactors with `--keep-*` flags.
