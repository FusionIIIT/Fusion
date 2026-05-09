from .common import *
import json

from django.db.backends.signals import connection_created


SECRET_KEY = "test-secret-key"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "test_db.sqlite3"),
        "TEST": {
            "SERIALIZE": False,
        },
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
SILENCED_SYSTEM_CHECKS = [
    "fields.E180",
    "fields.W122",
    "fields.W342",
]


def _sqlite_json_valid(value):
    if value is None:
        return 0
    try:
        json.loads(value)
        return 1
    except (TypeError, ValueError):
        return 0


def _register_sqlite_json_functions(sender, connection, **kwargs):
    if connection.vendor != "sqlite":
        return
    connection.connection.create_function("JSON_VALID", 1, _sqlite_json_valid)


connection_created.connect(
    _register_sqlite_json_functions,
    dispatch_uid="fusion_test_sqlite_json_valid",
)
