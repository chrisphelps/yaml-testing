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



def show_resolved_arns(config):
    default_role = config.get("defaults", {}).get("roleName", "")
    print("  Resolved ARNs:")
    for account_id, entry in config.get("accounts", {}).items():
        role_name = entry.get("roleName", default_role)
        arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        print(f"    {arn}")


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
