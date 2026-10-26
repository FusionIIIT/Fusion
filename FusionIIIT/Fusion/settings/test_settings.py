# Test settings: build the test schema directly from the current models instead
# of replaying historical migrations. Several legacy migrations reference tables
# via raw SQL before those tables exist, so they cannot run against an empty
# database (the dev DB is loaded from a prod dump, not migrated from zero).
from Fusion.settings.development import *  # noqa: F401,F403


class _DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = _DisableMigrations()
