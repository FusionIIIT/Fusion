from django import template
from django.contrib.contenttypes.models import ContentType

from notification_channels.models import Notification

register = template.Library()


""" Notification tags """


@register.simple_tag(name='get_all_notifs')
def get_all_notifs(user):
    return user.notifications.all().order_by("-timestamp")


@register.simple_tag(name='get_notif_count')
def get_notif_count(user):
    return user.notifications.all().count()


@register.simple_tag(name='get_related_notifs')
def get_related_notifs(obj):
    obj_ctype = ContentType.objects.get_for_model(obj)
    return Notification.objects.filter(target_ctype=obj_ctype,
                                       target_id=obj.id).order_by("-timestamp")


@register.simple_tag(name='get_action_notifs')
def get_action_notifs(obj):
    obj_ctype = ContentType.objects.get_for_model(obj)
    return Notification.objects.filter(action_obj_ctype=obj_ctype,
                                       action_obj_id=obj.id).order_by("-timestamp")


@register.simple_tag(name='get_user_action_notifs')
def get_user_action_notifs(user, obj):
    obj_ctype = ContentType.objects.get_for_model(obj)
    return Notification.objects.filter(recipient=user, action_obj_ctype=obj_ctype,
                                       action_obj_id=obj.id).order_by("-timestamp")


@register.simple_tag(name='get_user_related_notifs')
def get_user_related_notifs(user, obj):
    obj_ctype = ContentType.objects.get_for_model(obj)
    return Notification.objects.filter(recipient=user, target_ctype=obj_ctype,
                                       target_id=obj.id).order_by("-timestamp")


def unread_notifs(user):
    unread = user.notifications.filter(read=False).order_by("-timestamp")
    return {
            "notifications": unread,
        }


register.inclusion_tag("notification_channels/notify.html")(unread_notifs)


def unseen_notifs(user):
    unseen = user.notifications.filter(seen=False).order_by("-timestamp")
    return {
            "notifications": unseen,
        }


register.inclusion_tag("notification_channels/notify.html")(unseen_notifs)


def all_notifs(user):
    notifs = user.notifications.all().order_by("-timestamp")
    return {
            "notifications": notifs,
        }


register.inclusion_tag("notification_channels/notify.html")(all_notifs)


def type_notifs(typ, user):
    notifs = user.notifications.filter(notif_type=typ).order_by("-timestamp")
    return {
            "notifications": notifs,
        }


register.inclusion_tag("notification_channels/notify.html")(type_notifs)


def get_notification(notification):
    return {
            "notification": notification,
        }


register.inclusion_tag("notification_channels/notification.html")(get_notification)
