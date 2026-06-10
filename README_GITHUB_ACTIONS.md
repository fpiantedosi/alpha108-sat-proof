# Alpha108 GitHub Actions SAT Pack

This repository attempts to prove the finite upper bound

\[
\alpha(T_{19,8}^{(5,4)}) \le 108.
\]

It does so by generating a **naked CNF model** asserting the opposite:

\[
\exists A\subseteq T_{19,8}^{(5,4)},\quad |A|\ge109,\quad A\text{ is 3-AP-free}.
\]

If the CNF is UNSAT, then no AP-free subset of size 109 exists.

## Important claim boundary

The generated CNF contains only:

- 480 AP-free clauses:
  \[
  \neg x_a \lor \neg x_b \lor \neg x_c
  \]
- one cardinality constraint encoded in CNF:
  \[
  \sum_{i=1}^{180} x_i \ge 109.
  \]

It contains no NormalFormA, no H7, no signatures, no S4 gauge constraints, no SP-A1 basis constraints and no local-maximality constraints.

## How to use by browser only

1. Create a new GitHub repository.
2. Upload the full contents of this pack to the root of the repository.
3. Go to the `Actions` tab.
4. Enable workflows if GitHub asks.
5. Select `alpha108 naked SAT proof attempt`.
6. Click `Run workflow`.
7. Start with:
   - `cardinality_encoding = seqcounter`
   - `solver_timeout_seconds = 21000`
8. Wait for completion.
9. Download the artifact named `alpha108-results`.

## How to interpret outcomes

### Best case

The logs contain:

```text
s UNSATISFIABLE
```

and `drat_trim.log` confirms the proof.

Then the upper bound is certificate-supported.

### SAT

If the logs contain:

```text
s SATISFIABLE
```

then a counterexample of size at least 109 may exist. Download all artifacts immediately.

### Timeout / Unknown

Try another encoding:

- `cardnetwrk`
- `sortnetwrk`
- `totalizer`

or run on a larger VM.

## Files

- `scripts/generate_alpha108_cnf.py`: builds the naked model.
- `scripts/verify_alpha108_cnf.py`: verifies the generated model structure.
- `.github/workflows/run_alpha108_sat.yml`: GitHub Actions workflow.
- `scripts/package_alpha108_results.py`: collects hashes and outputs.
