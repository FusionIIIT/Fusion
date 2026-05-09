"""
runner.py - Custom Test Runner + Automated Report Generator

When tests are run with:
    python manage.py test applications.notifications_extension.tests --testrunner=applications.notifications_extension.tests.runner.ReportingTestRunner

This runner:
  1. Runs all tests normally
  2. Collects results from every test method
  3. Reads YAML spec files for test design documentation
  4. Generates ALL 7 CSV report sheets automatically

Output files (in tests/reports/):
  - Module_Test_Summary.csv     (Sheet 1)
  - UC_Test_Design.csv          (Sheet 2)
  - BR_Test_Design.csv          (Sheet 3)
  - WF_Test_Design.csv          (Sheet 4)
  - Test_Execution_Log.csv      (Sheet 5)
  - Defect_Log.csv              (Sheet 6)
  - Artifact_Evaluation.csv     (Sheet 7)
"""

import csv
import os
import sys
import traceback
import unittest
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from django.test.runner import DiscoverRunner


TESTS_DIR = Path(__file__).parent
SPECS_DIR = TESTS_DIR / "specs"
REPORTS_DIR = TESTS_DIR / "reports"


class ReportCollectingResult(unittest.TextTestResult):
    """Extended TestResult that captures metadata from test methods for reports."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_records = []
        self.defects = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self._record_test(test, "Pass")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._record_test(test, "Fail", err)

    def addError(self, test, err):
        super().addError(test, err)
        self._record_test(test, "Fail", err)

    def _record_test(self, test, status, err=None):
        record = {
            "test_id": getattr(test, "_test_id", test.id().split(".")[-1]),
            "source_type": self._detect_source_type(test),
            "source_id": (getattr(test, "_uc_id", "")
                          or getattr(test, "_br_id", "")
                          or getattr(test, "_wf_id", "")),
            "test_category": getattr(test, "_test_category", ""),
            "scenario": getattr(test, "_scenario", test.shortDescription() or ""),
            "preconditions": getattr(test, "_preconditions", ""),
            "input_action": getattr(test, "_input_action", ""),
            "expected_result": getattr(test, "_expected_result", ""),
            "actual_result": getattr(
                test, "_actual_result",
                self._format_error(err) if err else "Test passed",
            ),
            "status": getattr(test, "_status", status) or status,
            "evidence": getattr(test, "_evidence", ""),
            "tester": os.environ.get("TESTER_NAME", "Automated"),
            "test_class": test.__class__.__name__,
            "test_method": test._testMethodName,
        }
        self.test_records.append(record)

        if record["status"] in ("Fail", "Partial"):
            error_desc = self._format_error(err) if err else record["actual_result"]
            self.defects.append({
                "defect_id": f"DEF-{len(self.defects) + 1:03d}",
                "related_test_id": record["test_id"],
                "related_artifact": record["source_id"],
                "severity": "High" if record["status"] == "Fail" else "Medium",
                "description": (error_desc or "")[:500],
                "suggested_fix": "Investigate and fix the failing condition",
            })

    def _detect_source_type(self, test):
        class_name = test.__class__.__name__
        module_name = test.__class__.__module__
        if "use_case" in module_name or class_name.startswith("TestUC"):
            return "UC"
        if "business_rule" in module_name or class_name.startswith("TestBR"):
            return "BR"
        if "workflow" in module_name or class_name.startswith("TestWF"):
            return "WF"
        return "Other"

    def _format_error(self, err):
        if err:
            return "".join(traceback.format_exception(*err))[:500]
        return ""


class ReportingTestRunner(DiscoverRunner):
    """Django test runner that generates the 7 CSV reports after the run."""

    def get_resultclass(self):
        return ReportCollectingResult

    def run_suite(self, suite, **kwargs):
        result = super().run_suite(suite, **kwargs)
        self._generate_reports(result)
        return result

    def _generate_reports(self, result):
        if not hasattr(result, "test_records"):
            print("\nNo test records collected. Skipping report generation.")
            return

        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        print("\n" + "=" * 60)
        print("GENERATING TEST REPORTS")
        print("=" * 60)

        records = result.test_records
        defects = result.defects

        uc_specs = self._load_yaml_safe("use_cases.yaml", "use_cases")
        br_specs = self._load_yaml_safe("business_rules.yaml", "business_rules")
        wf_specs = self._load_yaml_safe("workflows.yaml", "workflows")

        self._gen_sheet2_uc_design(uc_specs)
        self._gen_sheet3_br_design(br_specs)
        self._gen_sheet4_wf_design(wf_specs)
        self._gen_sheet5_execution_log(records)
        self._gen_sheet6_defect_log(defects)
        self._gen_sheet7_artifact_eval(records, uc_specs, br_specs, wf_specs)
        self._gen_sheet1_summary(records, uc_specs, br_specs, wf_specs)

        print("\n" + "=" * 60)
        print(f"All 7 reports generated in: {REPORTS_DIR}")
        print("=" * 60 + "\n")

    def _load_yaml_safe(self, filename, key):
        try:
            import yaml
            filepath = SPECS_DIR / filename
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    return data.get(key, []) if data else []
        except Exception as exc:
            print(f"Warning: could not load {filename}: {exc}")
        return []

    def _write_csv(self, filename, headers, rows):
        filepath = REPORTS_DIR / filename
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in rows:
                writer.writerow(row)
        print(f"  Wrote {filename} ({len(rows)} rows)")

    # Sheet 1: Module Test Summary
    def _gen_sheet1_summary(self, records, uc_specs, br_specs, wf_specs):
        num_ucs, num_brs, num_wfs = len(uc_specs), len(br_specs), len(wf_specs)
        required_uc = 3 * num_ucs
        required_br = 2 * num_brs
        required_wf = 2 * num_wfs

        uc_records = [r for r in records if r["source_type"] == "UC"]
        br_records = [r for r in records if r["source_type"] == "BR"]
        wf_records = [r for r in records if r["source_type"] == "WF"]

        designed_uc = len(uc_records)
        designed_br = len(br_records)
        designed_wf = len(wf_records)

        total_executed = len(records)
        total_pass = sum(1 for r in records if r["status"] == "Pass")
        total_partial = sum(1 for r in records if r["status"] == "Partial")
        total_fail = sum(1 for r in records if r["status"] == "Fail")

        def pct(n, d):
            return f"{(n / d * 100):.1f}%" if d > 0 else "N/A"

        rows = [
            ["Total Use Cases", num_ucs],
            ["Total Business Rules", num_brs],
            ["Total Workflows", num_wfs],
            ["Required UC Tests", required_uc],
            ["Designed UC Tests", designed_uc],
            ["Required BR Tests", required_br],
            ["Designed BR Tests", designed_br],
            ["Required WF Tests", required_wf],
            ["Designed WF Tests", designed_wf],
            ["UC Adequacy %", pct(designed_uc, required_uc)],
            ["BR Adequacy %", pct(designed_br, required_br)],
            ["WF Adequacy %", pct(designed_wf, required_wf)],
            ["Total Tests Executed", total_executed],
            ["Total Pass", total_pass],
            ["Total Partial", total_partial],
            ["Total Fail", total_fail],
            ["Strict Pass Rate %", pct(total_pass, total_executed)],
        ]
        self._write_csv("Module_Test_Summary.csv", ["Metric", "Value"], rows)

    # Sheet 2: UC Test Design
    def _gen_sheet2_uc_design(self, uc_specs):
        headers = ["Test ID", "UC ID", "Test Category", "Scenario",
                   "Preconditions", "Input / Action", "Expected Result"]
        rows = []
        for uc in uc_specs:
            uc_id = uc["id"]
            for i, hp in enumerate(uc.get("happy_paths", []), 1):
                rows.append([f"{uc_id}-HP-{i:02d}", uc_id, "Happy Path",
                             hp.get("scenario", ""), hp.get("preconditions", ""),
                             hp.get("input_action", ""), hp.get("expected_result", "")])
            for i, ap in enumerate(uc.get("alternate_paths", []), 1):
                rows.append([f"{uc_id}-AP-{i:02d}", uc_id, "Alternate Path",
                             ap.get("scenario", ""), ap.get("preconditions", ""),
                             ap.get("input_action", ""), ap.get("expected_result", "")])
            for i, ep in enumerate(uc.get("exception_paths", []), 1):
                rows.append([f"{uc_id}-EX-{i:02d}", uc_id, "Exception",
                             ep.get("scenario", ""), ep.get("preconditions", ""),
                             ep.get("input_action", ""), ep.get("expected_result", "")])
        self._write_csv("UC_Test_Design.csv", headers, rows)

    # Sheet 3: BR Test Design
    def _gen_sheet3_br_design(self, br_specs):
        headers = ["Test ID", "BR ID", "Test Category", "Input / Action", "Expected Result"]
        rows = []
        for br in br_specs:
            br_id = br["id"]
            for i, vt in enumerate(br.get("valid_tests", []), 1):
                rows.append([f"{br_id}-V-{i:02d}", br_id, "Valid",
                             vt.get("input_action", ""), vt.get("expected_result", "")])
            for i, it in enumerate(br.get("invalid_tests", []), 1):
                rows.append([f"{br_id}-I-{i:02d}", br_id, "Invalid",
                             it.get("input_action", ""), it.get("expected_result", "")])
        self._write_csv("BR_Test_Design.csv", headers, rows)

    # Sheet 4: WF Test Design
    def _gen_sheet4_wf_design(self, wf_specs):
        headers = ["Test ID", "WF ID", "Test Category", "Scenario", "Expected Final State"]
        rows = []
        for wf in wf_specs:
            wf_id = wf["id"]
            for i, e2e in enumerate(wf.get("e2e_tests", []), 1):
                rows.append([f"{wf_id}-E2E-{i:02d}", wf_id, "End-to-End",
                             e2e.get("scenario", ""), e2e.get("expected_final_state", "")])
            for i, neg in enumerate(wf.get("negative_tests", []), 1):
                rows.append([f"{wf_id}-NEG-{i:02d}", wf_id, "Negative",
                             neg.get("scenario", ""), neg.get("expected_final_state", "")])
            for i, ext in enumerate(wf.get("exit_tests", []), 1):
                rows.append([f"{wf_id}-EXIT-{i:02d}", wf_id, "Exit",
                             ext.get("scenario", ""), ext.get("expected_final_state", "")])
        self._write_csv("WF_Test_Design.csv", headers, rows)

    # Sheet 5: Execution Log
    def _gen_sheet5_execution_log(self, records):
        headers = ["Test ID", "Source Type", "Source ID", "Expected Result",
                   "Actual Result", "Status", "Evidence", "Tester"]
        rows = []
        for r in records:
            rows.append([r["test_id"], r["source_type"], r["source_id"],
                         r["expected_result"], r["actual_result"],
                         r["status"], r["evidence"], r["tester"]])
        self._write_csv("Test_Execution_Log.csv", headers, rows)

    # Sheet 6: Defect Log
    def _gen_sheet6_defect_log(self, defects):
        headers = ["Defect ID", "Related Test ID", "Related Artifact",
                   "Severity", "Description", "Suggested Fix"]
        rows = [[d["defect_id"], d["related_test_id"], d["related_artifact"],
                 d["severity"], d["description"], d["suggested_fix"]] for d in defects]
        self._write_csv("Defect_Log.csv", headers, rows)

    # Sheet 7: Artifact Evaluation
    def _gen_sheet7_artifact_eval(self, records, uc_specs, br_specs, wf_specs):
        headers = ["Artifact ID", "Artifact Type", "Tests", "Pass",
                   "Partial", "Fail", "Final Status", "Remarks"]
        rows = []

        def evaluate(spec_list, type_code, pass_label, partial_label,
                      fail_label, missing_label):
            for spec in spec_list:
                sid = spec["id"]
                tests = [r for r in records if r["source_id"] == sid]
                p = sum(1 for t in tests if t["status"] == "Pass")
                pa = sum(1 for t in tests if t["status"] == "Partial")
                f = sum(1 for t in tests if t["status"] == "Fail")
                total = len(tests)
                if total == 0:
                    status = missing_label
                elif f == 0 and pa == 0:
                    status = pass_label
                elif p > 0:
                    status = partial_label
                else:
                    status = fail_label
                remarks = f"{p}/{total} passed" if total else "No tests executed"
                rows.append([sid, type_code, total, p, pa, f, status, remarks])

        evaluate(uc_specs, "UC",
                 "Implemented Correctly", "Partially Implemented",
                 "Incorrectly Implemented", "Not Implemented")
        evaluate(br_specs, "BR",
                 "Enforced Correctly", "Partially Enforced",
                 "Incorrectly Enforced", "Not Enforced")
        evaluate(wf_specs, "WF",
                 "Complete", "Partial", "Incorrect", "Missing")

        self._write_csv("Artifact_Evaluation.csv", headers, rows)
