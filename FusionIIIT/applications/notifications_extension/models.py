"""
models.py

All models and constants (TextChoices / IntegerChoices) for the notification module.

Source analysis:
  - notification/views.py       : All module names and verb strings extracted → TextChoices
  - notifications_extension/views.py : mark_as_read_and_redirect logic uses Notification model
  - Both source models.py were empty → NotificationPreference is a new custom model added here
"""

import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


# ─────────────────────────────────────────────
#  TextChoices — extracted from all hardcoded
#  module/type strings in both source views.py
# ─────────────────────────────────────────────

class ModuleName(models.TextChoices):
    LEAVE_MODULE          = "Leave Module",              "Leave Module"
    PLACEMENT_CELL        = "Placement Cell",            "Placement Cell"
    ACADEMICS_MODULE      = "Academic's Module",         "Academic's Module"
    CENTRAL_MESS          = "Central Mess",              "Central Mess"
    VISITORS_HOSTEL       = "Visitor's Hostel",          "Visitor's Hostel"
    HEALTHCARE_CENTER     = "Healthcare Center",         "Healthcare Center"
    FILE_TRACKING         = "File Tracking",             "File Tracking"
    SCHOLARSHIP_PORTAL    = "Scholarship Portal",        "Scholarship Portal"
    COMPLAINT_SYSTEM      = "Complaint System",          "Complaint System"
    OFFICE_DEAN_PND       = "Office of Dean PnD Module", "Office of Dean PnD Module"
    OFFICE_MODULE         = "Office Module",             "Office Module"
    GYMKHANA_MODULE       = "Gymkhana Module",           "Gymkhana Module"
    ASSISTANTSHIP_REQUEST = "Assistantship Request",     "Assistantship Request"
    DEPARTMENT            = "department",                "Department"
    RESEARCH_PROCEDURES   = "Research Procedures",       "Research Procedures"


class LeaveNotifType(models.TextChoices):
    LEAVE_APPLIED       = "leave_applied",       "Leave Applied"
    REQUEST_ACCEPTED    = "request_accepted",    "Request Accepted"
    REQUEST_DECLINED    = "request_declined",    "Request Declined"
    LEAVE_ACCEPTED      = "leave_accepted",      "Leave Accepted"
    LEAVE_FORWARDED     = "leave_forwarded",     "Leave Forwarded"
    LEAVE_REJECTED      = "leave_rejected",      "Leave Rejected"
    OFFLINE_LEAVE       = "offline_leave",       "Offline Leave Updated"
    REPLACEMENT_REQUEST = "replacement_request", "Replacement Request"
    LEAVE_REQUEST       = "leave_request",       "Leave Request"
    LEAVE_WITHDRAWN     = "leave_withdrawn",     "Leave Withdrawn"
    REPLACEMENT_CANCEL  = "replacement_cancel",  "Replacement Cancelled"


class MessNotifType(models.TextChoices):
    FEEDBACK_SUBMITTED    = "feedback_submitted",    "Feedback Submitted"
    MENU_CHANGE_ACCEPTED  = "menu_change_accepted",  "Menu Change Accepted"
    LEAVE_REQUEST         = "leave_request",         "Leave Request"
    VACATION_REQUEST      = "vacation_request",      "Vacation Request"
    MEETING_INVITATION    = "meeting_invitation",    "Meeting Invitation"
    SPECIAL_REQUEST       = "special_request",       "Special Request"
    ADDED_COMMITTEE       = "added_committee",       "Added to Committee"


class VisitorHostelNotifType(models.TextChoices):
    BOOKING_CONFIRMATION              = "booking_confirmation",              "Booking Confirmed"
    BOOKING_CANCELLATION_REQ_ACCEPTED = "booking_cancellation_request_accepted", "Cancellation Accepted"
    BOOKING_REQUEST                   = "booking_request",                   "Booking Request"
    CANCELLATION_REQUEST_PLACED       = "cancellation_request_placed",       "Cancellation Request Placed"
    BOOKING_FORWARDED                 = "booking_forwarded",                 "Booking Forwarded"
    BOOKING_REJECTED                  = "booking_rejected",                  "Booking Rejected"


class HealthcareNotifType(models.TextChoices):
    APPOINTMENT_BOOKED  = "appoint",      "Appointment Booked"
    AMBULANCE_REQUEST   = "amb_request",  "Ambulance Request Placed"
    PRESCRIPTION        = "Presc",        "Prescription Issued"
    APPOINTMENT_REQUEST = "appoint_req",  "New Appointment Request"
    AMBULANCE_REQ       = "amb_req",      "New Ambulance Request"


