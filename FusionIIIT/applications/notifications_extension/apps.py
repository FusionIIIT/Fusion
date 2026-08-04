# NOTE (as of 2026-07-31): This app's REST API (`/notifications/api/...`) is not used
# by the Fusion React frontend. The frontend's Notifications tab instead calls the
# equivalent endpoints in `applications/globals/api/` (`/api/notification/`,
# `/api/notificationread`, `/api/notificationdelete`, `/api/notificationunread`).
# This app appears to be an earlier/parallel implementation that was superseded but
# never removed. Left in place rather than deleted - verify it is still unused before
# building on or relying on it. See `applications/notifications_extension/api/views.py`
# and `api/urls.py` for the duplicated notification list/read/delete endpoints, plus a
# set of per-module notification-sending wrapper endpoints that are also unreferenced
# by the frontend (modules send notifications by calling `notification/views.py`
# helper functions directly instead).
from django.apps import AppConfig


class NotificationsExtensionConfig(AppConfig):
    name = 'applications.notifications_extension'
