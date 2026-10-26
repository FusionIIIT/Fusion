"""
Student first-login profile-completion popup: GET the logged-in student's
record (frozen + prefilled editable fields) and POST the completed profile.
Data lives on StudentBatchUpload / PhdStudentBatchUpload (linked to the user
via create_user_account).
"""
import json
import re

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from applications.globals.access import _user_from_request
from applications.programme_curriculum.models_student_management import (
    StudentBatchUpload,
    PhdStudentBatchUpload,
)
from .views_student_management import (
    _decode_base64_blob, _student_image_url, _safe_decimal_conversion,
)
from .account_sync import sync_account_from_admission


# What a student may change on their own record. The rest comes from the
# admission file and only the academic section can correct it.
ALWAYS_EDITABLE = (
    "phone_number", "apaar_id", "father_occupation", "mother_occupation",
    "parent_email", "income_group", "income", "state", "resume_link",
)

# Left blank at admission, so the student may fill it in once and no more.
FILL_ONCE = (
    "aadhar_number", "hindi_name", "minority", "blood_group",
    "blood_group_remarks", "nationality", "country", "address",
    "father_mobile", "mother_mobile",
)

IMAGE_MAX_KB = {"photo": 200, "signature": 30}

# Only PG and PhD students are paid a stipend, so only they are asked for
# an account.
BANK_FIELDS = ("bank_name", "bank_account_no", "ifsc_code")


def _wants_bank_details(rec):
    if isinstance(rec, PhdStudentBatchUpload):
        return True
    return (getattr(rec, "programme_type", "") or "").lower() == "pg"


def _editable_fields(rec):
    filled = [f for f in FILL_ONCE if str(getattr(rec, f, "") or "").strip()]
    fields = list(ALWAYS_EDITABLE) + [f for f in FILL_ONCE if f not in filled]
    if _wants_bank_details(rec):
        fields += list(BANK_FIELDS)
    return fields


def _get_student_record(user):
    if user is None:
        return None
    return (
        StudentBatchUpload.objects.filter(user=user).first()
        or PhdStudentBatchUpload.objects.filter(user=user).first()
    )


def _serialize(rec):
    is_phd = isinstance(rec, PhdStudentBatchUpload)
    return {
        "profile_completed": rec.profile_completed,
        "is_phd": is_phd,
        "programme_type": "phd" if is_phd else getattr(rec, "programme_type", ""),
        # Frozen (read-only) fields
        "roll_number": rec.roll_number or "",
        "name": rec.name or "",
        "discipline": (rec.discipline if is_phd else rec.branch) or "",
        "specialization": "" if is_phd else (getattr(rec, "specialization", "") or ""),
        "gender": rec.gender or "",
        "category": rec.category or "",
        "father_name": rec.father_name or "",
        "mother_name": rec.mother_name or "",
        "date_of_birth": rec.date_of_birth.isoformat() if rec.date_of_birth else "",
        "admission_mode": (
            getattr(rec, "admission_type", "") if is_phd else getattr(rec, "admission_mode", "")
        )
        or "",
        # Editable fields (prefilled from DB)
        "aadhar_number": rec.aadhar_number or "",
        "apaar_id": rec.apaar_id or "",
        "hindi_name": rec.hindi_name or "",
        "photo": _student_image_url(rec, "photo"),
        "signature": _student_image_url(rec, "signature"),
        "minority": rec.minority or "",
        "phone_number": rec.phone_number or "",
        "parent_email": rec.parent_email or "",
        "father_occupation": rec.father_occupation or "",
        "mother_occupation": rec.mother_occupation or "",
        "father_mobile": rec.father_mobile or "",
        "mother_mobile": rec.mother_mobile or "",
        "blood_group": rec.blood_group or "",
        "blood_group_remarks": rec.blood_group_remarks or "",
        "country": rec.country or "",
        "nationality": rec.nationality or "",
        "income_group": rec.income_group or "",
        "income": str(rec.income) if rec.income is not None else "",
        "state": rec.state or "",
        "address": rec.address or "",
        "resume_link": rec.resume_link or "",
        "wants_bank_details": _wants_bank_details(rec),
        "bank_name": rec.bank_name or "",
        "bank_account_no": rec.bank_account_no or "",
        "ifsc_code": rec.ifsc_code or "",
        "editable": _editable_fields(rec),
    }


@csrf_exempt
@require_http_methods(["GET"])
def student_profile_completion(request):
    user = _user_from_request(request)
    if user is None:
        return JsonResponse({"success": False, "message": "Authentication required"}, status=401)
    rec = _get_student_record(user)
    if rec is None:
        return JsonResponse({"success": False, "message": "No student record found"}, status=404)
    return JsonResponse({"success": True, "data": _serialize(rec)})


