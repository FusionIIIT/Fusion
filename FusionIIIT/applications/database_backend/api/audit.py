from django.utils import timezone
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


class DatabaseAuditLog:
    """
    Utility class for logging database access activities.
    Logs all successful and failed attempts to access sensitive data.
    """

    AUDIT_LOG_NAME = 'database_access_audit'
    audit_logger = logging.getLogger(AUDIT_LOG_NAME)

    @staticmethod
    def log_access(user: User, action: str, endpoint: str, batch_id: str = None,
                   status: str = "SUCCESS", error_message: str = None, additional_data: dict = None):
        """
        Log database access activity.

        Args:
            user: User object performing the action
            action: Type of action (e.g., 'FETCH_BATCHES', 'VIEW_GRADES', 'EXPORT_DATA')
            endpoint: API endpoint accessed (e.g., '/database/api/batches/')
            batch_id: Optional batch year being accessed
            status: 'SUCCESS' or 'FAILURE'
            error_message: Optional error message if action failed
            additional_data: Optional dictionary with additional context
        """
        timestamp = timezone.now().isoformat()

        log_entry = {
            'timestamp': timestamp,
            'username': user.username,
            'user_id': user.id,
            'action': action,
            'endpoint': endpoint,
            'batch_id': batch_id or 'N/A',
            'status': status,
            'error': error_message or 'N/A',
            'additional_data': additional_data or {}
        }

        # Log at INFO level for successful access, WARNING for failures
        if status == "SUCCESS":
            DatabaseAuditLog.audit_logger.info(
                f"Database access: {action} | User: {user.username} | Endpoint: {endpoint} | "
                f"Batch: {batch_id or 'N/A'} | Status: {status}"
            )
        else:
            DatabaseAuditLog.audit_logger.warning(
                f"Failed database access attempt: {action} | User: {user.username} | "
                f"Endpoint: {endpoint} | Error: {error_message}"
            )

        return log_entry

    @staticmethod
    def log_unauthorized_attempt(user_username: str, user_id: int, endpoint: str, reason: str):
        """
        Log unauthorized access attempts (e.g., user without database permission).

        Args:
            user_username: Username attempting access
            user_id: User ID
            endpoint: API endpoint accessed
            reason: Reason for denial (e.g., 'Missing database permission')
        """
        timestamp = timezone.now().isoformat()

        DatabaseAuditLog.audit_logger.warning(
            f"UNAUTHORIZED DATABASE ACCESS ATTEMPT | Timestamp: {timestamp} | "
            f"User: {user_username} (ID: {user_id}) | Endpoint: {endpoint} | "
            f"Reason: {reason}"
        )
