#!/usr/bin/env python
"""
Verify test framework was created successfully
"""
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

test_files = [
    'applications/globals/tests/__init__.py',
    'applications/globals/tests/conftest.py',
    'applications/globals/tests/runner.py',
    'applications/globals/tests/test_use_cases.py',
    'applications/globals/tests/test_business_rules.py',
    'applications/globals/tests/test_workflows.py',
    'applications/globals/tests/specs/use_cases.yaml',
    'applications/globals/tests/specs/business_rules.yaml',
    'applications/globals/tests/specs/workflows.yaml',
    'Fusion/settings/test.py',
]

print("=" * 80)
print("Dashboard Module Test Framework Verification")
print("=" * 80)

all_exist = True
for test_file in test_files:
    exists = os.path.isfile(test_file)
    status = "✓" if exists else "✗"
    print(f"{status} {test_file}")
    if not exists:
        all_exist = False

print("\n" + "=" * 80)
print("Test File Counts:")
print("=" * 80)

# Count test cases in test_use_cases.py
use_case_file = 'applications/globals/tests/test_use_cases.py'
if os.path.isfile(use_case_file):
    with open(use_case_file, 'r', encoding='utf-8') as f:
        content = f.read()
        uc_count = content.count('def test_')
        print(f"✓ Use Case Tests: {uc_count} test methods found")

# Count test cases in test_business_rules.py
br_file = 'applications/globals/tests/test_business_rules.py'
if os.path.isfile(br_file):
    with open(br_file, 'r', encoding='utf-8') as f:
        content = f.read()
        br_count = content.count('def test_')
        print(f"✓ Business Rule Tests: {br_count} test methods found")

# Count test cases in test_workflows.py
wf_file = 'applications/globals/tests/test_workflows.py'
if os.path.isfile(wf_file):
    with open(wf_file, 'r', encoding='utf-8') as f:
        content = f.read()
        wf_count = content.count('def test_')
        print(f"✓ Workflow Tests: {wf_count} test methods found")

print("\n" + "=" * 80)
print("Summary:")
print("=" * 80)
if all_exist:
    print(f"✓ All {len(test_files)} framework files created successfully!")
    print(f"✓ Total test methods expected: {60 + 28 + 18} (60 UC + 28 BR + 18 WF)")
    print("\nTo run the tests, execute:")
    print("  python run_tests.py")
    print("\nOr from command line:")
    print("  python manage.py test applications.globals.tests -v 2 --testrunner=applications.globals.tests.runner.ReportingTestRunner")
else:
    print("✗ Some test framework files are missing!")
    sys.exit(1)

print("\n" + "=" * 80)
