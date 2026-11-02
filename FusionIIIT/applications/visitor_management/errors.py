"""Service-layer exceptions. The API layer turns them into HTTP responses."""


class ServiceError(Exception):
    status_code = 400
    default_code = "invalid"

    def __init__(self, message, code=None, details=None):
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        self.details = details or {}

    def as_dict(self):
        payload = {"detail": self.message, "code": self.code}
        if self.details:
            payload["errors"] = self.details
        return payload


class ValidationFailed(ServiceError):
    status_code = 400
    default_code = "validation_failed"


class NotAuthenticated(ServiceError):
    status_code = 401
    default_code = "not_authenticated"


class NotAuthorized(ServiceError):
    status_code = 403
    default_code = "not_authorized"


class NotFound(ServiceError):
    status_code = 404
    default_code = "not_found"


class Conflict(ServiceError):
    status_code = 409
    default_code = "conflict"


class RateLimited(ServiceError):
    status_code = 429
    default_code = "rate_limited"


class Unavailable(ServiceError):
    status_code = 503
    default_code = "unavailable"
