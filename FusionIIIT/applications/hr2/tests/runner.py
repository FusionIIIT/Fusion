import csv
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml
from django.test.runner import DiscoverRunner


REPORTS_DIRNAME = "reports"


@dataclass
class ExecutionRecord:
    test_id: str
    artifact_id: Optional[str]
    artifact_type: str
    category: str
    scenario: str
    preconditions: str
    input_action: str
    expected_result: str
    status: str
    message: str
    evidence: str
    steps: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DefectRecord:
    test_id: str
    artifact_id: Optional[str]
    artifact_type: str
    status: str
    error: str


class ReportStore:
    def __init__(self) -> None:
        self.execution_log: List[ExecutionRecord] = []
        self.defect_log: List[DefectRecord] = []

    def add_execution(
        self,
        test_id: str,
        artifact_id: Optional[str],
        artifact_type: str,
        category: str,
        scenario: str,
        preconditions: str,
        input_action: str,
        expected_result: str,
        status: str,
        message: str,
        evidence: str,
        steps: List[Dict[str, Any]],
    ) -> None:
        self.execution_log.append(
            ExecutionRecord(
                test_id=test_id,
                artifact_id=artifact_id,
                artifact_type=artifact_type,
                category=category,
                scenario=scenario,
                preconditions=preconditions,
                input_action=input_action,
                expected_result=expected_result,
                status=status,
                message=message,
                evidence=evidence,
                steps=steps,
            )
        )

    def add_defect(
        self, test_id: str, artifact_id: Optional[str], artifact_type: str, status: str, error: str
    ) -> None:
        self.defect_log.append(
            DefectRecord(
                test_id=test_id,
                artifact_id=artifact_id,
                artifact_type=artifact_type,
                status=status,
                error=error,
            )
        )


REPORT_STORE = ReportStore()


def _specs_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "specs")


def _reports_dir() -> str:
    return os.path.join(os.path.dirname(__file__), REPORTS_DIRNAME)


def _load_yaml(filename: str) -> Dict[str, Any]:
    path = os.path.join(_specs_dir(), filename)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_specs() -> Dict[str, Any]:
    return {
        "use_cases": _load_yaml("use_cases.yaml").get("use_cases", []),
        "business_rules": _load_yaml("business_rules.yaml").get("business_rules", []),
        "workflows": _load_yaml("workflows.yaml").get("workflows", []),
    }


