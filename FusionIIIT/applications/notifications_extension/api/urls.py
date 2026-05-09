"""
api/urls.py — All API URL routing for the notification module.
Each endpoint is registered both with and without trailing slash.
"""

from django.urls import path

from . import views

app_name = "notifications_api"

def _both(route, view, name):
    """Register a URL both with and without trailing slash."""
    return [
        path(route,          view, name=name),
        path(route.rstrip("/"), view, name=name + "-noslash"),
    ]

urlpatterns = [

    # ── Mark as read + redirect ───────────────────────────────────────────────
    path("mark-as-read-and-redirect/<str:slug>/", views.mark_as_read_and_redirect, name="mark_as_read_and_redirect"),
    path("mark-as-read-and-redirect/<str:slug>",  views.mark_as_read_and_redirect, name="mark_as_read_and_redirect-noslash"),

    # ── List ──────────────────────────────────────────────────────────────────
    path("",          views.get_all_notifications,   name="notification-list"),
    *_both("unread/",       views.get_unread_notifications,  "notification-unread-list"),
    *_both("unread-count/", views.get_unread_count,          "notification-unread-count"),

    # ── Bulk actions ──────────────────────────────────────────────────────────
    *_both("mark-all-read/",   views.mark_all_as_read,         "notification-mark-all-read"),
    *_both("mark-all-unread/", views.mark_all_as_unread,       "notification-mark-all-unread"),
    *_both("delete-all/",    views.delete_all_notifications,  "notification-delete-all"),

    # ── Single-notification actions ───────────────────────────────────────────
    *_both("<int:notification_id>/mark-read/",   views.mark_as_read,        "notification-mark-read"),
    *_both("<int:notification_id>/mark-unread/", views.mark_as_unread,      "notification-mark-unread"),
    *_both("<int:notification_id>/delete/",      views.delete_notification,  "notification-delete"),
    *_both("<int:notification_id>/star/",        views.toggle_star,          "notification-star"),

    # ── Module-filtered ───────────────────────────────────────────────────────
    *_both("module/<str:module>/", views.get_notifications_by_module, "notification-by-module"),

    # ── Preferences (BR-NT-06: per-module opt-out) ───────────────────────────
    *_both("preferences/",     views.get_preferences, "notification-preferences"),
    *_both("preferences/set/", views.set_preference,  "notification-preference-set"),

    # ── Generic send (from other modules) ────────────────────────────────────
    *_both("send/", views.receive_notification, "notification-send"),
    *_both("send-group/", views.send_group_notification, "notification-send-group"),

    # ── UC-NT-01: Event Type Registry ────────────────────────────────────────
    *_both("event-types/register/",  views.register_event_type, "event-type-register"),
    *_both("event-types/",           views.list_event_types,    "event-type-list"),
    path("event-types/<str:event_id>/",  views.get_event_type,  name="event-type-detail"),
    path("event-types/<str:event_id>",   views.get_event_type,  name="event-type-detail-noslash"),

    # ── UC-NT-02: Trigger via Event ID ───────────────────────────────────────
    *_both("trigger/", views.trigger_event_notification, "trigger-event"),

    # ── UC-NT-03: Announcements ───────────────────────────────────────────────
    *_both("announcements/",                   views.list_active_announcements, "announcement-list"),
    *_both("announcements/all/",               views.list_all_announcements,    "announcement-list-all"),
    *_both("announcements/broadcast/",         views.broadcast_announcement,    "announcement-broadcast"),
    *_both("announcements/preview-audience/",  views.preview_audience,          "announcement-preview-audience"),

    # ── UC-NT-03: audience option lists for the dashboard broadcast modal ────
    *_both("audience/departments/",  views.list_departments,  "audience-departments"),
    *_both("audience/designations/", views.list_designations, "audience-designations"),
    *_both("audience/batches/",      views.list_batches,      "audience-batches"),
    *_both("audience/users/",        views.list_users,        "audience-users"),

    # ── UC-NT-04: Deep link open (mark read + return URL) ────────────────────
    *_both("<int:notification_id>/open/", views.mark_read_return_url, "notification-open"),

    # ── Module-specific endpoints ─────────────────────────────────────────────
    *_both("notify/leave/",                    views.notify_leave,                  "notify-leave"),
    *_both("notify/mess/",                     views.notify_mess,                   "notify-mess"),
    *_both("notify/hostel/",                   views.notify_hostel,                 "notify-hostel"),
    *_both("notify/healthcare/",               views.notify_healthcare,             "notify-healthcare"),
    *_both("notify/scholarship/",              views.notify_scholarship,            "notify-scholarship"),
    *_both("notify/dean-pnd/",                 views.notify_dean_pnd,               "notify-dean-pnd"),
    *_both("notify/dean-students/",            views.notify_dean_students,          "notify-dean-students"),
    *_both("notify/dean-rspc/",                views.notify_dean_rspc,              "notify-dean-rspc"),
    *_both("notify/gymkhana/voting/",          views.notify_gymkhana_voting,        "notify-gymkhana-voting"),
    *_both("notify/gymkhana/session/",         views.notify_gymkhana_session,       "notify-gymkhana-session"),
    *_both("notify/gymkhana/event/",           views.notify_gymkhana_event,         "notify-gymkhana-event"),
    *_both("notify/research/",                 views.notify_research,               "notify-research"),
    *_both("notify/assistantship/approved/",   views.notify_assistantship_approved, "notify-assistantship-approved"),
    *_both("notify/assistantship/faculty/",    views.notify_assistantship_faculty,  "notify-assistantship-faculty"),
    *_both("notify/assistantship/acad/",       views.notify_assistantship_acad,     "notify-assistantship-acad"),
    *_both("notify/assistantship/accounts/",   views.notify_assistantship_accounts, "notify-assistantship-accounts"),
    *_both("notify/complaint/",                views.notify_complaint,              "notify-complaint"),
    *_both("notify/file-tracking/",            views.notify_file_tracking,          "notify-file-tracking"),
    *_both("notify/placement/",                views.notify_placement,              "notify-placement"),
    *_both("notify/academics/",                views.notify_academics,              "notify-academics"),
    *_both("notify/department/",               views.notify_department,             "notify-department"),
]
