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

from applications.globals.access import _user_from_request
from applications.programme_curriculum.models_student_management import (
    StudentBatchUpload,
    PhdStudentBatchUpload,
)
from .views_student_management import _decode_base64_image, _safe_decimal_conversion


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
        "hindi_name": rec.hindi_name or "",
        "photo": rec.photo.url if rec.photo else "",
        "signature": rec.signature.url if rec.signature else "",
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
    if not (rec.photo or ";base64," in photo_val):
        errors["photo"] = "Passport photo is required"
    if not (rec.signature or ";base64," in signature_val):
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
    rec.hindi_name = text("hindi_name")
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

    roll = str(rec.roll_number or user.username or "student")
    new_photo = _decode_base64_image(photo_val, roll + "_photo", max_kb=200)
    if new_photo is not None:
        if rec.photo:
            try:
                rec.photo.delete(save=False)
            except Exception:
                pass
        rec.photo = new_photo
    new_signature = _decode_base64_image(signature_val, roll + "_sign", max_kb=30)
    if new_signature is not None:
        if rec.signature:
            try:
                rec.signature.delete(save=False)
            except Exception:
                pass
        rec.signature = new_signature

    rec.profile_completed = True
    rec.save()
    return JsonResponse({"success": True, "message": "Profile completed successfully"})
