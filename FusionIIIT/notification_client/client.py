"""
notification_client/client.py

The ONLY way other Fusion modules are allowed to send notifications.

Rules:
  - Other modules MUST import from this file.
  - Other modules must NOT call notify.send() directly.
  - Other modules must NOT import from applications.notifications_extension.services directly.
  - This client calls the Notification Module REST API internally.

Usage example (from any other Fusion module):
    from notification_client.client import NotificationClient
    client = NotificationClient.for_request(request)
    client.leave(recipient_username="student1", type="leave_accepted")
"""

import requests
from django.conf import settings


# Base URL for the notification module API.
# In production replace with the real service URL via settings.
_BASE_URL = getattr(settings, "NOTIFICATION_API_BASE_URL", "http://127.0.0.1:8000/api/notifications")


class NotificationError(Exception):
    """Raised when the notification API returns an error."""


class NotificationClient:
    """
    Client for the Fusion Notification Module API.

    Instantiate with an auth token:
        client = NotificationClient(token="abc123")

    Or from a DRF request (token is extracted automatically):
        client = NotificationClient.for_request(request)
    """

    def __init__(self, token: str):
        self._headers = {
            "Authorization": f"Token {token}",
            "Content-Type":  "application/json",
        }

    # ── Factory ──────────────────────────────────────────────────────────────

    @classmethod
    def for_request(cls, request):
        """
        Build a client from the current DRF request.
        The calling module's authenticated token is forwarded.
        """
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if auth.startswith("Token "):
            return cls(token=auth.split(" ", 1)[1])
        # Session-auth fallback: fetch or create a token for this user
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=request.user)
        return cls(token=token.key)

    # ── Internal ─────────────────────────────────────────────────────────────

    def _post(self, endpoint: str, payload: dict):
        url = f"{_BASE_URL}/{endpoint.lstrip('/')}"
        response = requests.post(url, json=payload, headers=self._headers, timeout=5)
        if not response.ok:
            raise NotificationError(
                f"Notification API error [{response.status_code}]: {response.text}"
            )
        return response.json()

    # ─────────────────────────────────────────────────────────────────────────
    #  Public methods — one per Fusion module
    #  Each method maps 1-to-1 with a notification type.
    # ─────────────────────────────────────────────────────────────────────────

    def leave(self, *, recipient_username: str, type: str, date: str = None):
        """
        Send a Leave Module notification.

        type choices:
            leave_applied | request_accepted | request_declined |
            leave_accepted | leave_forwarded | leave_rejected |
            offline_leave | replacement_request | leave_request |
            leave_withdrawn | replacement_cancel

        date: required for leave_withdrawn and replacement_cancel
        """
        payload = {"recipient_username": recipient_username, "type": type}
        if date:
            payload["date"] = date
        return self._post("notify/leave/", payload)

    def mess(self, *, recipient_username: str, type: str, message: str = None):
        """
        Send a Central Mess notification.

        type choices:
            feedback_submitted | menu_change_accepted | leave_request |
            vacation_request | meeting_invitation | special_request | added_committee

        message: required for leave_request, vacation_request,
                 meeting_invitation, special_request
        """
        payload = {"recipient_username": recipient_username, "type": type}
        if message:
            payload["message"] = message
        return self._post("notify/mess/", payload)

    def hostel(self, *, recipient_username: str, type: str):
        """
        Send a Visitor's Hostel notification.

        type choices:
            booking_confirmation | booking_cancellation_request_accepted |
            booking_request | cancellation_request_placed |
            booking_forwarded | booking_rejected
        """
        return self._post("notify/hostel/", {
            "recipient_username": recipient_username,
            "type": type,
        })

    def healthcare(self, *, recipient_username: str, type: str):
        """
        Send a Healthcare Center notification.

        type choices:
            appoint | amb_request | Presc | appoint_req | amb_req
        """
        return self._post("notify/healthcare/", {
            "recipient_username": recipient_username,
            "type": type,
        })

    def scholarship(self, *, recipient_username: str, type: str):
        """
        Send a Scholarship Portal notification.

        type choices:
            Accept_MCM | Reject_MCM | Accept_Gold | Reject_Gold |
            Accept_Silver | Reject_Silver | Accept_DM
        """
        return self._post("notify/scholarship/", {
            "recipient_username": recipient_username,
            "type": type,
        })

    def dean_pnd(self, *, recipient_username: str, type: str):
        """
        Send an Office of Dean PnD notification.

        type choices:
            requisition_filed | request_accepted | request_rejected |
            assignment_created | assignment_received |
            assignment_reverted | assignment_approved | assignment_rejected
        """
        return self._post("notify/dean-pnd/", {
            "recipient_username": recipient_username,
            "type": type,
        })

    def dean_students(self, *, recipient_username: str, type: str):
        """
        Send an Office Module (Dean Students) notification.

        type choices:
            hostel_alloted | insufficient_funds | MOM_submitted |
            budget_approved | budget_rejected | club_approved | club_rejected |
            meeting_booked | session_approved | session_rejected | budget_alloted
        """
        return self._post("notify/dean-students/", {
            "recipient_username": recipient_username,
            "type": type,
        })

    def dean_rspc(self, *, recipient_username: str, type: str):
        """
        Send an Office Module (Dean RSPC) notification.

        type choices:
            Approve | Disapprove | Pending
        """
        return self._post("notify/dean-rspc/", {
            "recipient_username": recipient_username,
            "type": type,
        })

    def gymkhana_voting(self, *, recipient_username: str, title: str, desc: str):
        """Send a Gymkhana voting-open notification."""
        return self._post("notify/gymkhana/voting/", {
            "recipient_username": recipient_username,
            "title": title,
            "desc":  desc,
        })

    def gymkhana_session(self, *, recipient_username: str, club: str,
                         desc: str, venue: str):
        """Send a Gymkhana new-session notification."""
        return self._post("notify/gymkhana/session/", {
            "recipient_username": recipient_username,
            "club":  club,
            "desc":  desc,
            "venue": venue,
        })

    def gymkhana_event(self, *, recipient_username: str, club: str,
                       event_name: str, desc: str, venue: str):
        """Send a Gymkhana new-event notification."""
        return self._post("notify/gymkhana/event/", {
            "recipient_username": recipient_username,
            "club":        club,
            "event_name":  event_name,
            "desc":        desc,
            "venue":       venue,
        })

    def research(self, *, recipient_username: str, type: str):
        """
        Send a Research Procedures notification.

        type choices:
            Approved | Disapproved | Pending | submitted | created
        """
        return self._post("notify/research/", {
            "recipient_username": recipient_username,
            "type": type,
        })

    def assistantship_approved(self, *, recipient_username: str,
                                month: str, year: str):
        """Notify student that assistantship claim is approved."""
        return self._post("notify/assistantship/approved/", {
            "recipient_username": recipient_username,
            "month": month,
            "year":  year,
        })

    def assistantship_faculty(self, *, recipient_username: str):
        """Notify faculty that an assistantship claim is requested."""
        return self._post("notify/assistantship/faculty/", {
            "recipient_username": recipient_username,
        })

    def assistantship_acad(self, *, recipient_username: str):
        """Notify academic section that an assistantship claim is requested."""
        return self._post("notify/assistantship/acad/", {
            "recipient_username": recipient_username,
        })

    def assistantship_accounts(self, *, recipient_username: str,
                                student_username: str):
        """Notify accounts section that a claim has been forwarded."""
        return self._post("notify/assistantship/accounts/", {
            "recipient_username": recipient_username,
            "student_username":   student_username,
        })

    def complaint(self, *, recipient_username: str, complaint_id: int,
                  is_student: bool, message: str):
        """
        Send a Complaint System notification.

        is_student=True  → links to student complaint detail view
        is_student=False → links to staff complaint detail view
        """
        return self._post("notify/complaint/", {
            "recipient_username": recipient_username,
            "complaint_id":       complaint_id,
            "is_student":         is_student,
            "message":            message,
        })

    def file_tracking(self, *, recipient_username: str, title: str):
        """Send a File Tracking notification. title = the file/document name."""
        return self._post("notify/file-tracking/", {
            "recipient_username": recipient_username,
            "title": title,
        })

    def placement(self, *, recipient_username: str, message: str):
        """Send a Placement Cell notification."""
        return self._post("notify/placement/", {
            "recipient_username": recipient_username,
            "message": message,
        })

    def academics(self, *, recipient_username: str, message: str):
        """Send an Academics Module notification."""
        return self._post("notify/academics/", {
            "recipient_username": recipient_username,
            "message": message,
        })

    def department(self, *, recipient_username: str, message: str):
        """Send a Department notification."""
        return self._post("notify/department/", {
            "recipient_username": recipient_username,
            "message": message,
        })
