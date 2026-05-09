from datetime import date

from .models import Special_request


SPECIAL_REQUEST_TYPE_ALIASES = {
    'medical': 'medical',
    'illness': 'medical',
    'medical_note': 'medical',
    'medical-proof': 'medical',
    'event': 'event',
}

REQUEST_STATUS_FLOW = {
    'request': {
        'pending': 'pending',
        'accept': 'accept',
        'reject': 'reject',
        'escalated': 'escalated',
    },
    'numeric': {
        'pending': '1',
        'accept': '2',
        'reject': '0',
        'escalated': '3',
    },
}

REQUEST_STATUS_ALIASES = {
    'pending': 'pending',
    '1': 'pending',
    'accept': 'accept',
    'accepted': 'accept',
    'approve': 'accept',
    'approved': 'accept',
    '2': 'accept',
    'reject': 'reject',
    'rejected': 'reject',
    'decline': 'reject',
    'declined': 'reject',
    '0': 'reject',
    'escalate': 'escalated',
    'escalated': 'escalated',
    '3': 'escalated',
}


def normalize_special_request_type(value, default=None):
    if value in (None, ''):
        return default
    return SPECIAL_REQUEST_TYPE_ALIASES.get(str(value).strip().lower(), default)


def normalize_request_status(value, status_kind):
    if value in (None, ''):
        return None

    normalized = REQUEST_STATUS_ALIASES.get(str(value).strip().lower())
    if not normalized:
        return None
    return REQUEST_STATUS_FLOW[status_kind][normalized]


def get_request_status_key(value, status_kind):
    for key, flow_value in REQUEST_STATUS_FLOW[status_kind].items():
        if flow_value == value:
            return key
    return None


def is_escalated_request_status(value, status_kind):
    return value == REQUEST_STATUS_FLOW[status_kind]['escalated']


def get_special_request_document(request):
    files = getattr(request, 'FILES', None)
    if not files:
        return None
    return (
        files.get('supporting_document')
        or files.get('medical_proof')
        or files.get('proof_document')
    )


def validate_special_food_request(student, start_date, end_date, request_type,
                                  supporting_document, exclude_request_id=None):
    if start_date < date.today():
        return 'Special food requests must be submitted before the start date.'

    if end_date < start_date:
        return 'End date must be on or after start date.'

    queryset = Special_request.objects.filter(student_id=student)
    if exclude_request_id:
        queryset = queryset.exclude(id=exclude_request_id)

    overlap = queryset.exclude(status='0').filter(
        start_date__lte=end_date,
        end_date__gte=start_date,
    ).exists()
    if overlap:
        return 'A special food request already exists for the selected dates.'

    semester = getattr(student, 'curr_semester_no', None) or 1
    current_semester_requests = queryset.filter(
        semester=semester
    ).exclude(status='0').count()
    if current_semester_requests >= 3:
        return 'Special food request limit exceeded. Maximum 3 requests are allowed per semester.'

    if request_type == 'medical' and not supporting_document:
        return 'Medical proof is required for illness-based special food requests.'

    return None
