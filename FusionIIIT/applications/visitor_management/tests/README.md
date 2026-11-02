# VMS test suite

Self-contained Django `TestCase` suite, same layout as `placement_cell/tests`. Uses `FusionIIIT/test_settings.py`
(migrations disabled, schema built from models) against PostgreSQL. Requires PyYAML.

```bash
cd FusionIIIT
python manage.py test \
    applications.visitor_management.tests.test_use_cases \
    applications.visitor_management.tests.test_business_rules \
    applications.visitor_management.tests.test_workflows \
    applications.visitor_management.tests.test_api \
    --settings=test_settings
```

| File | Covers |
|---|---|
| `specs/*.yaml` | Generated from the frozen v1.3 UC/BR/WF documents: 39 UCs, 47 BRs, 30 workflows with all 116 STT rows |
| `test_use_cases.py` | Every active UC: happy, alternate and exception path (UC-001 to UC-040, UC-029 retired) |
| `test_business_rules.py` | Every BR: one valid and one invalid case; catalog check that no BR lacks a test class |
| `test_workflows.py` | STT traceability (every row mapped to code), all 23 basis workflows end-to-end plus a negative case each |
| `test_api.py` | URL wiring, auth boundaries, credential hiding in staff views, integration-key endpoints |
| `conftest.py` | Campus fixture (zones, gates), one user per role, visit/pass helpers |

Expected: all tests pass. The same-day-urgent tests skip themselves if run within 30 minutes of midnight.
