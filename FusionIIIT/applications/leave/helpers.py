from django.contrib.auth.models import User
from django.db.models import Q


def get_user_choices(user):
    try:
        user_type = user.extrainfo.user_type
        ALL_USERS = User.objects.filter()
        USER_CHOICES = [(usr.username, "{} {}".format(usr.first_name, usr.last_name))
                         for usr in User.objects.filter(
                            ~Q(username = user.username),
                            Q(extrainfo__user_type = user_type),
                         )]

    except Exception as e:
        USER_CHOICES = []

    return USER_CHOICES
