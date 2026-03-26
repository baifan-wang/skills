# Troubleshooting Guide

## Installation Issues

### Python Dependencies

**Problem:** Module not found errors (rdkit, pandas, etc.)

**Solution:**
```bash
pip install rdkit pandas numpy matplotlib
```

For conda users:
```bash
conda install -c conda-forge rdkit pandas numpy matplotlib
```

### External Tools Not Found

**Problem:** `FileNotFoundError: vina.exe not found`

**Solution:**
1. Download AutoDock Vina from: http://vina.scripps.edu/download.html
2. Update path in `autovina.py`:
```python
VINA_EXE_PATH = "C:\\path\\to\\vina.exe"
```

**Problem:** OpenBabel not found

**Solution:**
1. Download from: https://openbabel.org/docs/dev/Installation/windows.html
2. Update path:
```python
OPENBABEL_PATH = "C:\\path\\to\\obabel.exe"
```

**Problem:** MGLTools not found

**Solution:**
1. Download from: http://mgltools.scripps.edu/downloads
2. Update paths:
```python
MGL_PATH = "C:\\Program Files (x86)\\MGLTools-1.5.7\\"
```

## Docking Errors

### No Output Files Generated

**Causes and Solutions:**

1. **Empty ligands directory**
   - Check `ligands/` folder exists
   - Verify file extensions match supported formats

2. **Invalid ligand structure**
   - Check SDF/SMILES with RDKit:
   ```python
   from rdkit import Chem
   mol = Chem.MolFromSmiles('your_smiles')
   print(mol is not None)  # Should be True
   ```

3. **Receptor preparation failed**
   - Check receptor.pdb has ATOM records
   - Try re-processing: `python process_pdb.py input.pdb -o receptor.pdb`

### Low/Affinity Scores

**Problem:** All compounds show weak binding (> -5 kcal/mol)

**Solutions:**

1. **Check pocket center**
   - Verify center.pdb contains correct atoms
   - Print center coordinates from log

2. **Increase box size**
   ```
   size_x = 25.0
   size_y = 25.0
   size_z = 25.0
   ```

3. **Increase exhaustiveness**
   ```
   exhaustiveness = 16
   ```

4. **Validate ligand preparation**
   - Ensure 3D structures generated correctly
   - Check protonation states

### Windows-Specific Issues

**Problem:** Corrupt PDBQT output files

**Solution:** The pipeline auto-fixes Windows Vina output issues. If problems persist:
- Check for file encoding issues
- Ensure sufficient disk space

**Problem:** Subprocess shell=True required

**Solution:** Already handled in code. If modifying, use:
```python
subprocess.run(cmd, shell=True, capture_output=True)
```

## PDB Processing Errors

### Missing Residues

**Problem:** Residue not found in PDB

**Solutions:**
1. Check residue name spelling (case-sensitive)
2. Verify chain ID is correct
3. Check for insertion codes: `96A` vs `96`
4. Use verbose mode: `python extract_residues.py ... -v`

### Hydrogen Addition Fails

**Problem:** pdb2pqr or OpenBabel fails

**Solutions:**

1. **Try alternate tool:**
```bash
python process_pdb.py input.pdb --add-hydrogens --tool openbabel
# or
python process_pdb.py input.pdb --add-hydrogens --tool pdb2pqr
```

2. **Check for modified residues** that tools don't recognize

3. **Fix malformed PDB** format issues first

### Format Conversion Issues

**Problem:** SMILES to 3D fails

**Solution:**
- Verify SMILES string is valid
- Check for unusual valences
- Try generating conformer manually:
```python
from rdkit import Chem
from rdkit.Chem import AllChem

mol = Chem.MolFromSmiles('CCO')
mol = Chem.AddHs(mol)
AllChem.EmbedMolecule(mol)
AllChem.MMFFOptimizeMolecule(mol)
```

**Problem:** CDX conversion fails

**Solution:**
- Ensure OpenBabel was built with CDX support
- Try exporting to SDF from ChemDraw first

## Performance Issues

### Slow Docking

**Causes and Solutions:**

1. **Large search box**
   - Reduce size_x/y/z if possible
   - Target the pocket more precisely

2. **Low exhaustiveness vs thoroughness**
   - Higher exhaustiveness = more thorough but slower
   - Balance based on requirements

3. **CPU vs GPU**
   - Consider Vina-GPU for large screens
   - Use all available cores (default behavior)

### Memory Errors

**Problem:** Out of memory during batch processing

**Solutions:**
1. Reduce batch size
2. Process ligands in smaller groups
3. Close other applications

## Output Interpretation Issues

### No Poses Generated

**Problem:** PDBQT output has no ATOM records

**Causes:**
- Ligand too large for pocket
- Pocket coordinates wrong
- Ligand preparation failed

**Solution:**
- Verify ligand was converted successfully
- Check pocket coordinates match binding site
- Increase box size

### Multiple Conformations

**Problem:** Which pose to use?

**Solution:**
- First pose (rank 1) has best score
- Check RMSD between poses
- Lower energy = better prediction
- Consider experimental validation

## Common Warning Messages

### "Warning: SDF file contains no molecules"

**Cause:** Empty or corrupt SDF file

**Solution:** Verify source file, try re-downloading or re-exporting

### "Warning: Unable to generate 3D structure"

**Cause:** RDKit conformer generation failed

**Solution:**
- Check SMILES validity
- May need manual 3D structure generation

### "Warning: PDB file has no ENDMDL marker"

**Cause:** Non-standard PDB format

**Solution:** Usually auto-fixed; if not, manually add ENDMDL

## Getting Help

1. **Check logs:** Use `-v` or `--verbose` flags
2. **Validate inputs:** Use RDKit/OpenBabel tools directly
3. **Simplify:** Test with single ligand first
4. **File formats:** Ensure correct file extensions
5. **Paths:** Verify all external tool paths in configuration
