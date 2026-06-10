#!/usr/bin/env python3
"""
Lightweight verification of the generated alpha108 CNF.

This checks the generated object, not the UNSAT proof:
- 180 original variables are mapped.
- 480 AP clauses are present as the first 480 clauses.
- No forbidden structural terms occur in the CNF.
"""

from __future__ import annotations

from itertools import product
from pathlib import Path
import argparse
import hashlib
import json
import re


def norm2(x):
    return sum(t*t for t in x)


def is_ap(a,b,c):
    return a != c and all(a[i] + c[i] == 2*b[i] for i in range(4))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_dimacs(path: Path):
    clauses = []
    nvars = None
    nclauses = None
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("c"):
            continue
        if line.startswith("p cnf"):
            _, _, nv, nc = line.split()
            nvars = int(nv)
            nclauses = int(nc)
            continue
        lits = [int(x) for x in line.split()]
        if not lits or lits[-1] != 0:
            raise RuntimeError(f"Bad DIMACS clause line: {line}")
        clauses.append(lits[:-1])
    return nvars, nclauses, clauses


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="alpha108_run")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    cnf_path = outdir / "alpha108_no109.cnf"
    manifest_path = outdir / "alpha108_model_manifest.json"

    if not cnf_path.exists():
        raise FileNotFoundError(cnf_path)

    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    points = sorted(
        x for x in product(range(5), repeat=4)
        if 19 <= norm2(x) <= 27
    )
    assert len(points) == 180

    var = {p:i+1 for i,p in enumerate(points)}
    T = set(points)
    aps = []
    for i,a in enumerate(points):
        for c in points[i+1:]:
            s = tuple(a[k] + c[k] for k in range(4))
            if all(v % 2 == 0 for v in s):
                b = tuple(v//2 for v in s)
                if b in T and is_ap(a,b,c):
                    aps.append((a,b,c))
    assert len(aps) == 480

    nvars, nclauses, clauses = read_dimacs(cnf_path)

    expected_ap_clauses = [[-var[a], -var[b], -var[c]] for a,b,c in aps]

    ok = True
    checks = []
    checks.append(("cnf exists", cnf_path.exists()))
    checks.append(("DIMACS nclauses matches", nclauses == len(clauses)))
    checks.append(("first 480 clauses are AP clauses", clauses[:480] == expected_ap_clauses))
    checks.append(("manifest says 480 AP clauses", manifest.get("canonical_AP_clauses") == 480))
    checks.append(("manifest says 180 original variables", manifest.get("variables_original") == 180))
    checks.append(("no forbidden terms", not manifest.get("forbidden_structural_terms")))

    for name, passed in checks:
        print(("PASS" if passed else "FAIL") + ": " + name)
        ok = ok and bool(passed)

    print("sha256(alpha108_no109.cnf)=" + sha256_file(cnf_path))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