@csrf_exempt
@require_http_methods(["POST", "PUT"])
def student_profile_image(request):
    """Replace the photo or the signature on its own, keeping the bytes as sent."""
    user = _user_from_request(request)
    if user is None:
        return JsonResponse({"success": False, "message": "Authentication required"}, status=401)
    rec = _get_student_record(user)
    if rec is None:
        return JsonResponse({"success": False, "message": "No student record found"}, status=404)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid request data"}, status=400)

    kind = (data.get("kind") or "photo").strip().lower()
    if kind not in IMAGE_MAX_KB:
        return JsonResponse({"success": False, "message": "Unknown image"}, status=400)

    max_kb = IMAGE_MAX_KB[kind]
    image = data.get("image") or data.get(kind) or ""
    if ";base64," not in image:
        return JsonResponse(
            {"success": False, "message": "Please choose a PNG or JPEG image"}, status=400)

    blob, mime = _decode_base64_blob(image, max_kb=max_kb)
    if blob is None:
        return JsonResponse(
            {"success": False,
             "message": "{} must be a PNG or JPEG of up to {} KB".format(
                 kind.capitalize(), max_kb)},
            status=400)

    setattr(rec, kind + "_blob", blob)
    setattr(rec, kind + "_mime", mime)
    rec.save(update_fields=[kind + "_blob", kind + "_mime"])
    return JsonResponse({"success": True, kind: _student_image_url(rec, kind)})


@csrf_exempt
@require_http_methods(["POST", "PUT"])
def student_profile_update(request):
    """Save the fields a student is allowed to change on their own record."""
    user = _user_from_request(request)
    if user is None:
        return JsonResponse({"success": False, "message": "Authentication required"}, status=401)
    rec = _get_student_record(user)
    if rec is None:
        return JsonResponse({"success": False, "message": "No student record found"}, status=404)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid request data"}, status=400)

    allowed = set(_editable_fields(rec))
    known = set(ALWAYS_EDITABLE) | set(FILL_ONCE) | set(BANK_FIELDS)
    submitted = {k: v for k, v in data.items() if k in known}
    refused = sorted(set(submitted) - allowed)
    if refused:
        def why(field):
            if field in BANK_FIELDS:
                return "Bank details are collected for PG and PhD students only"
            return "This field can no longer be changed here"

        return JsonResponse(
            {"success": False,
             "errors": {f: why(f) for f in refused},
             "message": "Some of those fields cannot be edited"},
            status=400)

    def text(field):
        value = submitted.get(field)
        return value.strip() if isinstance(value, str) else ("" if value is None else str(value))

    errors = {}
    for field, label in (("aadhar_number", "Aadhaar number"), ("apaar_id", "APAAR ID")):
        if field in submitted and text(field) and not re.fullmatch(r"\d{12}", text(field)):
            errors[field] = "{} must be exactly 12 digits".format(label)

    if "hindi_name" in submitted and text("hindi_name"):
        value = text("hindi_name")
        if not (re.search(r"[\u0900-\u097F]", value)
                and re.fullmatch(r"[\u0900-\u097F\u200c\u200d\s.'-]+", value)):
            errors["hindi_name"] = "Name (Hindi) must be written in Devanagari, not English"

    phone = text("phone_number") if "phone_number" in submitted else (rec.phone_number or "")
    father_mobile = (text("father_mobile") if "father_mobile" in submitted
                     else (rec.father_mobile or ""))
    mother_mobile = (text("mother_mobile") if "mother_mobile" in submitted
                     else (rec.mother_mobile or ""))
    if phone and phone in (father_mobile, mother_mobile):
        errors["phone_number"] = "Your mobile number must not match a parent's mobile number"
    for field in ("phone_number", "father_mobile", "mother_mobile"):
        if field in submitted and text(field) and not re.fullmatch(r"\d{10}", text(field)):
            errors[field] = "Enter a 10-digit mobile number"

    if "resume_link" in submitted and text("resume_link"):
        link = text("resume_link")
        if not re.match(r"https://(drive|docs)\.google\.com/", link):
            errors["resume_link"] = (
                "Paste a Google Drive or Google Docs link starting with https://")

    if "ifsc_code" in submitted:
        submitted["ifsc_code"] = text("ifsc_code").upper()
        if text("ifsc_code") and not re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", text("ifsc_code")):
            errors["ifsc_code"] = "IFSC must be 11 characters, like SBIN0001234"

    if "bank_account_no" in submitted and text("bank_account_no"):
        if not re.fullmatch(r"\d{9,18}", text("bank_account_no")):
            errors["bank_account_no"] = "Account number must be 9 to 18 digits"

    if "parent_email" in submitted and text("parent_email"):
        try:
            validate_email(text("parent_email"))
        except ValidationError:
            errors["parent_email"] = "Enter a valid email address"

    income_value = None
    if "income" in submitted:
        income_value = _safe_decimal_conversion(text("income") or None)
        if text("income") and income_value is None:
            errors["income"] = "Income must be a valid number"

    blood_group = text("blood_group") if "blood_group" in submitted else (rec.blood_group or "")
    blood_remarks = (text("blood_group_remarks") if "blood_group_remarks" in submitted
                     else (rec.blood_group_remarks or ""))
    if blood_group == "Other" and not blood_remarks:
        errors["blood_group_remarks"] = "Please specify the blood group"

    if errors:
        return JsonResponse(
            {"success": False, "errors": errors, "message": "Please fix the highlighted fields"},
            status=400)

    for field in submitted:
        setattr(rec, field, income_value if field == "income" else text(field))
    rec.save()
    sync_account_from_admission(rec)
    return JsonResponse({"success": True, "data": _serialize(rec),
                         "message": "Profile updated"})


