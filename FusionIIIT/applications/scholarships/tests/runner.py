"""
runner.py — Custom Django test runner + CSV report generator for SPACS module.

Generates all 7 required CSV deliverable sheets:
  1. Module_Test_Summary.csv
  2. UC_Test_Design.csv
  3. BR_Test_Design.csv
  4. WF_Test_Design.csv
  5. Test_Execution_Log.csv
  6. Defect_Log.csv
  7. Artifact_Evaluation.csv

Usage:
    python manage.py test applications.scholarships.tests -v 2 \
        --testrunner=applications.scholarships.tests.runner.ReportingTestRunner
"""

import csv
import os
import traceback
from datetime import datetime
from unittest import TestResult

import yaml
from django.test.runner import DiscoverRunner


# ── Paths ──────────────────────────────────────────────────────────────────────

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SPECS_DIR = os.path.join(_THIS_DIR, 'specs')
_REPORTS_DIR = os.path.join(_THIS_DIR, 'reports2')


def _ensure_reports_dir():
    os.makedirs(_REPORTS_DIR, exist_ok=True)


def _load_yaml(filename):
    path = os.path.join(_SPECS_DIR, filename)
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


# ── Custom TestResult ──────────────────────────────────────────────────────────

class ReportingTestResult(TestResult):
    """Collects per-test metadata for CSV generation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_records = []
        self.tester_name = os.environ.get('TESTER_NAME', 'Tester')

    def _extract_metadata(self, test):
        return {
            'test_id': getattr(test, '_test_id', '') or '',
            'uc_id': getattr(test, '_uc_id', '') or '',
            'br_id': getattr(test, '_br_id', '') or '',
            'wf_id': getattr(test, '_wf_id', '') or '',
            'test_category': getattr(test, '_test_category', '') or '',
            'scenario': getattr(test, '_scenario', '') or '',
            'preconditions': getattr(test, '_preconditions', '') or '',
            'input_action': getattr(test, '_input_action', '') or '',
            'expected_result': getattr(test, '_expected_result', '') or '',
            'results': list(getattr(test, '_results', [])),
            'steps': list(getattr(test, '_steps', [])),
        }

    def addSuccess(self, test):
        super().addSuccess(test)
        meta = self._extract_metadata(test)
        meta['outcome'] = 'Pass'
        meta['error'] = ''
        self.test_records.append(meta)

    def addFailure(self, test, err):
        super().addFailure(test, err)
        meta = self._extract_metadata(test)
        meta['outcome'] = 'Fail'
        meta['error'] = ''.join(traceback.format_exception(*err))
        self.test_records.append(meta)

    def addError(self, test, err):
        super().addError(test, err)
        meta = self._extract_metadata(test)
        meta['outcome'] = 'Error'
        meta['error'] = ''.join(traceback.format_exception(*err))
        self.test_records.append(meta)


# ── CSV generators ─────────────────────────────────────────────────────────────

def _write_csv(filename, headers, rows):
    path = os.path.join(_REPORTS_DIR, filename)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"  ✓ {filename} ({len(rows)} rows)")


def generate_uc_test_design():
    specs = _load_yaml('use_cases.yaml')
    rows = []
    for uc in specs.get('use_cases', []):
        uc_id = uc.get('id', '')
        title = uc.get('title', '')
        for hp in uc.get('happy_paths', []):
            rows.append([uc_id, title, 'Happy Path', hp.get('scenario', ''),
                         hp.get('preconditions', ''), hp.get('input_action', ''),
                         hp.get('expected_result', '')])
        for ap in uc.get('alternate_paths', []):
            rows.append([uc_id, title, 'Alternate Path', ap.get('scenario', ''),
                         ap.get('preconditions', ''), ap.get('input_action', ''),
                         ap.get('expected_result', '')])
        for ex in uc.get('exception_paths', []):
            rows.append([uc_id, title, 'Exception', ex.get('scenario', ''),
                         ex.get('preconditions', ''), ex.get('input_action', ''),
                         ex.get('expected_result', '')])
    _write_csv('UC_Test_Design.csv',
               ['UC_ID', 'Title', 'Category', 'Scenario', 'Preconditions',
                'Input/Action', 'Expected Result'],
               rows)
    return rows


def generate_br_test_design():
    specs = _load_yaml('business_rules.yaml')
    rows = []
    for br in specs.get('business_rules', []):
        br_id = br.get('id', '')
        title = br.get('title', '')
        for vt in br.get('valid_tests', []):
            rows.append([br_id, title, 'Valid', vt.get('input_action', ''),
                         vt.get('expected_result', '')])
        for it in br.get('invalid_tests', []):
            rows.append([br_id, title, 'Invalid', it.get('input_action', ''),
                         it.get('expected_result', '')])
    _write_csv('BR_Test_Design.csv',
               ['BR_ID', 'Title', 'Category', 'Input/Action', 'Expected Result'],
               rows)
    return rows


def generate_wf_test_design():
    specs = _load_yaml('workflows.yaml')
    rows = []
    for wf in specs.get('workflows', []):
        wf_id = wf.get('id', '')
        title = wf.get('title', '')
        for e2e in wf.get('e2e_tests', []):
            rows.append([wf_id, title, 'End-to-End',
                         e2e.get('scenario', ''),
                         e2e.get('expected_final_state', '')])
        for neg in wf.get('negative_tests', []):
            rows.append([wf_id, title, 'Negative',
                         neg.get('scenario', ''),
                         neg.get('expected_final_state', '')])
    _write_csv('WF_Test_Design.csv',
               ['WF_ID', 'Title', 'Category', 'Scenario', 'Expected Final State'],
               rows)
    return rows


def generate_execution_log(records, tester_name):
    rows = []
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for rec in records:
        test_id = rec.get('test_id', 'N/A')
        outcome = rec.get('outcome', 'N/A')
        results = rec.get('results', [])
        actual = results[0].get('actual', '') if results else ''
        evidence = results[0].get('evidence', '') if results else ''
        status_from_results = results[0].get('status', outcome) if results else outcome
        rows.append([
            test_id,
            rec.get('scenario', ''),
            rec.get('input_action', ''),
            rec.get('expected_result', ''),
            actual,
            status_from_results,
            evidence,
            tester_name,
            timestamp,
        ])
    _write_csv('Test_Execution_Log.csv',
               ['Test_ID', 'Scenario', 'Input/Action', 'Expected Result',
                'Actual Result', 'Status', 'Evidence', 'Tester', 'Timestamp'],
               rows)
    return rows


def generate_defect_log(records):
    rows = []
    for rec in records:
        if rec.get('outcome') in ('Fail', 'Error'):
            rows.append([
                rec.get('test_id', 'N/A'),
                rec.get('scenario', ''),
                rec.get('outcome', ''),
                rec.get('error', '')[:500],
                'Open',
                'High' if rec.get('outcome') == 'Error' else 'Medium',
            ])
    _write_csv('Defect_Log.csv',
               ['Test_ID', 'Scenario', 'Outcome', 'Error Details',
                'Status', 'Severity'],
               rows)
    return rows


def _evaluate_status(items, pass_key, spec_type):
    """Evaluate final artifact status based on test outcomes."""
    if not items:
        return 'Not Implemented' if spec_type == 'UC' else \
               'Not Enforced' if spec_type == 'BR' else 'Missing'

    total = len(items)
    passed = sum(1 for i in items if i == 'Pass')
    failed = sum(1 for i in items if i in ('Fail', 'Error'))

    if passed == total:
        if spec_type == 'UC':
            return 'Implemented Correctly'
        elif spec_type == 'BR':
            return 'Enforced Correctly'
        else:
            return 'Complete'
    elif passed > 0:
        if spec_type == 'UC':
            return 'Partially Implemented'
        elif spec_type == 'BR':
            return 'Partially Enforced'
        else:
            return 'Partial'
    elif failed == total:
        if spec_type == 'UC':
            return 'Incorrectly Implemented'
        elif spec_type == 'BR':
            return 'Incorrectly Enforced'
        else:
            return 'Incorrect'
    else:
        if spec_type == 'UC':
            return 'Not Implemented'
        elif spec_type == 'BR':
            return 'Not Enforced'
        else:
            return 'Missing'


def generate_artifact_evaluation(records):
    # Group outcomes by artifact ID
    uc_outcomes = {}
    br_outcomes = {}
    wf_outcomes = {}

    for rec in records:
        outcome = rec.get('outcome', 'N/A')
        uc_id = rec.get('uc_id', '')
        br_id = rec.get('br_id', '')
        wf_id = rec.get('wf_id', '')

        if uc_id:
            uc_outcomes.setdefault(uc_id, []).append(outcome)
        if br_id:
            br_outcomes.setdefault(br_id, []).append(outcome)
        if wf_id:
            wf_outcomes.setdefault(wf_id, []).append(outcome)

    rows = []
    for uid, outcomes in sorted(uc_outcomes.items()):
        status = _evaluate_status(outcomes, 'Pass', 'UC')
        rows.append([uid, 'Use Case', status,
                     f"{outcomes.count('Pass')}/{len(outcomes)} passed"])

    for bid, outcomes in sorted(br_outcomes.items()):
        status = _evaluate_status(outcomes, 'Pass', 'BR')
        rows.append([bid, 'Business Rule', status,
                     f"{outcomes.count('Pass')}/{len(outcomes)} passed"])

    for wid, outcomes in sorted(wf_outcomes.items()):
        status = _evaluate_status(outcomes, 'Pass', 'WF')
        rows.append([wid, 'Workflow', status,
                     f"{outcomes.count('Pass')}/{len(outcomes)} passed"])

    _write_csv('Artifact_Evaluation.csv',
               ['Artifact_ID', 'Type', 'Status', 'Details'],
               rows)
    return rows


def generate_module_test_summary(records, uc_designs, br_designs, wf_designs):
    specs_uc = _load_yaml('use_cases.yaml')
    specs_br = _load_yaml('business_rules.yaml')
    specs_wf = _load_yaml('workflows.yaml')

    num_ucs = len(specs_uc.get('use_cases', []))
    num_brs = len(specs_br.get('business_rules', []))
    num_wfs = len(specs_wf.get('workflows', []))

    req_uc = 3 * num_ucs
    req_br = 2 * num_brs
    req_wf = 2 * num_wfs

    des_uc = len(uc_designs)
    des_br = len(br_designs)
    des_wf = len(wf_designs)

    total_executed = len(records)
    total_pass = sum(1 for r in records if r.get('outcome') == 'Pass')
    total_partial = sum(1 for r in records
                        if any(res.get('status') == 'Partial'
                               for res in r.get('results', [])))
    total_fail = sum(1 for r in records if r.get('outcome') in ('Fail', 'Error'))

    uc_adeq = f"{(des_uc / req_uc * 100) if req_uc else 0:.1f}%"
    br_adeq = f"{(des_br / req_br * 100) if req_br else 0:.1f}%"
    wf_adeq = f"{(des_wf / req_wf * 100) if req_wf else 0:.1f}%"
    pass_rate = f"{(total_pass / total_executed * 100) if total_executed else 0:.1f}%"

    rows = [
        ['Total Use Cases', num_ucs],
        ['Total Business Rules', num_brs],
        ['Total Workflows', num_wfs],
        ['Required UC Tests', req_uc],
        ['Designed UC Tests', des_uc],
        ['Required BR Tests', req_br],
        ['Designed BR Tests', des_br],
        ['Required WF Tests', req_wf],
        ['Designed WF Tests', des_wf],
        ['UC Adequacy %', uc_adeq],
        ['BR Adequacy %', br_adeq],
        ['WF Adequacy %', wf_adeq],
        ['Total Tests Executed', total_executed],
        ['Total Pass', total_pass],
        ['Total Partial', total_partial],
        ['Total Fail', total_fail],
        ['Strict Pass Rate %', pass_rate],
    ]
    _write_csv('Module_Test_Summary.csv', ['Metric', 'Value'], rows)
    return rows


# ── Custom Test Runner ─────────────────────────────────────────────────────────

class ReportingTestRunner(DiscoverRunner):
    """Runs tests + auto-generates all 7 CSV reports."""

    def get_resultclass(self):
        return ReportingTestResult

    def run_suite(self, suite, **kwargs):
        result = ReportingTestResult()
        suite.run(result)
        return result

    def suite_result(self, suite, result, **kwargs):
        # Generate reports after all tests complete
        _ensure_reports_dir()
        print(f"\n{'=' * 60}")
        print("SPACS Module — Generating CSV Reports")
        print(f"{'=' * 60}")

        uc_designs = generate_uc_test_design()
        br_designs = generate_br_test_design()
        wf_designs = generate_wf_test_design()
        generate_execution_log(result.test_records, result.tester_name)
        generate_defect_log(result.test_records)
        generate_artifact_evaluation(result.test_records)
        generate_module_test_summary(
            result.test_records, uc_designs, br_designs, wf_designs)

        print(f"{'=' * 60}")
        print(f"Reports saved to: {_REPORTS_DIR}")
        print(f"{'=' * 60}\n")

        return super().suite_result(suite, result, **kwargs)
