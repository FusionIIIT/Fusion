import datetime

from django.contrib.auth.models import User
from django.db.models import Q

from .models import LeaveMigration, LeaveRequest, LeavesCount


def get_user_choices(user):

    """

    # This Hacky way is to avoid an unrecognized error caused by following code:
    ------------------------
        try:
            user_type = user.extrainfo.user_type
            USER_CHOICES = [(usr.username, "{} {}".format(usr.first_name, usr.last_name))
                            for usr in User.objects.filter(
                            ~Q(username=user.username),
                            Q(extrainfo__user_type=user_type))]
        except Exception as e:
            USER_CHOICES = []
    -------------------------

    """
    error = False

    try:
        user_type = user.extrainfo.user_type
    except Exception as e:
        error = True
        USER_CHOICES = []

    if not error:
        USER_CHOICES = [(usr.username, "{} {}".format(usr.first_name, usr.last_name))
                        for usr in User.objects.filter(
                        ~Q(username=user.username),
                        Q(extrainfo__user_type=user_type))]

    return USER_CHOICES


def get_special_leave_count(start, end, leave_name):
    #from applications.academic_information.models import Holiday
    #special_holidays = Holiday.objects.filter(holiday_name=leave_name)
    from applications.leave.models import RestrictedHoliday
    special_holidays = RestrictedHoliday.objects.all()
    count = 0.0
    while start <= end:
        if not special_holidays.filter(date=start).exists():
            return -1
        count += 1.0
        start = start + datetime.timedelta(days=1)
    return count

#def date_range(start, end):
#    r = (end+datetime.timedelta(days=1)-start).days
#    return [start+datetime.timedelta(days=i) for i in range(r)]

def get_vacation_leave_count(start,end,leave_name):
    #win_start = datetime.date(2018,12,1)
    #win_end = datetime.date(2018,12,31)
    #vacation_winter=date_range(win_start,win_end)
    #sum_start = datetime.date(2019,5,1)
    #sum_end = datetime.date(2019,7,31)
    #vacation_summer = date_range(sum_start,sum_end)
    from applications.leave.models import VacationHoliday
    vacation_holidays = VacationHoliday.objects.all()
    count = 0.0
    while start <= end:
        if not vacation_holidays.filter(date=start).exists():
            return -1
        count += 1.0
        start = start + datetime.timedelta(days=1)
    return count


def get_leave_days(start, end, leave_type, start_half, end_half):
    count = 0.0
    leave_name = leave_type.name

    # TODO: Remove this hard code and make it database dependent
    # Maybe add one field in leave type, which tells that this has to be taken from
    # academic calendar
    if leave_name.lower()=='restricted':
        count = get_special_leave_count(start, end, leave_name.lower())
    elif leave_name.lower()=='vacation':
        count = get_vacation_leave_count(start, end, leave_name.lower())
    else:
        while start <= end:
            if not start.weekday() in [5, 6]:
                count += 1.0

            start = start + datetime.timedelta(days=1)

    if start_half and start.weekday() not in [5, 6]:
        count -= 0.5
    if end_half and end.weekday() not in [5, 6]:
        count -= 0.5

    return count


def get_leaves(leave):
    """
    @param - leave: Leave application object
    This helper function returns a dictionary which maps from leave_type to number
    of days of leaves of that particular leave type.
    """
    mapping = dict()

    for segment in leave.segments.all():
        #if segment.leave_type.is_station:
        #    continue

        count = get_leave_days(segment.start_date, segment.end_date, segment.leave_type,
                               segment.start_half, segment.end_half)
        if segment in mapping.keys():
            mapping[segment] += count
        else:
            mapping[segment] = count

    return mapping


def restore_leave_balance(leave):
    to_restore = get_leaves(leave)
    for key, value in to_restore.items():
        count = LeavesCount.objects.get(user=leave.applicant, leave_type=key.leave_type,
                                        year=key.start_date.year)
        count.remaining_leaves += value
        count.save()
        try:
            if key.leave_type == 'Vacation':
                count = LeavesCount.objects.get(user=leave.applicant, leave_type__name='Earned',
                                                year=key.start_date.year)
                count.remaining_leaves += value / 2
                count.save()
            elif key.leave_type == 'Earned':
                count = LeavesCount.objects.get(user=leave.applicant, leave_type__name='Vacation',
                                                year=key.start_date.year)
                count.remaining_leaves += 2.0 * value
                count.save()
        except:
            pass


def deduct_leave_balance(leave):
    to_deduct = get_leaves(leave)
    for key, value in to_deduct.items():
        count = LeavesCount.objects.get(user=leave.applicant, leave_type=key.leave_type,
                                        year=key.start_date.year)
        count.remaining_leaves -= value
        count.save()
        try:
            if key.leave_type == 'Vacation':
                count = LeavesCount.objects.get(user=leave.applicant, leave_type__name='Earned',
                                                year=key.start_date.year)
                count.remaining_leaves -= value / 2
                count.save()
            elif key.leave_type == 'Earned':
                count = LeavesCount.objects.get(user=leave.applicant, leave_type__name='Vacation',
                                                year=key.start_date.year)
                count.remaining_leaves -= 2.0 * value
                count.save()
        except:
            pass


def get_pending_leave_requests(user):
    users = list(x.user for x in user.current_designation.all())
    requests = LeaveRequest.objects.filter(Q(requested_from__in=users), Q(status='pending'))
    return requests


def get_processed_leave_requests(user):
    pass


def create_migrations(leave):
    migrations = []
    applicant = leave.applicant
    for rep_segment in leave.replace_segments.all():
        mig_transfer = LeaveMigration(
            leave=leave,
            type_migration='transfer',
            on_date=rep_segment.start_date,
            replacee=applicant,
            replacer=rep_segment.replacer,
            replacement_type=rep_segment.replacement_type
        )
        mig_revert = LeaveMigration(
            leave=leave,
            type_migration='revert',
            on_date=rep_segment.end_date + datetime.timedelta(days=1),
            replacee=applicant,
            replacer=rep_segment.replacer,
            replacement_type=rep_segment.replacement_type
        )

        migrations += [mig_transfer, mig_revert]

    LeaveMigration.objects.bulk_create(migrations)
