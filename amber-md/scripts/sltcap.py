#!/usr/bin/env python3
"""SLTCAP: Screening Layer Tally by Container Average Potential.

Calculate the number of salt ions needed for MD simulation based on the
Donnan equilibrium method described in:
  Schmit et al., J. Chem. Theory Comput. 14, 1823-1827 (2018)

Usage:
  sltcap.py --mass 50 --conc 150 --charge -8 --box 10
  sltcap.py --mass 0 --conc 150 --charge 0 --waters 10000
  sltcap.py --mass 50 --conc 150 --charge -8 --edge 5 --axis 5
  sltcap.py --mass 0 --conc 150 --charge 0 --box-x 10 --box-y 10 --box-z 12
"""

import argparse
import math
import sys

# Calibrated constants — matched to SLTCAP web tool output
BOX_ION_FACTOR = 0.0006020  # n_base = V_solv(nm³) × C(mM) × BOX_ION_FACTOR
WATER_MOLARITY = 55.556  # mol/L, n_base = N_w × C(mM) / (WATER_MOLARITY × 1000)
WATER_FACTOR = 1.0 / (WATER_MOLARITY * 1000)
WATER_DENSITY = BOX_ION_FACTOR / WATER_FACTOR  # ~33.445 molecules/nm³
KT_OVER_E = 25.68  # mV at 298 K
PROT_SPECIFIC_VOLUME = 1.1947  # nm³/kDa, calibrated from 50kDa protein data


def protein_volume(mass_kda: float) -> float:
    """Compute protein excluded volume in nm³."""
    return mass_kda * PROT_SPECIFIC_VOLUME


def solve_donnan(n_base: float, z_solute: float) -> dict:
    """Solve Donnan equilibrium for ion counts and potential.

    n_cations - n_anions = -z_solute  (charge neutrality)
    n_cations * n_anions = n_base²    (Donnan equilibrium)
    """
    if n_base == 0:
        return {"n_anions": 0.0, "n_cations": 0.0, "potential_mv": 0.0}

    # eΦ/kT = arcsinh(Z / (2*n_base))
    x = z_solute / (2.0 * n_base)
    ephi_over_kt = math.asinh(x)

    n_anions = n_base * math.exp(ephi_over_kt)
    n_cations = n_base * math.exp(-ephi_over_kt)
    potential_mv = ephi_over_kt * KT_OVER_E

    return {
        "n_anions": n_anions,
        "n_cations": n_cations,
        "potential_mv": potential_mv,
    }


def from_box_volume(
    box_volume_nm3: float,
    mass_kda: float,
    conc_mm: float,
    z_solute: float,
) -> dict:
    """Calculate using box volume method."""
    v_prot = protein_volume(mass_kda)
    v_solv = max(box_volume_nm3 - v_prot, 0.0)
    n_base = v_solv * conc_mm * BOX_ION_FACTOR
    n_water = v_solv * WATER_DENSITY
    result = solve_donnan(n_base, z_solute)
    result.update({
        "v_box": box_volume_nm3,
        "v_prot": v_prot,
        "v_solv": v_solv,
        "n_water": n_water,
        "n_base": n_base,
        "method": "box_volume",
    })
    return result


def from_water_count(
    n_water: float,
    conc_mm: float,
    z_solute: float,
) -> dict:
    """Calculate using explicit water molecule count."""
    n_base = n_water * conc_mm * WATER_FACTOR
    result = solve_donnan(n_base, z_solute)
    result.update({
        "v_box": None,
        "v_prot": None,
        "v_solv": n_water / WATER_DENSITY,
        "n_water": n_water,
        "n_base": n_base,
        "method": "water_count",
    })
    return result


def from_edge_axis(
    box_edge_nm: float,
    protein_axis_nm: float,
    mass_kda: float,
    conc_mm: float,
    z_solute: float,
) -> dict:
    """Calculate using distance-to-edge + protein longest axis method."""
    box_length = 2.0 * box_edge_nm + protein_axis_nm
    box_volume = box_length ** 3
    return from_box_volume(box_volume, mass_kda, conc_mm, z_solute)


