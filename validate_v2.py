#!/usr/bin/env python3
"""Validate enrichment_v2.yaml structure, format, and cross-references."""

import sys
import yaml
import jsonschema

SCHEMA_FILE = "schema_v2.yaml"
CONFIG_FILE = "enrichment_v2.yaml"

errors = []
warnings = []


def err(msg):
    errors.append(f"  ERROR: {msg}")


def warn(msg):
    warnings.append(f"  WARN:  {msg}")


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def validate_schema(config, schema):
    validator = jsonschema.Draft7Validator(schema)
    schema_errors = sorted(validator.iter_errors(config), key=lambda e: e.path)
    for e in schema_errors:
        path = " -> ".join(str(p) for p in e.absolute_path) or "(root)"
        err(f"[schema] {path}: {e.message}")


def validate_cross_references(config):
    top_regions = set(config.get("awsRegions", []))
    top_namespaces = set(config.get("awsNamespaces", []))

    for account_id, entry in config.get("accounts", {}).items():
        for ns in entry.get("namespaces", []):
            if ns not in top_namespaces:
                err(f"Account {account_id}: namespace '{ns}' not in top-level awsNamespaces")

        for region in entry.get("regions", []):
            if region not in top_regions:
                err(f"Account {account_id}: region '{region}' not in top-level awsRegions")


def validate_unused_top_level(config):
    top_regions = set(config.get("awsRegions", []))
    top_namespaces = set(config.get("awsNamespaces", []))

    used_regions = set()
    used_namespaces = set()
    for entry in config.get("accounts", {}).values():
        used_regions.update(entry.get("regions", []))
        used_namespaces.update(entry.get("namespaces", []))

    for region in top_regions - used_regions:
        warn(f"Region '{region}' declared in awsRegions but not used by any account")

    for ns in top_namespaces - used_namespaces:
        warn(f"Namespace '{ns}' declared in awsNamespaces but not used by any account")


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
    if not errors:
        validate_cross_references(config)
        validate_unused_top_level(config)

    if errors or warnings:
        status = "FAIL" if errors else "WARN"
        print(f"{status}  {CONFIG_FILE}")
        for line in errors + warnings:
            print(line)
        sys.exit(1 if errors else 0)
    else:
        print(f"OK    {CONFIG_FILE}")
        show_resolved_arns(config)
        sys.exit(0)


if __name__ == "__main__":
    main()
