from convert import convert

BASE_V2 = {
    "defaults": {"roleName": "CloudWatchLogsRole"},
    "teams": [
        {
            "name": "compute",
            "namespaces": ["AWS/EC2"],
            "accounts": {
                "123456789012": {"regions": ["us-west-2"]},
                "345678901234": {"regions": ["eu-west-1"]},
            },
        },
        {
            "name": "serverless",
            "namespaces": ["AWS/Lambda"],
            "accounts": {
                "234567890123": {"regions": ["us-west-2"]},
            },
        },
    ],
}


def test_top_level_keys():
    result = convert(BASE_V2)
    assert set(result.keys()) == {"awsRegions", "awsNamespaces", "awsRoleArns"}


def test_regions_derived_from_all_teams():
    result = convert(BASE_V2)
    assert set(result["awsRegions"]) == {"us-west-2", "eu-west-1"}


def test_namespaces_derived_from_all_teams():
    result = convert(BASE_V2)
    assert set(result["awsNamespaces"]) == {"AWS/EC2", "AWS/Lambda"}


def test_regions_and_namespaces_are_sorted():
    result = convert(BASE_V2)
    assert result["awsRegions"] == sorted(result["awsRegions"])
    assert result["awsNamespaces"] == sorted(result["awsNamespaces"])


def test_regions_and_namespaces_deduplicated():
    v2 = {
        **BASE_V2,
        "teams": [
            {
                "name": "t1",
                "namespaces": ["AWS/EC2"],
                "accounts": {"123456789012": {"regions": ["us-west-2"]}},
            },
            {
                "name": "t2",
                "namespaces": ["AWS/EC2"],
                "accounts": {"234567890123": {"regions": ["us-west-2"]}},
            },
        ],
    }
    result = convert(v2)
    assert result["awsRegions"] == ["us-west-2"]
    assert result["awsNamespaces"] == ["AWS/EC2"]


def test_role_count_equals_total_accounts():
    result = convert(BASE_V2)
    total_accounts = sum(len(t["accounts"]) for t in BASE_V2["teams"])
    assert len(result["awsRoleArns"]) == total_accounts


def test_role_is_single_item_list():
    result = convert(BASE_V2)
    for entry in result["awsRoleArns"]:
        assert isinstance(entry["role"], list)
        assert len(entry["role"]) == 1


def test_arn_constructed_from_default_role_name():
    result = convert(BASE_V2)
    arns = [e["role"][0] for e in result["awsRoleArns"]]
    assert "arn:aws:iam::123456789012:role/CloudWatchLogsRole" in arns
    assert "arn:aws:iam::234567890123:role/CloudWatchLogsRole" in arns
    assert "arn:aws:iam::345678901234:role/CloudWatchLogsRole" in arns


def test_namespaces_come_from_team():
    result = convert(BASE_V2)
    by_arn = {e["role"][0]: e for e in result["awsRoleArns"]}
    assert by_arn["arn:aws:iam::123456789012:role/CloudWatchLogsRole"]["namespaces"] == ["AWS/EC2"]
    assert by_arn["arn:aws:iam::234567890123:role/CloudWatchLogsRole"]["namespaces"] == ["AWS/Lambda"]


def test_regions_come_from_account():
    result = convert(BASE_V2)
    by_arn = {e["role"][0]: e for e in result["awsRoleArns"]}
    assert by_arn["arn:aws:iam::123456789012:role/CloudWatchLogsRole"]["regions"] == ["us-west-2"]
    assert by_arn["arn:aws:iam::345678901234:role/CloudWatchLogsRole"]["regions"] == ["eu-west-1"]


def test_team_role_name_override():
    v2 = {
        **BASE_V2,
        "teams": [
            {
                "name": "compute",
                "namespaces": ["AWS/EC2"],
                "roleName": "CustomRole",
                "accounts": {"123456789012": {"regions": ["us-west-2"]}},
            },
        ],
    }
    result = convert(v2)
    assert result["awsRoleArns"][0]["role"][0] == "arn:aws:iam::123456789012:role/CustomRole"


def test_team_without_role_name_uses_default():
    v2 = {
        **BASE_V2,
        "teams": [
            {
                "name": "compute",
                "namespaces": ["AWS/EC2"],
                "accounts": {"123456789012": {"regions": ["us-west-2"]}},
            },
        ],
    }
    result = convert(v2)
    assert result["awsRoleArns"][0]["role"][0] == "arn:aws:iam::123456789012:role/CloudWatchLogsRole"


def test_empty_teams():
    v2 = {**BASE_V2, "teams": []}
    result = convert(v2)
    assert result["awsRoleArns"] == []
    assert result["awsRegions"] == []
    assert result["awsNamespaces"] == []
