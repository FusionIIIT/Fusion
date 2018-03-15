from django import template

register = template.Library()


""" Activity tags """


@register.simple_tag(name='get_all_activities')
def get_all_activities(user):
    return user.activities.all().order_by("-timestamp")


@register.simple_tag(name='get_activities_count')
def get_activities_count(user):
    return user.activities.all().count()


def unread_activities(user):
    unread = user.activities.filter(read=False).order_by("-timestamp")
    return {
            "activities": unread,
        }


register.inclusion_tag("notification_channels/activity.html")(unread_activities)


def unseen_activities(user):
    unseen = user.activities.filter(seen=False).order_by("-timestamp")
    return {
            "activities": unseen,
        }


register.inclusion_tag("notification_channels/activity.html")(unseen_activities)


def all_activities(user):
    activities = user.activities.all().order_by("-timestamp")
    return {
            "activities": activities,
        }


register.inclusion_tag("notification_channels/activity.html")(all_activities)
