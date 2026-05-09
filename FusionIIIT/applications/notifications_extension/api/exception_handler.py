"""
Global DRF exception handler — returns consistent {error, detail} envelope
for any unhandled exception and logs server errors.
"""

import logging

from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Wrap DRF's default handler to:
    - add a consistent 'error' field
    - log server errors (5xx) at ERROR level
    """
    response = drf_exception_handler(exc, context)
    view = context.get("view").__class__.__name__ if context.get("view") else "Unknown"

    if response is not None:
        if response.status_code >= 500:
            logger.error("api.error view=%s status=%s exc=%s",
                         view, response.status_code, exc)
        elif response.status_code >= 400:
            logger.info("api.4xx view=%s status=%s",
                        view, response.status_code)
        return response

    # Unhandled exception — return 500 with a user-friendly message
    logger.exception("api.unhandled view=%s exc=%s", view, exc)
    return Response(
        {"error": "Internal server error. Please try again or contact support."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
