"""Talk to Fusion_System_Administrator, so one login reaches every Fusion app.

This portal keeps its own token and its own session; the bridge only ADDS an
IAM session beside them, so a user who signs in here can walk into
Fusion-Integrated without signing in again.

Everything here fails soft. The IAM being unreachable must never stop somebody
logging into this portal — they simply do not get the extra modules until it is
back. Configuration is read from the environment so no settings file changes.
"""
import logging
import os

import requests

log = logging.getLogger("fusion.iam_bridge")

BASE_URL = os.environ.get("IAM_BASE_URL", "http://127.0.0.1:8001")
API_PREFIX = os.environ.get("IAM_API_PREFIX", "/api")
TIMEOUT = float(os.environ.get("IAM_TIMEOUT_SECONDS", "5"))

#: Must match what Fusion-Integrated reads, or the walk-across silently fails.
COOKIE_NAME = os.environ.get("IAM_AUTH_COOKIE_NAME", "auth_token")
#: Blank in development; set to .iiitdmj.ac.in in production.
COOKIE_DOMAIN = os.environ.get("IAM_AUTH_COOKIE_DOMAIN", "")
COOKIE_MAX_AGE = int(os.environ.get("IAM_AUTH_COOKIE_MAX_AGE", str(12 * 60 * 60)))
COOKIE_SECURE = os.environ.get("IAM_AUTH_COOKIE_SECURE", "0") == "1"


def _url(path):
    return f"{BASE_URL.rstrip('/')}{API_PREFIX.rstrip('/')}/{path.lstrip('/')}"


def mint_session(username, password):
    """A session token at the IAM for credentials this portal just accepted."""
    try:
        r = requests.post(_url("iam/v1/auth/login"),
                          json={"username": username, "password": password},
                          timeout=TIMEOUT)
        if r.status_code >= 400:
            log.warning("iam login returned %s for %s", r.status_code, username)
            return None
        return r.json().get("token")
    except (requests.RequestException, ValueError):
        log.exception("iam login failed")
        return None


def attach_session(response, token):
    """Put the IAM session beside this portal's own credential."""
    if not token:
        return response
    kwargs = {"max_age": COOKIE_MAX_AGE, "httponly": True,
              "samesite": "Lax", "secure": COOKIE_SECURE, "path": "/"}
    if COOKIE_DOMAIN:
        kwargs["domain"] = COOKIE_DOMAIN
    response.set_cookie(COOKIE_NAME, token, **kwargs)
    return response


def clear_session(response):
    kwargs = {"path": "/"}
    if COOKIE_DOMAIN:
        kwargs["domain"] = COOKIE_DOMAIN
    response.delete_cookie(COOKIE_NAME, **kwargs)
    return response


def _me(token):
    """The IAM's session payload, or None if it cannot be reached."""
    if not token:
        return None
    try:
        r = requests.get(_url("iam/v1/me"),
                         headers={"Authorization": f"Token {token}"},
                         timeout=TIMEOUT)
        return r.json() if r.status_code < 400 else None
    except (requests.RequestException, ValueError):
        log.exception("iam /me failed")
        return None



def plugged_modules(token):
    """(modules by designation, navigation) from the other services, in one call."""
    payload = _me(token) or {}
    return (dict(payload.get("modules_by_role") or {}),
            list(payload.get("navigation") or []))
