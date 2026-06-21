"""
Test settings for the placement_cell test suite (and any other app tests).

Why this file exists
--------------------
The project's historical migrations do not apply cleanly on a fresh database
(e.g. ``programme_curriculum.0026`` references ``course_registration`` before it
exists). Django's test runner builds the test database by replaying every
migration, so tests would fail during DB setup for reasons unrelated to the code
under test.

To keep the test suite reliable now and in the future, we disable migrations for
the test database and let Django create the schema directly from the current
model state. This is a standard, well-supported pattern and is also much faster.

It does NOT touch the production settings (common/development/production.py).

Run the placement suite (list the modules explicitly -- ``applications`` has no
``__init__.py`` so unittest package discovery cannot introspect it)::

    python manage.py test \
        applications.placement_cell.tests.test_placement_api \
        applications.placement_cell.tests.test_use_cases \
        applications.placement_cell.tests.test_business_rules \
        applications.placement_cell.tests.test_workflows \
        applications.placement_cell.tests.test_module \
        --settings=test_settings
"""

from Fusion.settings.development import *  # noqa: F401,F403


class DisableMigrations:
    """Make every app create its schema from models instead of migrations."""

    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Faster, deterministic tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
DEBUG = False
