from applications.globals.models import Designation, ExtraInfo, HoldsDesignation


def _infer_user_type(user):
    designation_names = set(
        HoldsDesignation.objects.select_related("designation")
        .filter(working=user)
        .values_list("designation__name", flat=True)
    )

    if "student" in designation_names:
        return "student"
    if any(
        name in designation_names
        for name in ("faculty", "professor", "assistant_professor", "associate_professor")
    ):
        return "faculty"
    return "staff"


def _build_extrainfo_id(user):
    base = (user.username or f"user{user.pk}" or "user")[:20]
    candidate = base
    counter = 1

    while ExtraInfo.objects.filter(pk=candidate).exclude(user=user).exists():
        suffix = str(counter)
        candidate = f"{base[:20 - len(suffix)]}{suffix}"
        counter += 1

    return candidate


def ensure_initial_designation(user):
    if HoldsDesignation.objects.filter(working=user).exists():
        return

    designation, _ = Designation.objects.get_or_create(
        name="portal_user",
        defaults={
            "full_name": "Portal User",
            "type": "administrative",
        },
    )
    HoldsDesignation.objects.get_or_create(
        user=user,
        working=user,
        designation=designation,
    )


def ensure_extrainfo(user):
    ensure_initial_designation(user)

    extrainfo = ExtraInfo.objects.filter(user=user).first()
    if extrainfo:
        return extrainfo

    return ExtraInfo.objects.create(
        id=_build_extrainfo_id(user),
        user=user,
        user_type=_infer_user_type(user),
    )
