import os
import sys

# The exact Custom Runner logic built during the Scholarship implementation
RUNNER_CODE = """\"\"\"
runner.py — Custom Django test runner + CSV report generator.
Generates all 7 required CSV deliverable sheets.
\"\"\"

import csv
import os
import traceback
from datetime import datetime
from unittest import TestResult

import yaml
from django.test.runner import DiscoverRunner

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SPECS_DIR = os.path.join(_THIS_DIR, 'specs')
_REPORTS_DIR = os.path.join(_THIS_DIR, 'reports')

def _ensure_reports_dir():
    os.makedirs(_REPORTS_DIR, exist_ok=True)

def _load_yaml(filename):
    path = os.path.join(_SPECS_DIR, filename)
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

class ReportingTestResult(TestResult):
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

def _write_csv(filename, headers, rows):
    path = os.path.join(_REPORTS_DIR, filename)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

def generate_uc_test_design():
    specs = _load_yaml('use_cases.yaml')
    rows = []
    for uc in specs.get('use_cases', []):
        uc_id = uc.get('id', '')
        title = uc.get('title', '')
        for hp in uc.get('happy_paths', []):
            rows.append([uc_id, title, 'Happy Path', hp.get('scenario', ''), hp.get('preconditions', ''), hp.get('input_action', ''), hp.get('expected_result', '')])
        for ap in uc.get('alternate_paths', []):
            rows.append([uc_id, title, 'Alternate Path', ap.get('scenario', ''), ap.get('preconditions', ''), ap.get('input_action', ''), ap.get('expected_result', '')])
        for ex in uc.get('exception_paths', []):
            rows.append([uc_id, title, 'Exception', ex.get('scenario', ''), ex.get('preconditions', ''), ex.get('input_action', ''), ex.get('expected_result', '')])
    _write_csv('UC_Test_Design.csv', ['UC_ID', 'Title', 'Category', 'Scenario', 'Preconditions', 'Input/Action', 'Expected Result'], rows)
    return rows

def generate_br_test_design():
    specs = _load_yaml('business_rules.yaml')
    rows = []
    for br in specs.get('business_rules', []):
        br_id = br.get('id', '')
        title = br.get('title', '')
        for vt in br.get('valid_tests', []):
            rows.append([br_id, title, 'Valid', vt.get('input_action', ''), vt.get('expected_result', '')])
        for it in br.get('invalid_tests', []):
            rows.append([br_id, title, 'Invalid', it.get('input_action', ''), it.get('expected_result', '')])
    _write_csv('BR_Test_Design.csv', ['BR_ID', 'Title', 'Category', 'Input/Action', 'Expected Result'], rows)
    return rows

def generate_wf_test_design():
    specs = _load_yaml('workflows.yaml')
    rows = []
    for wf in specs.get('workflows', []):
        wf_id = wf.get('id', '')
        title = wf.get('title', '')
        for e2e in wf.get('e2e_tests', []):
            rows.append([wf_id, title, 'End-to-End', e2e.get('scenario', ''), e2e.get('expected_final_state', '')])
        for neg in wf.get('negative_tests', []):
            rows.append([wf_id, title, 'Negative', neg.get('scenario', ''), neg.get('expected_final_state', '')])
    _write_csv('WF_Test_Design.csv', ['WF_ID', 'Title', 'Category', 'Scenario', 'Expected Final State'], rows)
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
        rows.append([test_id, rec.get('scenario', ''), rec.get('input_action', ''), rec.get('expected_result', ''), actual, status_from_results, evidence, tester_name, timestamp])
    _write_csv('Test_Execution_Log.csv', ['Test_ID', 'Scenario', 'Input/Action', 'Expected Result', 'Actual Result', 'Status', 'Evidence', 'Tester', 'Timestamp'], rows)
    return rows

def generate_defect_log(records):
    rows = []
    for rec in records:
        if rec.get('outcome') in ('Fail', 'Error'):
            rows.append([rec.get('test_id', 'N/A'), rec.get('scenario', ''), rec.get('outcome', ''), str(rec.get('error', ''))[:500], 'Open', 'High' if rec.get('outcome') == 'Error' else 'Medium'])
    _write_csv('Defect_Log.csv', ['Test_ID', 'Scenario', 'Outcome', 'Error Details', 'Status', 'Severity'], rows)
    return rows

def _evaluate_status(items, pass_key, spec_type):
    if not items:
        return 'Not Implemented' if spec_type == 'UC' else 'Not Enforced' if spec_type == 'BR' else 'Missing'
    total = len(items)
    passed = sum(1 for i in items if i == 'Pass')
    failed = sum(1 for i in items if i in ('Fail', 'Error'))
    if passed == total:
        return 'Implemented Correctly' if spec_type == 'UC' else 'Enforced Correctly' if spec_type == 'BR' else 'Complete'
    elif passed > 0:
        return 'Partially Implemented' if spec_type == 'UC' else 'Partially Enforced' if spec_type == 'BR' else 'Partial'
    elif failed == total:
        return 'Incorrectly Implemented' if spec_type == 'UC' else 'Incorrectly Enforced' if spec_type == 'BR' else 'Incorrect'
    return 'Not Implemented' if spec_type == 'UC' else 'Not Enforced' if spec_type == 'BR' else 'Missing'

def generate_artifact_evaluation(records):
    uc_outcomes, br_outcomes, wf_outcomes = {}, {}, {}
    for rec in records:
        out = rec.get('outcome', 'N/A')
        if rec.get('uc_id'): uc_outcomes.setdefault(rec.get('uc_id'), []).append(out)
        if rec.get('br_id'): br_outcomes.setdefault(rec.get('br_id'), []).append(out)
        if rec.get('wf_id'): wf_outcomes.setdefault(rec.get('wf_id'), []).append(out)
    rows = []
    for uid, outs in sorted(uc_outcomes.items()): rows.append([uid, 'Use Case', _evaluate_status(outs, 'Pass', 'UC'), f"{outs.count('Pass')}/{len(outs)} passed"])
    for bid, outs in sorted(br_outcomes.items()): rows.append([bid, 'Business Rule', _evaluate_status(outs, 'Pass', 'BR'), f"{outs.count('Pass')}/{len(outs)} passed"])
    for wid, outs in sorted(wf_outcomes.items()): rows.append([wid, 'Workflow', _evaluate_status(outs, 'Pass', 'WF'), f"{outs.count('Pass')}/{len(outs)} passed"])
    _write_csv('Artifact_Evaluation.csv', ['Artifact_ID', 'Type', 'Status', 'Details'], rows)
    return rows

def generate_module_test_summary(records, uc_designs, br_designs, wf_designs):
    specs_uc, specs_br, specs_wf = _load_yaml('use_cases.yaml'), _load_yaml('business_rules.yaml'), _load_yaml('workflows.yaml')
    num_ucs, num_brs, num_wfs = len(specs_uc.get('use_cases', [])), len(specs_br.get('business_rules', [])), len(specs_wf.get('workflows', []))
    req_uc, req_br, req_wf = 3 * num_ucs, 2 * num_brs, 2 * num_wfs
    des_uc, des_br, des_wf = len(uc_designs), len(br_designs), len(wf_designs)
    total_exec = len(records)
    total_pass = sum(1 for r in records if r.get('outcome') == 'Pass')
    total_fail = sum(1 for r in records if r.get('outcome') in ('Fail', 'Error'))
    total_partial = sum(1 for r in records if any(res.get('status') == 'Partial' for res in r.get('results', [])))
    rows = [
        ['Total Use Cases', num_ucs], ['Total Business Rules', num_brs], ['Total Workflows', num_wfs],
        ['Required UC Tests', req_uc], ['Designed UC Tests', des_uc],
        ['Required BR Tests', req_br], ['Designed BR Tests', des_br],
        ['Required WF Tests', req_wf], ['Designed WF Tests', des_wf],
        ['UC Adequacy %', f"{(des_uc / req_uc * 100) if req_uc else 0:.1f}%"],
        ['BR Adequacy %', f"{(des_br / req_br * 100) if req_br else 0:.1f}%"],
        ['WF Adequacy %', f"{(des_wf / req_wf * 100) if req_wf else 0:.1f}%"],
        ['Total Tests Executed', total_exec], ['Total Pass', total_pass], ['Total Partial', total_partial], ['Total Fail', total_fail],
        ['Strict Pass Rate %', f"{(total_pass / total_exec * 100) if total_exec else 0:.1f}%"]
    ]
    _write_csv('Module_Test_Summary.csv', ['Metric', 'Value'], rows)
    return rows

class ReportingTestRunner(DiscoverRunner):
    def get_resultclass(self): return ReportingTestResult
    def run_suite(self, suite, **kwargs):
        result = ReportingTestResult()
        suite.run(result)
        return result
    def suite_result(self, suite, result, **kwargs):
        _ensure_reports_dir()
        uc, br, wf = generate_uc_test_design(), generate_br_test_design(), generate_wf_test_design()
        generate_execution_log(result.test_records, result.tester_name)
        generate_defect_log(result.test_records)
        generate_artifact_evaluation(result.test_records)
        generate_module_test_summary(result.test_records, uc, br, wf)
        print(f"\\nReports saved to: {_REPORTS_DIR}\\n")
        return super().suite_result(suite, result, **kwargs)
"""

