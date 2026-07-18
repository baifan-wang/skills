#!/usr/bin/env python3
"""Validate SLTCAP Python implementation against web tool output."""
import json
import subprocess
import sys

tests = [
    # (args, expected_anions, expected_cations, expected_potential)
    ("--mass 0 --conc 150 --charge 0 --box 10", 90.30, 90.30, 0.00),
    ("--mass 0 --conc 150 --charge -8 --box 10", 86.39, 94.39, -1.14),
    ("--mass 0 --conc 150 --charge -4 --box 10", 88.32, 92.32, -0.57),
    ("--mass 0 --conc 150 --charge -2 --box 10", 89.31, 91.31, -0.28),
    ("--mass 0 --conc 150 --charge +4 --box 10", 92.32, 88.32, 0.57),
    ("--mass 0 --conc 100 --charge 0 --box 10", 60.20, 60.20, 0.00),
    ("--mass 0 --conc 50 --charge 0 --box 10", 30.10, 30.10, 0.00),
    ("--mass 0 --conc 50 --charge -8 --box 10", 26.36, 34.36, -3.40),
    ("--mass 50 --conc 150 --charge -8 --box 10", 81.00, 89.00, -1.21),
    ("--mass 0 --conc 150 --charge 0 --waters 10000", 27.00, 27.00, 0.00),
    ("--mass 0 --conc 150 --charge -8 --waters 10000", 23.29, 31.29, -3.79),
    ("--mass 0 --conc 150 --charge 0 --waters 5000", 13.50, 13.50, 0.00),
    ("--mass 0 --conc 50 --charge 0 --waters 10000", 9.00, 9.00, 0.00),
    ("--mass 0 --conc 150 --charge -8 --edge 5 --axis 5", 300.79, 308.79, -0.34),
    ("--mass 0 --conc 150 --charge -8 --box-x 10 --box-y 10 --box-z 12", None, None, None),
]

print(f"{'Test':<60s} {'Anions':>8s} {'Cations':>8s} {'Pot(mV)':>8s}  Status")
print("-" * 98)

all_ok = True
for args, exp_an, exp_cat, exp_phi in tests:
    result = subprocess.run(
        f"python3 scripts/sltcap.py --json {args}",
        shell=True, capture_output=True, text=True, cwd="/mnt/d/claude/_skills/amber-md"
    )
    data = json.loads(result.stdout)
    an = data["n_anions"]
    cat = data["n_cations"]
    phi = data["potential_mv"]

    if exp_an is not None:
        ok = (abs(an - exp_an) < 0.015 and abs(cat - exp_cat) < 0.015
              and abs(phi - exp_phi) < 0.015)
        if not ok:
            all_ok = False
        status = "OK" if ok else f"FAIL an={an-exp_an:+.3f} cat={cat-exp_cat:+.3f} phi={phi-exp_phi:+.3f}"
    else:
        ok = True
        status = "INFO"

    print(f"{args:<60s} {an:8.2f} {cat:8.2f} {phi:8.2f}  {status}")

print()
print("ALL TESTS PASSED" if all_ok else "SOME TESTS FAILED")
sys.exit(0 if all_ok else 1)