def format_result(result: dict) -> str:
    """Format calculation result for display."""
    lines = []
    lines.append("=" * 52)
    lines.append("  SLTCAP — Ion Count Calculator for MD Simulation")
    lines.append("=" * 52)
    lines.append(f"  Method:              {result['method']}")

    if result.get("v_box") is not None:
        lines.append(f"  Box volume:          {result['v_box']:.1f} nm³")
    if result.get("v_prot") is not None:
        lines.append(f"  Protein volume:      {result['v_prot']:.1f} nm³")
    lines.append(f"  Solvent volume:      {result['v_solv']:.1f} nm³")
    lines.append(f"  Water molecules:     {result['n_water']:.0f}")
    lines.append(f"  Base ions (each):    {result['n_base']:.2f}")
    lines.append("-" * 52)
    lines.append(f"  Anions  (Cl⁻):       {result['n_anions']:.2f}")
    lines.append(f"  Cations (Na⁺):       {result['n_cations']:.2f}")
    lines.append(f"  Total ions:          {result['n_anions'] + result['n_cations']:.2f}")
    lines.append("-" * 52)
    lines.append(f"  Average potential:   {result['potential_mv']:.2f} mV")
    lines.append("=" * 52)
    lines.append("")
    lines.append("  Note: Round ion counts to nearest integer for tleap addions2.")
    lines.append("  Cite: Schmit et al., JCTC 14, 1823-1827 (2018)")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="SLTCAP — Calculate salt ions for MD simulation boxes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --mass 50 --conc 150 --charge -8 --box 10
  %(prog)s --mass 0 --conc 150 --charge 0 --waters 10000
  %(prog)s --mass 50 --conc 150 --charge -8 --edge 5 --axis 5
  %(prog)s --mass 0 --conc 150 --charge 0 --box-x 10 --box-y 10 --box-z 12
        """,
    )

    # Required for all modes
    parser.add_argument("--conc", type=float, required=True,
                        help="Salt concentration (mM)")
    parser.add_argument("--charge", type=float, required=True,
                        help="Net solute charge (proton charge units)")

    # Protein
    parser.add_argument("--mass", type=float, default=0.0,
                        help="Protein mass (kDa), default 0")

    # Geometry (choose one)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--box", type=float,
                       help="Simple cubic box length (nm)")
    group.add_argument("--box-x", type=float,
                       help="Rectangular box X length (nm)")
    group.add_argument("--waters", type=float,
                       help="Number of water molecules")
    group.add_argument("--edge", type=float,
                       help="Distance from protein to box edge (nm)")

    # Rectangular box needs Y, Z
    parser.add_argument("--box-y", type=float,
                        help="Rectangular box Y length (nm)")
    parser.add_argument("--box-z", type=float,
                        help="Rectangular box Z length (nm)")

    # Edge+axis method needs axis
    parser.add_argument("--axis", type=float,
                        help="Longest axis of protein (nm)")

    # Output options
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    parser.add_argument("--quiet", action="store_true",
                        help="Only print ion counts (n_anions n_cations)")

    args = parser.parse_args()

    # Validate and route to correct method
    if args.box is not None:
        result = from_box_volume(args.box ** 3, args.mass, args.conc,
                                 args.charge)
    elif args.box_x is not None:
        if args.box_y is None or args.box_z is None:
            parser.error("--box-x requires --box-y and --box-z")
        vol = args.box_x * args.box_y * args.box_z
        result = from_box_volume(vol, args.mass, args.conc, args.charge)
    elif args.waters is not None:
        result = from_water_count(args.waters, args.conc, args.charge)
    elif args.edge is not None:
        if args.axis is None:
            parser.error("--edge requires --axis")
        result = from_edge_axis(args.edge, args.axis, args.mass, args.conc,
                                args.charge)
    else:
        parser.error("No geometry method specified")

    if args.json:
        import json
        print(json.dumps(result, indent=2, default=str))
    elif args.quiet:
        print(f"{result['n_anions']:.2f} {result['n_cations']:.2f}")
    else:
        print(format_result(result))


if __name__ == "__main__":
    main()
