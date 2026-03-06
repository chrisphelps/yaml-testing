#!/usr/bin/env python3
"""Convert enrichment_v2.yaml (compact format) to enrichment.yaml (expanded format)."""

import argparse
import sys
import yaml


def convert(v2: dict) -> dict:
    default_role_name = v2["defaults"]["roleName"]

    all_regions = set()
    all_namespaces = set()
    role_arns = []
    for team in v2["teams"]:
        role_name = team.get("roleName", default_role_name)
        for account_id, account in team["accounts"].items():
            all_regions.update(account["regions"])
            all_namespaces.update(team["namespaces"])
            arn = f"arn:aws:iam::{account_id}:role/{role_name}"
            role_arns.append({
                "role": [arn],
                "namespaces": team["namespaces"],
                "regions": account["regions"],
            })

    return {
        "awsRegions": sorted(all_regions),
        "awsNamespaces": sorted(all_namespaces),
        "awsRoleArns": role_arns,
    }


def main():
    parser = argparse.ArgumentParser(description="Convert enrichment_v2.yaml to v1 format.")
    parser.add_argument("input", nargs="?", default="enrichment_v2.yaml",
                        help="Input file (default: enrichment_v2.yaml)")
    parser.add_argument("-o", "--output", default="-",
                        help="Output file (default: stdout)")
    args = parser.parse_args()

    with open(args.input) as f:
        v2 = yaml.safe_load(f)

    v1 = convert(v2)
    output = yaml.dump(v1, default_flow_style=False, sort_keys=False)

    if args.output == "-":
        sys.stdout.write(output)
    else:
        with open(args.output, "w") as f:
            f.write(output)


if __name__ == "__main__":
    main()
