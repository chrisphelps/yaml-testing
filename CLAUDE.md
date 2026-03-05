# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv run pytest                        # run all tests
uv run pytest test_convert.py -v     # run a single test file
uv run validate.py                   # validate enrichment.yaml (v1)
uv run validate_v2.py                # validate enrichment_v2.yaml (v2)
uv run convert.py                    # convert v2 → v1, output to stdout
uv run convert.py -o out.yaml        # convert v2 → v1, write to file
```

## Architecture

This project manages AWS CloudWatch enrichment configuration in two YAML formats and provides tooling to validate and convert between them.

### Two config formats

**v1 (`enrichment.yaml`)** — verbose, role-ARN-centric:
- `awsRoleArns` is a list of objects, each with a `role` (single-item list containing a full ARN), `namespaces`, and `regions`

**v2 (`enrichment_v2.yaml`)** — compact, account-ID-centric:
- `accounts` is a map keyed by 12-digit AWS account ID
- `defaults.roleName` provides the shared role name; individual accounts can override it with their own `roleName`
- Full ARNs are constructed at runtime: `arn:aws:iam::<account_id>:role/<roleName>`

### File relationships

- `schema.yaml` / `schema_v2.yaml` — JSON Schema (Draft 7) for each format; used by the validators
- `validate.py` / `validate_v2.py` — load the corresponding schema, run structural validation, then check cross-references (role `namespaces`/`regions` must be declared in top-level `awsNamespaces`/`awsRegions`) and warn on unused top-level entries
- `convert.py` — converts v2 → v1; the `convert(v2: dict) -> dict` function is pure (no I/O) and is the unit-tested surface
- `test_convert.py` — pytest tests for `convert()`
