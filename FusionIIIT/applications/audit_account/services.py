from .models import Request, RequestStatus, RequestType


def create_draft_request(data, user):
    """
    Create a draft request
    """
    request_type = data.get('type', '')
    if isinstance(request_type, str):
        request_type = request_type.strip().upper()

    if request_type not in RequestType.values:
        raise ValueError("Invalid request type. Use EXPENSE or VOUCHER.")

    request_obj = Request.objects.create(
        type=request_type,
        amount=data.get('amount'),
        department=data.get('department'),
        description=data.get('description', ''),
        status=RequestStatus.DRAFT,
        created_by=user.id,
        created_by_user=user,
    )
    return request_obj


def submit_request(request_obj):
    """
    Submit a request (change status from DRAFT to SUBMITTED)
    """
    request_obj.status = RequestStatus.SUBMITTED
    request_obj.save()
    return request_obj


def update_request_status(request_obj, new_status):
    """
    Update request status for finance/dean workflow
    """
    status_value = new_status.strip().upper()
    if status_value not in RequestStatus.values:
        raise ValueError("Invalid status value.")

    request_obj.status = status_value
    request_obj.save()
    return request_obj