"""Shared fixtures. `stub_iam` replaces the IAM client with an in-memory fake,
so the suite runs with no network and no Fusion_System_Administrator."""
import sys

import pytest

from fusion_auth import client as iam_client
from fusion_auth.client import IamSession, UserRef
from fusion_auth.principal import Principal


class FakeIam:
    """Mirrors IamClient exactly. If the real client grows a method, add it
    here too — a fake that has drifted is worse than no fake."""

    def __init__(self, session=None, users=None, standings=None):
        self.session, self.users = session, users or {}
        #: Override to make the identity service disagree with the projection.
        self.employees = None
        self.standings = standings or {}
        self.calls = []
        self.login_result = "tok-123"      # override per test
        self.login_error = None
        self.standings_error = None
        self.directory_error = None
        self.directory = {"count": 0, "limit": 50, "offset": 0, "results": []}
        self.filters = {"disciplines": [], "batch_years": [], "programmes": []}

    def login(self, username, password):
        self.calls.append(("login", username))
        if self.login_error:
            raise self.login_error
        return self.login_result

    def logout(self, auth_token):
        self.calls.append(("logout", auth_token))

    def resolve_session(self, *, auth_token=None, cookies=None):
        self.calls.append(("resolve_session", auth_token))
        return self.session

    def get_users(self, user_ids):
        ids = list(user_ids)
        self.calls.append(("get_users", tuple(sorted(ids))))
        return {i: self.users[i] for i in ids if i in self.users}

    def search_users(self, q="", kind=None, limit=25):
        return list(self.users.values())[:limit]

    def employee_page(self, *, limit=500, offset=0):
        rows = self._employees()
        return {"count": len(rows), "limit": limit, "offset": offset,
                "results": rows[offset:offset + limit]}

    def count_employees(self):
        return len(self._employees())

    def iter_employees(self, *, page_size=500):
        yield from self._employees()

    def _employees(self):
        """Whoever the test put in `users` who is not a student."""
        if self.employees is not None:
            return list(self.employees)
        from modules.directory.models import UserRef
        return list(UserRef.objects.filter(
            kind__in=("faculty", "staff"), is_active=True))

    def academic_directory(self, **filters):
        self.calls.append(("academic_directory", tuple(sorted(filters.items()))))
        if self.directory_error:
            raise self.directory_error
        return self.directory

    def academic_filters(self):
        self.calls.append(("academic_filters", ()))
        if self.directory_error:
            raise self.directory_error
        return self.filters

    def get_academic_standings(self, user_ids):
        """A student absent from `standings` has no declared result, which is
        what the eligibility engine must fail closed on."""
        ids = list(user_ids)
        self.calls.append(("get_academic_standings", tuple(sorted(ids))))
        if self.standings_error:
            raise self.standings_error
        return {i: self.standings[i] for i in ids if i in self.standings}


def make_session(user_id=1001, permissions=(), modules=(), kind="student",
                 roles=("student",), active_role="student"):
    return IamSession(
        user_id=user_id, username=f"u{user_id}", display_name=f"User {user_id}",
        kind=kind, active_role=active_role, roles=tuple(roles),
        permissions=frozenset(permissions), modules=tuple(modules),
    )


def make_principal(**kw):
    return Principal.from_session(make_session(**kw))


@pytest.fixture(autouse=True)
def _clear_throttle_state():
    """Throttle counters live in the cache and would otherwise carry from one
    test into the next — the sixth request of a run failing wherever it landed."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def stub_iam(monkeypatch):
    fake = FakeIam()

    def _install(session=None, users=None):
        fake.session = session
        fake.users = users or {}
        # `from ... import get_client` binds the name in every importer, so
        # patching the source alone lets the real client leak through. A
        # hand-maintained list goes stale silently; sys.modules does not.
        patched = 0
        for mod in list(sys.modules.values()):
            if mod is None:
                continue
            name = getattr(mod, "__name__", "")
            if not name.startswith(("fusion_auth", "modules", "core", "config")):
                continue
            if getattr(mod, "get_client", None) is not None:
                monkeypatch.setattr(mod, "get_client", lambda: fake)
                patched += 1
        monkeypatch.setattr(iam_client, "get_client", lambda: fake)
        assert patched, "no get_client bindings were found to patch"
        return fake

    _install()
    return _install


@pytest.fixture
def user_ref():
    def _make(user_id, name="Asha Verma", kind="student", discipline="CSE"):
        return UserRef(user_id=user_id, username=f"u{user_id}", display_name=name,
                       kind=kind, discipline=discipline)
    return _make
