import pytest
from convert import convert

BASE_V2 = {
    "defaults": {"roleName": "CloudWatchLogsRole"},
    "awsRegions": ["us-east-1", "us-west-2"],
    "awsNamespaces": ["AWS/EC2", "AWS/Lambda"],
    "accounts": {
        "123456789012": {
            "namespaces": ["AWS/EC2"],
            "regions": ["us-west-2"],
        },
        "234567890123": {
            "namespaces": ["AWS/Lambda"],
            "regions": ["us-east-1"],
        },
    },
}


def test_top_level_keys():
    result = convert(BASE_V2)
    assert set(result.keys()) == {"awsRegions", "awsNamespaces", "awsRoleArns"}


def test_regions_and_namespaces_passed_through():
    result = convert(BASE_V2)
    assert result["awsRegions"] == ["us-east-1", "us-west-2"]
    assert result["awsNamespaces"] == ["AWS/EC2", "AWS/Lambda"]


def test_role_arn_constructed_from_default_role_name():
    result = convert(BASE_V2)
    arns = [entry["role"][0] for entry in result["awsRoleArns"]]
    assert "arn:aws:iam::123456789012:role/CloudWatchLogsRole" in arns
    assert "arn:aws:iam::234567890123:role/CloudWatchLogsRole" in arns


def test_role_is_single_item_list():
    result = convert(BASE_V2)
    for entry in result["awsRoleArns"]:
        assert isinstance(entry["role"], list)
        assert len(entry["role"]) == 1


def test_namespaces_and_regions_per_account():
    result = convert(BASE_V2)
    by_arn = {e["role"][0]: e for e in result["awsRoleArns"]}

    entry_1 = by_arn["arn:aws:iam::123456789012:role/CloudWatchLogsRole"]
    assert entry_1["namespaces"] == ["AWS/EC2"]
    assert entry_1["regions"] == ["us-west-2"]

    entry_2 = by_arn["arn:aws:iam::234567890123:role/CloudWatchLogsRole"]
    assert entry_2["namespaces"] == ["AWS/Lambda"]
    assert entry_2["regions"] == ["us-east-1"]


def test_per_account_role_name_override():
    v2 = {
        **BASE_V2,
        "accounts": {
            "123456789012": {
                "roleName": "CustomRole",
                "namespaces": ["AWS/EC2"],
                "regions": ["us-west-2"],
            },
        },
    }
    result = convert(v2)
    arn = result["awsRoleArns"][0]["role"][0]
    assert arn == "arn:aws:iam::123456789012:role/CustomRole"


def test_account_without_override_uses_default_role_name():
    v2 = {
        **BASE_V2,
        "accounts": {
            "123456789012": {
                "namespaces": ["AWS/EC2"],
                "regions": ["us-west-2"],
            },
        },
    }
    result = convert(v2)
    arn = result["awsRoleArns"][0]["role"][0]
    assert arn == "arn:aws:iam::123456789012:role/CloudWatchLogsRole"


def test_account_count_matches():
    result = convert(BASE_V2)
    assert len(result["awsRoleArns"]) == len(BASE_V2["accounts"])


def test_empty_accounts():
    v2 = {**BASE_V2, "accounts": {}}
    result = convert(v2)
    assert result["awsRoleArns"] == []
