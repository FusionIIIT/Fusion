import csv
from pathlib import Path

import yaml


BASE_DIR = Path(__file__).resolve().parent
SPECS_DIR = BASE_DIR / "specs"
REPORTS_DIR = BASE_DIR / "reports"


def _load_yaml(filename):
    path = SPECS_DIR / filename
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _write_csv(path, headers, rows):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def _collect_design_rows(items, item_id_key, scenario_keys):
    rows = []
    for item in items:
        item_id = item.get("id", "")
        item_name = item.get("name", "")
        endpoint = item.get("endpoint", "")
        method = item.get("method", "")
        description = item.get("description", "")
        scenarios = item.get("scenarios", {})
        for scenario_key in scenario_keys:
            scenario = scenarios.get(scenario_key, {})
            if not scenario:
                continue
            rows.append(
                {
                    "test_id": scenario.get("_test_id", ""),
                    item_id_key: scenario.get("_{}_id".format(item_id_key.split("_")[0]), item_id),
                    "name": item_name,
                    "scenario": scenario.get("_scenario", ""),
                    "expected_result": scenario.get("_expected_result", ""),
                    "endpoint": endpoint,
                    "method": method,
                    "description": description,
                }
            )
    return rows


def generate_reports():
    use_cases = _load_yaml("use_cases.yaml").get("use_cases", [])
    business_rules = _load_yaml("business_rules.yaml").get("business_rules", [])
    workflows = _load_yaml("workflows.yaml").get("workflows", [])

    uc_rows = _collect_design_rows(
        use_cases,
        "uc_id",
        ["happy_path", "alternate_path", "exception_path"],
    )
    br_rows = _collect_design_rows(
        business_rules,
        "br_id",
        ["valid", "invalid"],
    )
    wf_rows = _collect_design_rows(
        workflows,
        "wf_id",
        ["end_to_end", "negative"],
    )

    summary_rows = [
        {"artifact": "Use Cases", "count": len(uc_rows)},
        {"artifact": "Business Rules", "count": len(br_rows)},
        {"artifact": "Workflows", "count": len(wf_rows)},
        {"artifact": "Total Tests Designed", "count": len(uc_rows) + len(br_rows) + len(wf_rows)},
    ]

    _write_csv(
        REPORTS_DIR / "Module_Test_Summary.csv",
        ["artifact", "count"],
        summary_rows,
    )
    _write_csv(
        REPORTS_DIR / "UC_Test_Design.csv",
        ["test_id", "uc_id", "name", "scenario", "expected_result", "endpoint", "method", "description"],
        uc_rows,
    )
    _write_csv(
        REPORTS_DIR / "BR_Test_Design.csv",
        ["test_id", "br_id", "name", "scenario", "expected_result", "endpoint", "method", "description"],
        br_rows,
    )
    _write_csv(
        REPORTS_DIR / "WF_Test_Design.csv",
        ["test_id", "wf_id", "name", "scenario", "expected_result", "endpoint", "method", "description"],
        wf_rows,
    )
    _write_csv(
        REPORTS_DIR / "Test_Execution_Log.csv",
        ["test_id", "status", "executed_at", "notes"],
        [],
    )
    _write_csv(
        REPORTS_DIR / "Defect_Log.csv",
        ["defect_id", "test_id", "severity", "summary", "status"],
        [],
    )
    _write_csv(
        REPORTS_DIR / "Artifact_Evaluation.csv",
        ["artifact", "status", "remarks"],
        [
            {"artifact": "use_cases.yaml", "status": "present", "remarks": ""},
            {"artifact": "business_rules.yaml", "status": "present", "remarks": ""},
            {"artifact": "workflows.yaml", "status": "present", "remarks": ""},
            {"artifact": "test_use_cases.py", "status": "present", "remarks": ""},
            {"artifact": "test_business_rules.py", "status": "present", "remarks": ""},
            {"artifact": "test_workflows.py", "status": "present", "remarks": ""},
        ],
    )


if __name__ == "__main__":
    generate_reports()