class ScholarshipNotifType(models.TextChoices):
    ACCEPT_MCM    = "Accept_MCM",    "MCM Form Accepted"
    REJECT_MCM    = "Reject_MCM",    "MCM Form Rejected"
    ACCEPT_GOLD   = "Accept_Gold",   "Gold Medal Form Accepted"
    REJECT_GOLD   = "Reject_Gold",   "Gold Medal Form Rejected"
    ACCEPT_SILVER = "Accept_Silver", "Silver Medal Form Accepted"
    REJECT_SILVER = "Reject_Silver", "Silver Medal Form Rejected"
    ACCEPT_DM     = "Accept_DM",     "D&M Medal Form Accepted"


class OfficeDeanPnDNotifType(models.TextChoices):
    REQUISITION_FILED    = "requisition_filed",    "Requisition Filed"
    REQUEST_ACCEPTED     = "request_accepted",     "Request Accepted"
    REQUEST_REJECTED     = "request_rejected",     "Request Rejected"
    ASSIGNMENT_CREATED   = "assignment_created",   "Assignment Created"
    ASSIGNMENT_RECEIVED  = "assignment_received",  "Assignment Received"
    ASSIGNMENT_REVERTED  = "assignment_reverted",  "Assignment Reverted"
    ASSIGNMENT_APPROVED  = "assignment_approved",  "Assignment Approved"
    ASSIGNMENT_REJECTED  = "assignment_rejected",  "Assignment Rejected"


class OfficeDeanSNotifType(models.TextChoices):
    HOSTEL_ALLOTED      = "hostel_alloted",      "Hostel Alloted"
    INSUFFICIENT_FUNDS  = "insufficient_funds",  "Insufficient Funds"
    MOM_SUBMITTED       = "MOM_submitted",       "MOM Submitted"
    BUDGET_APPROVED     = "budget_approved",     "Budget Approved"
    BUDGET_REJECTED     = "budget_rejected",     "Budget Rejected"
    CLUB_APPROVED       = "club_approved",       "Club Approved"
    CLUB_REJECTED       = "club_rejected",       "Club Rejected"
    MEETING_BOOKED      = "meeting_booked",      "Meeting Booked"
    SESSION_APPROVED    = "session_approved",    "Session Approved"
    SESSION_REJECTED    = "session_rejected",    "Session Rejected"
    BUDGET_ALLOTED      = "budget_alloted",      "Budget Alloted"


class OfficeDeanRSPCNotifType(models.TextChoices):
    APPROVE    = "Approve",    "Approved"
    DISAPPROVE = "Disapprove", "Disapproved"
    PENDING    = "Pending",    "Pending"


class GymkhanaNotifType(models.TextChoices):
    VOTING_OPEN = "voting_open", "Voting Open"
    NEW_SESSION = "new_session", "New Session"
    NEW_EVENT   = "new_event",   "New Event"


class ResearchProceduresNotifType(models.TextChoices):
    APPROVED    = "Approved",    "Approved"
    DISAPPROVED = "Disapproved", "Disapproved"
    PENDING     = "Pending",     "Pending"
    SUBMITTED   = "submitted",   "Submitted"
    CREATED     = "created",     "Created"


# ─────────────────────────────────────────────
#  Custom Model
# ─────────────────────────────────────────────

