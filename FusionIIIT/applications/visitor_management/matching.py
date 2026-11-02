"""Identity normalisation and registry matching.

The frozen baseline leaves the blacklist matching algorithm unresolved
(ISS-VMS-016 case-insensitivity, ISS-VMS-017 "name variations where possible").
This module is the single place that decides what counts as a match, so the
institution can swap the rule without touching any workflow code.

Current conservative rule:
  * a strong identifier match is enough: normalised ID-document number, phone
    (last 10 digits) or e-mail;
  * a registry entry that carries only a name matches on the normalised name;
  * name variations (ISS-VMS-017) are NOT attempted.
"""

import re
import unicodedata

from django.db.models import Q


def normalise_name(value):
    if not value:
        return ""
    value = unicodedata.normalize("NFKC", value)
    return " ".join(value.casefold().split())


def normalise_doc(value):
    if not value:
        return ""
    return re.sub(r"[^0-9A-Za-z]", "", value).upper()


def normalise_phone(value):
    if not value:
        return ""
    digits = re.sub(r"\D", "", value)
    return digits[-10:]


def normalise_email(value):
    return (value or "").strip().casefold()


def identity_keys(full_name="", id_doc_number="", phone="", email=""):
    return {
        "name_key": normalise_name(full_name),
        "id_doc_key": normalise_doc(id_doc_number),
        "phone_key": normalise_phone(phone),
        "email_key": normalise_email(email),
    }


def identity_q(keys, prefix=""):
    """Q object matching any strong identifier, or name-only entries on the name."""
    query = Q(pk__in=[])
    if keys.get("id_doc_key"):
        query |= Q(**{prefix + "id_doc_key": keys["id_doc_key"]})
    if keys.get("phone_key"):
        query |= Q(**{prefix + "phone_key": keys["phone_key"]})
    if keys.get("email_key"):
        query |= Q(**{prefix + "email_key": keys["email_key"]})
    if keys.get("name_key"):
        query |= Q(**{
            prefix + "name_key": keys["name_key"],
            prefix + "id_doc_key": "",
            prefix + "phone_key": "",
            prefix + "email_key": "",
        })
    return query


def strong_identity_q(keys, prefix=""):
    """Q object for strong identifiers only (pre-authorisation / VIP / duplicate checks)."""
    query = Q(pk__in=[])
    if keys.get("id_doc_key"):
        query |= Q(**{prefix + "id_doc_key": keys["id_doc_key"]})
    if keys.get("phone_key"):
        query |= Q(**{prefix + "phone_key": keys["phone_key"]})
    return query


def keys_for(obj):
    return {
        "name_key": getattr(obj, "name_key", "") or normalise_name(getattr(obj, "full_name", "")),
        "id_doc_key": getattr(obj, "id_doc_key", "") or normalise_doc(getattr(obj, "id_doc_number", "")),
        "phone_key": getattr(obj, "phone_key", "") or normalise_phone(getattr(obj, "phone", "")),
        "email_key": getattr(obj, "email_key", "") or normalise_email(getattr(obj, "email", "")),
    }
