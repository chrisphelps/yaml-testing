#!/usr/bin/env python3
"""Validate enrichment_v2.yaml structure, format, and cross-references."""

import sys
import yaml
import jsonschema

SCHEMA_FILE = "schema_v2.yaml"
CONFIG_FILE = "enrichment_v2.yaml"

errors = []


def err(msg):
    errors.append(f"  ERROR: {msg}")


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def validate_schema(config, schema):
    validator = jsonschema.Draft7Validator(schema)
    schema_errors = sorted(validator.iter_errors(config), key=lambda e: e.path)
    for e in schema_errors:
        path = " -> ".join(str(p) for p in e.absolute_path) or "(root)"
        err(f"[schema] {path}: {e.message}")


def validate_unique_accounts(config):
    seen = {}
    for team in config.get("teams", []):
        team_name = team.get("name", "<unnamed>")
        for account_id in team.get("accounts", {}):
            if account_id in seen:
                err(f"Account {account_id} appears in both team '{seen[account_id]}' and '{team_name}'")
            else:
                seen[account_id] = team_name


def show_resolved_arns(config):
    default_role = config.get("defaults", {}).get("roleName", "")
    print("  Resolved ARNs:")
    for team in config.get("teams", []):
        role_name = team.get("roleName", default_role)
        for account_id in team.get("accounts", {}):
            arn = f"arn:aws:iam::{account_id}:role/{role_name}"
            print(f"    [{team['name']}] {arn}")


def main():
    try:
        config = load_yaml(CONFIG_FILE)
    except yaml.YAMLError as e:
        print(f"FAIL  {CONFIG_FILE}\n  ERROR: YAML parse error: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"FAIL  {CONFIG_FILE}\n  ERROR: file not found")
        sys.exit(1)

    try:
        schema = load_yaml(SCHEMA_FILE)
    except Exception as e:
        print(f"FAIL  {SCHEMA_FILE}\n  ERROR: could not load schema: {e}")
        sys.exit(1)

    validate_schema(config, schema)
    if not errors:
        validate_unique_accounts(config)

    if errors:
        print(f"FAIL  {CONFIG_FILE}")
        for line in errors:
            print(line)
        sys.exit(1)
    else:
        print(f"OK    {CONFIG_FILE}")
        show_resolved_arns(config)
        sys.exit(0)


if __name__ == "__main__":
    main()