class NotificationPreference(models.Model):
    """
    Per-user, per-module notification preference.
    Allows users to opt in/out of notifications from specific Fusion modules.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    module = models.CharField(
        max_length=60,
        choices=ModuleName.choices,
    )
    is_enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "module")
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"

    def __str__(self):
        status = "ON" if self.is_enabled else "OFF"
        return f"{self.user.username} — {self.module} [{status}]"


# ─────────────────────────────────────────────
#  UC-NT-01: Notification Event Type Registry
# ─────────────────────────────────────────────

class EventPriority(models.TextChoices):
    LOW      = "low",      "Low"
    MEDIUM   = "medium",   "Medium"
    HIGH     = "high",     "High"
    CRITICAL = "critical", "Critical"  # BR-NT-05: bypasses user preferences


class NotificationEventType(models.Model):
    """
    UC-NT-01: Registered notification event types.
    External Fusion modules register their event types here before they can
    trigger notifications via the NAM API.
    """
    event_id       = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    event_name     = models.CharField(max_length=100)
    module         = models.CharField(max_length=60, choices=ModuleName.choices)
    default_priority = models.CharField(
        max_length=10,
        choices=EventPriority.choices,
        default=EventPriority.MEDIUM,
    )
    description    = models.TextField(blank=True, default="")
    registered_by  = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="registered_event_types",
    )
    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event_name", "module")
        verbose_name = "Notification Event Type"
        verbose_name_plural = "Notification Event Types"
        ordering = ["module", "event_name"]

    def __str__(self):
        return f"{self.module} / {self.event_name} [{self.event_id}]"


# ─────────────────────────────────────────────
#  UC-NT-03: Announcements (Manual Broadcast)
# ─────────────────────────────────────────────

class AudienceType(models.TextChoices):
    ALL           = "all",           "All Users"
    STUDENTS      = "students",      "All Students"
    FACULTY       = "faculty",       "All Faculty"
    STAFF         = "staff",         "All Staff"
    GROUP         = "group",         "Specific Designation"
    DEPARTMENT    = "department",    "By Department"
    BATCH         = "batch",         "By Batch"
    SPECIFIC_USER = "specific_user", "Specific User"


# ─────────────────────────────────────────────
#  BR-NT-09: Archived Notifications (soft delete)
# ─────────────────────────────────────────────

class ArchivedNotification(models.Model):
    """
    BR-NT-09: Tracks which notifications have been archived by a user.
    Notifications are NOT deleted from the DB — they are retained for 180 days.
    The notification_id refers to the django-notifications-hq Notification pk.
    """
    user            = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="archived_notifications"
    )
    notification_id = models.IntegerField()
    archived_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "notification_id")
        verbose_name = "Archived Notification"

    def __str__(self):
        return f"{self.user.username} archived #{self.notification_id} at {self.archived_at}"


# ─────────────────────────────────────────────
#  Fusionlab RBAC — unmanaged mirrors of the
#  globals_* tables that already exist in the DB.
#  managed = False means Django never creates/
#  drops these; it just lets us query them via ORM.
# ─────────────────────────────────────────────

class GlobalsDesignation(models.Model):
    """Mirror of public.globals_designation — roles like Director, HOD, Dean, etc."""
    name      = models.CharField(max_length=50)
    full_name = models.CharField(max_length=100)
    type      = models.CharField(max_length=30)    # 'academic' | 'administrative'
    basic     = models.BooleanField(default=False)
    category  = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        managed  = False
        db_table = "globals_designation"

    def __str__(self):
        return self.name


class GlobalsDepartmentInfo(models.Model):
    """Mirror of public.globals_departmentinfo — departments (CSE, ECE, ME, etc.)."""
    id   = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        managed  = False
        db_table = "globals_departmentinfo"

    def __str__(self):
        return self.name


class GlobalsExtraInfo(models.Model):
    """Mirror of public.globals_extrainfo — stores user_type and department."""
    id               = models.CharField(max_length=50, primary_key=True)
    user             = models.OneToOneField(
        User, on_delete=models.DO_NOTHING, db_column="user_id"
    )
    user_type        = models.CharField(max_length=20)   # 'student' | 'staff' | 'faculty'
    department       = models.ForeignKey(
        GlobalsDepartmentInfo, on_delete=models.DO_NOTHING,
        db_column="department_id", null=True, blank=True,
    )

    class Meta:
        managed  = False
        db_table = "globals_extrainfo"

    def __str__(self):
        return f"{self.id} ({self.user_type})"


class GlobalsHoldsDesignation(models.Model):
    """Mirror of public.globals_holdsdesignation — maps user → designation."""
    user        = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, db_column="user_id"
    )
    designation = models.ForeignKey(
        GlobalsDesignation, on_delete=models.DO_NOTHING, db_column="designation_id"
    )
    working_id  = models.IntegerField()
    held_at     = models.DateTimeField(null=True)

    class Meta:
        managed  = False
        db_table = "globals_holdsdesignation"

    def __str__(self):
        return f"{self.user_id} → {self.designation_id}"


class Announcement(models.Model):
    """
    UC-NT-03: Manual broadcast announcement created by an admin/authorized sender.
    Displayed on all targeted users' dashboards until the expiry date.
    """
    title          = models.CharField(max_length=200)
    message        = models.TextField()
    sender         = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_announcements",
    )
    audience_type  = models.CharField(
        max_length=20,
        choices=AudienceType.choices,
        default=AudienceType.ALL,
    )
    # For audience_type=GROUP: the Django auth group name (e.g. "4th_Year_BTech")
    audience_value = models.CharField(max_length=100, blank=True, default="")
    expiry_date    = models.DateField()
    created_at     = models.DateTimeField(auto_now_add=True)
    # BR-NT-08: Audit Trail Integrity — every announcement is stamped with a
    # unique Approval_ID at creation time. Admins self-approve at submit, so
    # we generate the UUID immediately rather than running a workflow.
    approval_id    = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        verbose_name = "Announcement"
        verbose_name_plural = "Announcements"
        ordering = ["-created_at"]

    @property
    def is_active(self):
        return self.expiry_date >= timezone.now().date()

    def __str__(self):
        return f"{self.title} (expires {self.expiry_date})"