@csrf_exempt
@require_http_methods(["POST", "PUT"])
def student_profile_completion_submit(request):
    user = _user_from_request(request)
    if user is None:
        return JsonResponse({"success": False, "message": "Authentication required"}, status=401)
    rec = _get_student_record(user)
    if rec is None:
        return JsonResponse({"success": False, "message": "No student record found"}, status=404)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid request data"}, status=400)

    def text(field):
        value = data.get(field)
        return value.strip() if isinstance(value, str) else (value or "")

    errors = {}
    required = {
        "aadhar_number": "Aadhaar number",
        "apaar_id": "APAAR ID",
        "hindi_name": "Name (Hindi)",
        "phone_number": "Mobile number",
        "blood_group": "Blood group",
        "country": "Country",
        "nationality": "Nationality",
        "income_group": "Income group",
        "income": "Income",
        "state": "State",
        "address": "Address",
    }
    for field, label in required.items():
        if not text(field):
            errors[field] = "{} is required".format(label)

    aadhar = str(text("aadhar_number"))
    if aadhar and not re.fullmatch(r"\d{12}", aadhar):
        errors["aadhar_number"] = "Aadhaar number must be exactly 12 digits"

    apaar = str(text("apaar_id"))
    if apaar and not re.fullmatch(r"\d{12}", apaar):
        errors["apaar_id"] = "APAAR ID must be exactly 12 digits"

    # The Hindi name has to be in Devanagari: the Latin spelling is already the
    # name field, so a repeat of it here carries nothing.
    hindi_name = text("hindi_name")
    if hindi_name and not (
        re.search(r"[\u0900-\u097F]", hindi_name)
        and re.fullmatch(r"[\u0900-\u097F\u200c\u200d\s.'-]+", hindi_name)
    ):
        errors["hindi_name"] = "Name (Hindi) must be written in Devanagari, not English"

    phone = str(text("phone_number"))
    father_mobile = str(text("father_mobile"))
    mother_mobile = str(text("mother_mobile"))
    if not father_mobile and not mother_mobile:
        errors["father_mobile"] = "At least one of father's or mother's mobile is required"
    if phone and phone in (father_mobile, mother_mobile):
        errors["phone_number"] = "Your mobile number must not match a parent's mobile number"

    income_value = _safe_decimal_conversion(text("income") or None)
    if text("income") and income_value is None:
        errors["income"] = "Income must be a valid number"

    photo_val = data.get("photo") or ""
    signature_val = data.get("signature") or ""
    if not (rec.photo_blob or rec.photo or ";base64," in photo_val):
        errors["photo"] = "Passport photo is required"
    if not (rec.signature_blob or rec.signature or ";base64," in signature_val):
        errors["signature"] = "Signature is required"

    blood_group = text("blood_group")
    blood_remarks = text("blood_group_remarks")
    if blood_group == "Other" and not blood_remarks:
        errors["blood_group_remarks"] = "Please specify the blood group"

    if errors:
        return JsonResponse(
            {"success": False, "errors": errors, "message": "Please fix the highlighted fields"},
            status=400,
        )

    rec.aadhar_number = aadhar
    rec.apaar_id = apaar
    rec.hindi_name = hindi_name
    rec.phone_number = phone
    rec.blood_group = blood_group
    rec.blood_group_remarks = blood_remarks
    rec.country = text("country")
    rec.nationality = text("nationality")
    rec.income_group = text("income_group")
    rec.income = income_value
    rec.state = text("state")
    rec.address = text("address")
    rec.minority = text("minority")
    rec.parent_email = text("parent_email")
    rec.father_occupation = text("father_occupation")
    rec.mother_occupation = text("mother_occupation")
    rec.father_mobile = father_mobile
    rec.mother_mobile = mother_mobile

    _photo_blob, _photo_mime = _decode_base64_blob(photo_val, max_kb=200)
    if _photo_blob is not None:
        rec.photo_blob = _photo_blob
        rec.photo_mime = _photo_mime
    _sign_blob, _sign_mime = _decode_base64_blob(signature_val, max_kb=30)
    if _sign_blob is not None:
        rec.signature_blob = _sign_blob
        rec.signature_mime = _sign_mime

    rec.profile_completed = True
    rec.save()
    sync_account_from_admission(rec)
    return JsonResponse({"success": True, "message": "Profile completed successfully"})
