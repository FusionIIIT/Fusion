from django.http import JsonResponse


def json_response(*, success, message=None, data=None, status_code=200):
    payload = {"success": success}
    if message is not None:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return JsonResponse(payload, status=status_code, safe=not isinstance(data, list))