def _write_csv(path: str, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _uc_design_rows(use_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for uc in use_cases:
        for test_type, key in (
            ("Happy Path", "happy_paths"),
            ("Alternate Path", "alternate_paths"),
            ("Exception", "exception_paths"),
        ):
            for item in uc.get(key, []):
                rows.append(
                    {
                        "uc_id": uc.get("id"),
                        "uc_title": uc.get("title"),
                        "test_type": test_type,
                        "scenario": item.get("scenario"),
                        "preconditions": item.get("preconditions"),
                        "input_action": item.get("input_action"),
                        "expected_result": item.get("expected_result"),
                    }
                )
    return rows


def _br_design_rows(business_rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for br in business_rules:
        for test_type, key in (("Valid", "valid_tests"), ("Invalid", "invalid_tests")):
            for item in br.get(key, []):
                rows.append(
                    {
                        "br_id": br.get("id"),
                        "br_title": br.get("title"),
                        "test_type": test_type,
                        "input_action": item.get("input_action"),
                        "expected_result": item.get("expected_result"),
                    }
                )
    return rows


def _wf_design_rows(workflows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for wf in workflows:
        for test_type, key in (("End-to-End", "e2e_tests"), ("Negative", "negative_tests")):
            for item in wf.get(key, []):
                rows.append(
                    {
                        "wf_id": wf.get("id"),
                        "wf_title": wf.get("title"),
                        "test_type": test_type,
                        "scenario": item.get("scenario"),
                        "expected_final_state": item.get("expected_final_state"),
                    }
                )
    return rows


def _artifact_status(records: List[ExecutionRecord]) -> str:
    if not records:
        return "Not Implemented"
    statuses = {record.status for record in records}
    if statuses == {"Pass"}:
        return "Implemented Correctly"
    if "Pass" in statuses and ("Fail" in statuses or "Partial" in statuses):
        return "Partially Implemented"
    if "Fail" in statuses and "Pass" not in statuses:
        return "Incorrectly Implemented"
    return "Partially Implemented"


def _evaluation_rows(
    artifact_type: str, artifacts: List[Dict[str, Any]], executions: List[ExecutionRecord]
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for artifact in artifacts:
        artifact_id = artifact.get("id")
        relevant = [record for record in executions if record.artifact_id == artifact_id]
        status = _artifact_status(relevant)
        rows.append(
            {
                "artifact_type": artifact_type,
                "artifact_id": artifact_id,
                "artifact_title": artifact.get("title"),
                "status": status,
            }
        )
    return rows


def _summary_rows(specs: Dict[str, Any], executions: List[ExecutionRecord]) -> List[Dict[str, Any]]:
    uc_count = len(specs["use_cases"])
    br_count = len(specs["business_rules"])
    wf_count = len(specs["workflows"])

    required_uc = uc_count * 3
    required_br = br_count * 2
    required_wf = wf_count * 2

    designed_uc = len([record for record in executions if record.artifact_type == "UC"])
    designed_br = len([record for record in executions if record.artifact_type == "BR"])
    designed_wf = len([record for record in executions if record.artifact_type == "WF"])

    total_executed = len(executions)
    total_pass = len([record for record in executions if record.status == "Pass"])
    total_partial = len([record for record in executions if record.status == "Partial"])
    total_fail = len([record for record in executions if record.status == "Fail"])

    def adequacy(designed: int, required: int) -> float:
        if required == 0:
            return 0.0
        return round((designed / required) * 100, 2)

    strict_pass_rate = 0.0
    if total_executed:
        strict_pass_rate = round((total_pass / total_executed) * 100, 2)

    return [
        {"Metric": "Total Use Cases", "Value": uc_count},
        {"Metric": "Total Business Rules", "Value": br_count},
        {"Metric": "Total Workflows", "Value": wf_count},
        {"Metric": "Required UC Tests", "Value": required_uc},
        {"Metric": "Designed UC Tests", "Value": designed_uc},
        {"Metric": "Required BR Tests", "Value": required_br},
        {"Metric": "Designed BR Tests", "Value": designed_br},
        {"Metric": "Required WF Tests", "Value": required_wf},
        {"Metric": "Designed WF Tests", "Value": designed_wf},
        {"Metric": "UC Adequacy %", "Value": adequacy(designed_uc, required_uc)},
        {"Metric": "BR Adequacy %", "Value": adequacy(designed_br, required_br)},
        {"Metric": "WF Adequacy %", "Value": adequacy(designed_wf, required_wf)},
        {"Metric": "Total Tests Executed", "Value": total_executed},
        {"Metric": "Total Pass", "Value": total_pass},
        {"Metric": "Total Partial", "Value": total_partial},
        {"Metric": "Total Fail", "Value": total_fail},
        {"Metric": "Strict Pass Rate %", "Value": strict_pass_rate},
        {"Metric": "Generated At", "Value": datetime.now().isoformat()},
        {"Metric": "Tester Name", "Value": os.getenv("TESTER_NAME", "")},
    ]


def _execution_rows(executions: List[ExecutionRecord]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for record in executions:
        rows.append(
            {
                "test_id": record.test_id,
                "artifact_type": record.artifact_type,
                "artifact_id": record.artifact_id,
                "category": record.category,
                "scenario": record.scenario,
                "preconditions": record.preconditions,
                "input_action": record.input_action,
                "expected_result": record.expected_result,
                "status": record.status,
                "message": record.message,
                "evidence": record.evidence,
                "steps": record.steps,
            }
        )
    return rows


def _defect_rows(defects: List[DefectRecord]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for record in defects:
        rows.append(
            {
                "test_id": record.test_id,
                "artifact_type": record.artifact_type,
                "artifact_id": record.artifact_id,
                "status": record.status,
                "error": record.error,
            }
        )
    return rows


class ReportingTestRunner(DiscoverRunner):
    def run_suite(self, suite, **kwargs):
        result = super().run_suite(suite, **kwargs)
        self._write_reports()
        return result

    def _write_reports(self) -> None:
        specs = load_specs()
        reports_dir = _reports_dir()

        uc_design = _uc_design_rows(specs["use_cases"])
        br_design = _br_design_rows(specs["business_rules"])
        wf_design = _wf_design_rows(specs["workflows"])

        summary_rows = _summary_rows(specs, REPORT_STORE.execution_log)
        execution_rows = _execution_rows(REPORT_STORE.execution_log)
        defect_rows = _defect_rows(REPORT_STORE.defect_log)
        evaluation_rows = (
            _evaluation_rows("UC", specs["use_cases"], REPORT_STORE.execution_log)
            + _evaluation_rows("BR", specs["business_rules"], REPORT_STORE.execution_log)
            + _evaluation_rows("WF", specs["workflows"], REPORT_STORE.execution_log)
        )

        _write_csv(
            os.path.join(reports_dir, "Module_Test_Summary.csv"),
            summary_rows,
            ["Metric", "Value"],
        )
        _write_csv(
            os.path.join(reports_dir, "UC_Test_Design.csv"),
            uc_design,
            [
                "uc_id",
                "uc_title",
                "test_type",
                "scenario",
                "preconditions",
                "input_action",
                "expected_result",
            ],
        )
        _write_csv(
            os.path.join(reports_dir, "BR_Test_Design.csv"),
            br_design,
            ["br_id", "br_title", "test_type", "input_action", "expected_result"],
        )
        _write_csv(
            os.path.join(reports_dir, "WF_Test_Design.csv"),
            wf_design,
            ["wf_id", "wf_title", "test_type", "scenario", "expected_final_state"],
        )
        _write_csv(
            os.path.join(reports_dir, "Test_Execution_Log.csv"),
            execution_rows,
            [
                "test_id",
                "artifact_type",
                "artifact_id",
                "category",
                "scenario",
                "preconditions",
                "input_action",
                "expected_result",
                "status",
                "message",
                "evidence",
                "steps",
            ],
        )
        _write_csv(
            os.path.join(reports_dir, "Defect_Log.csv"),
            defect_rows,
            ["test_id", "artifact_type", "artifact_id", "status", "error"],
        )
        _write_csv(
            os.path.join(reports_dir, "Artifact_Evaluation.csv"),
            evaluation_rows,
            ["artifact_type", "artifact_id", "artifact_title", "status"],
        )
