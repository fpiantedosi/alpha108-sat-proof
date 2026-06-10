#!/usr/bin/env python3
"""
Generate the naked CNF model for the alpha(T_{19,8}) <= 108 upper-bound test.

The CNF asserts the existence of an AP-free subset A of T_{19,8}^{(5,4)}
with |A| >= 109.

If this CNF is UNSAT, then alpha(T_{19,8}) <= 108.

No NormalFormA, H7, signature-count, S4 gauge, local-maximality, or SP-A1
basis constraints are included.
"""

from __future__ import annotations

from itertools import product
from pathlib import Path
import argparse
import hashlib
import json
from typing import Iterable, Tuple

from pysat.card import CardEnc, EncType
from pysat.formula import CNF


Point = Tuple[int, int, int, int]


def norm2(x: Point) -> int:
    return sum(t * t for t in x)


def is_ap(a: Point, b: Point, c: Point) -> bool:
    return a != c and all(a[i] + c[i] == 2 * b[i] for i in range(4))


def ts(x: Point) -> str:
    return "(" + ",".join(map(str, x)) + ")"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_points() -> list[Point]:
    points = sorted(
        x for x in product(range(5), repeat=4)
        if 19 <= norm2(x) <= 27
    )
    if len(points) != 180:
        raise RuntimeError(f"Expected 180 shell points, found {len(points)}")
    return points


def build_aps(points: list[Point]) -> list[tuple[Point, Point, Point]]:
    T = set(points)
    aps: list[tuple[Point, Point, Point]] = []
    for i, a in enumerate(points):
        for c in points[i + 1:]:
            s = tuple(a[k] + c[k] for k in range(4))
            if all(v % 2 == 0 for v in s):
                b = tuple(v // 2 for v in s)  # type: ignore[assignment]
                if b in T and is_ap(a, b, c):  # type: ignore[arg-type]
                    aps.append((a, b, c))  # type: ignore[arg-type]
    if len(aps) != 480:
        raise RuntimeError(f"Expected 480 canonical APs, found {len(aps)}")
    return aps


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="alpha108_run", help="Output directory.")
    parser.add_argument(
        "--encoding",
        default="seqcounter",
        choices=["seqcounter", "cardnetwrk", "sortnetwrk", "totalizer"],
        help="PySAT cardinality encoding for sum x_i >= 109.",
    )
    args = parser.parse_args()

    enc_map = {
        "seqcounter": EncType.seqcounter,
        "cardnetwrk": EncType.cardnetwrk,
        "sortnetwrk": EncType.sortnetwrk,
        "totalizer": EncType.totalizer,
    }

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    points = build_points()
    aps = build_aps(points)
    var = {p: i + 1 for i, p in enumerate(points)}

    cnf = CNF()

    # AP-free constraints: no canonical AP has all three selected.
    # Clause: not x_a OR not x_b OR not x_c.
    for a, b, c in aps:
        cnf.append([-var[a], -var[b], -var[c]])

    # Cardinality: at least 109 selected among x1..x180.
    card = CardEnc.atleast(
        lits=list(range(1, 181)),
        bound=109,
        top_id=180,
        encoding=enc_map[args.encoding],
    )
    cnf.extend(card.clauses)

    cnf_path = outdir / "alpha108_no109.cnf"
    cnf.to_file(str(cnf_path))

    variable_map = outdir / "alpha108_variable_map.csv"
    variable_map.write_text(
        "var_id,point\n" +
        "\n".join(f"{var[p]},{ts(p)}" for p in points) +
        "\n",
        encoding="utf-8",
    )

    ap_map = outdir / "alpha108_ap_constraints.csv"
    ap_map.write_text(
        "ap_id,a,b,c,var_a,var_b,var_c\n" +
        "\n".join(
            f"{i+1},{ts(a)},{ts(b)},{ts(c)},{var[a]},{var[b]},{var[c]}"
            for i, (a, b, c) in enumerate(aps)
        ) +
        "\n",
        encoding="utf-8",
    )

    forbidden_terms = [
        "NormalFormA", "SP-A1", "SP_A1", "P1", "P2", "P3", "P4", "P5",
        "H7", "signature", "Signature", "gauge", "S4", "selected_mask",
        "FULL", "NONE", "PARTIAL", "basis", "endpoint", "witness",
    ]

    cnf_text = cnf_path.read_text(encoding="utf-8", errors="ignore")
    forbidden_hits = [term for term in forbidden_terms if term in cnf_text]

    manifest = {
        "model": "alpha108_no109.cnf",
        "meaning": "existence of AP-free subset of T19_8 with size >= 109",
        "if_unsat": "alpha(T19_8) <= 108",
        "variables_original": 180,
        "cnf_variables_total": cnf.nv,
        "canonical_AP_clauses": len(aps),
        "cardinality_encoding": args.encoding,
        "cardinality_bound": "sum(x1..x180) >= 109",
        "cardinality_encoding_clauses": len(card.clauses),
        "total_clauses": len(cnf.clauses),
        "forbidden_structural_terms": forbidden_hits,
        "sha256_cnf": sha256_file(cnf_path),
        "sha256_variable_map": sha256_file(variable_map),
        "sha256_ap_map": sha256_file(ap_map),
    }

    manifest_path = outdir / "alpha108_model_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("Generated naked CNF model")
    print(json.dumps(manifest, indent=2))

    if forbidden_hits:
        raise RuntimeError(f"Forbidden structural terms found in CNF: {forbidden_hits}")


if __name__ == "__main__":
    main()