CONFTEST_SCAFFOLD = """\"\"\"
conftest.py — Initial setup scaffold.
Customize this file with your module's specific logic.
\"\"\"
from django.test import TestCase

class BaseModuleTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass # Add your module setup here
"""

def generate_spec_scaffold(title):
    return f"""{title}:
  - id: "TODO-1"
    title: "Example Title"
"""

def create_init_file(path_dir):
    """Ensures directories act as python packages (prevents ntpath errors on windows test runner)."""
    if not os.path.exists(path_dir):
        return
    init_path = os.path.join(path_dir, '__init__.py')
    if not os.path.exists(init_path):
        with open(init_path, 'w') as f:
            f.write("# Package marker\\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python setup_tests.py <module_name>")
        sys.exit(1)
        
    module = sys.argv[1]
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'applications', module)
    
    if not os.path.exists(base_dir):
        print(f"Error: Module directory '{base_dir}' does not exist.")
        sys.exit(1)

    tests_dir = os.path.join(base_dir, 'tests')
    specs_dir = os.path.join(tests_dir, 'specs')

    # Create directories
    os.makedirs(specs_dir, exist_ok=True)

    # Secure the application tree (Crucial fix for Windows runner discovery bug)
    create_init_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'applications'))
    create_init_file(base_dir)
    create_init_file(tests_dir)
    create_init_file(specs_dir)

    # Scaffolding Files
    files_to_write = {
        os.path.join(tests_dir, 'runner.py'): RUNNER_CODE,
        os.path.join(tests_dir, 'conftest.py'): CONFTEST_SCAFFOLD,
        os.path.join(tests_dir, 'test_use_cases.py'): "# UC tests\\n",
        os.path.join(tests_dir, 'test_business_rules.py'): "# BR tests\\n",
        os.path.join(tests_dir, 'test_workflows.py'): "# WF tests\\n",
        os.path.join(specs_dir, 'use_cases.yaml'): generate_spec_scaffold('use_cases'),
        os.path.join(specs_dir, 'business_rules.yaml'): generate_spec_scaffold('business_rules'),
        os.path.join(specs_dir, 'workflows.yaml'): generate_spec_scaffold('workflows'),
    }

    for path, content in files_to_write.items():
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Created: {path}")
        else:
            print(f"Skipped (already exists): {path}")

    print(f"\\n✅ Successfully scaffolded testing framework for '{module}'!")

if __name__ == '__main__':
    main()
