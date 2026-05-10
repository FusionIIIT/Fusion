from .models import Request


def get_all_requests():
    """
    Get all requests
    """
    return Request.objects.all()


def get_request_by_id(request_id):
    """
    Get a request by ID
    """
    return Request.objects.get(id=request_id)