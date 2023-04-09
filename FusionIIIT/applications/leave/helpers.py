import datetime

from django.contrib.auth.models import User
from django.db.models import Q
from applications.globals.models import HoldsDesignation, Designation
from applications.globals.models import (ExtraInfo)


from .models import LeaveMigration, LeaveRequest, LeavesCount

def get_designation(user):
    """
    Function Definition: get_designation(user)

    Parameter List:

        user: a User object representing the user for whom the designation is being retrieved

    Short Description:

        This function retrieves the designation of a user from the database by querying the HoldsDesignation and Designation models. If the user holds the Assistant Registrar designation, the function returns "Assistant Registrar" as the designation.

    Results:

        This function returns the designation of the user as a string. If the user holds the Assistant Registrar designation, "Assistant Registrar" is returned as the designation. The function also prints the designation to the console.
    """
    desig = list(HoldsDesignation.objects.all().filter(working = user).values_list('designation'))
    b = [i for sub in desig for i in sub]
    try:
        c=str(Designation.objects.get(id=b[0]))
        for i in b:
            obj = Designation.objects.get(id=i)
            if str(obj)=='Assistant Registrar':
                c='Assistant Registrar'
            elif str(obj)== 'administrative':
                c='administrative'
    except:
        c = 'administrative'

    print(c)
    return c


def get_user_choices(user):
    """
    Function name: get_user_choices(user)

    Parameter:

        user: a User object representing the current user

    Description:
        This function retrieves a list of user choices based on the user type of the current user. If the current user's user type is not defined, an empty list is returned. Otherwise, it returns a list of tuples, with each tuple containing the username and full name of a user with the same user type as the current user. The list excludes the current user.

    Return:

        USER_CHOICES: a list of tuples representing the user choices, or an empty list if the current user's user type is not defined.
    """


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
    """
    Function Definition: get_special_leave_count(start, end, leave_name)

    Parameters:

        - start: A datetime object representing the start date of the leave period
        - end: A datetime object representing the end date of the leave period
        - leave_name: A string representing the name of the special leave

    Short Description: 

        This function calculates the number of special leaves taken between two dates, based on the given name of the special leave.

    Results: 

        The function returns a float value representing the number of special leaves taken. If any of the days between start and end are not a special leave day, the function returns -1.
    """
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
    """
    Function definition: get_vacation_leave_count(start,end,leave_name):

    Parameter list:

        - start: a datetime.date object representing the start date of the period for which vacation leave count is to be calculated
        - end: a datetime.date object representing the end date of the period for which vacation leave count is to be calculated
        - leave_name: a string representing the name of the vacation leave for which the count is to be calculated

    Short description: 
        
        This function calculates the count of vacation leave for a given period.

    Results: 
    
        This function returns a float value representing the count of vacation leave for the given period. If the vacation holiday does not exist for any of the dates in the given period, the function returns -1.
    """
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
    """
    Function definition: get_leave_days(start, end, leave_type, start_half, end_half)

    Parameter List:

        - start: A datetime object representing the starting date of the leave
        - end: A datetime object representing the ending date of the leave
        - leave_type: A LeaveType object representing the type of leave being requested
        - start_half: A boolean value indicating if the start date of the leave includes half-day
        - end_half: A boolean value indicating if the end date of the leave includes half-day
        
    Short Description:
        
        This function calculates the number of leave days between the start and end dates based on the leave_type and whether the leave includes half-day or not.

    Results:
        
        The function returns the number of leave days as a float value.
    """
    count = 0.0
    leave_name = leave_type.name

    # TODO: Remove this hard code and make it database dependent
    # Maybe add one field in leave type, which tells that this has to be taken from
    # academic calendar
    try:
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
    except:
        pass

    return count


def get_leaves(leave, check):
    """
    @param - leave: Leave application object
    This helper function returns a dictionary which maps from leave_type to number
    of days of leaves of that particular leave type.
    """
    mapping = dict()
    if check:
        for segment in leave.segments_offline.all():
            #if segment.leave_type.is_station:
            #    continue

            count = get_leave_days(segment.start_date, segment.end_date, segment.leave_type,
                                   segment.start_half, segment.end_half)
            if segment in mapping.keys():
                mapping[segment] += count
            else:
                mapping[segment] = count

        return mapping
    else:
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

def get_leaves_restore(leave):
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
    """
    Function definition: restore_leave_balance(leave)

    Parameter list:

        - leave: a Leave object for which the leave balance is to be restored

    Short description: 
    
        This function restores the leave balance for a given Leave object.

    Results generated: 
    
        This function restores the leave balance by updating the LeavesCount objects in the database according to the leave type and the year of the leave. If the LeavesCount object does not exist, the function does not update the database.
    """
    to_restore = get_leaves_restore(leave)
    for key, value in to_restore.items():
        try:
            if key.leave_type == 'Vacation':
                count = LeavesCount.objects.get(user=leave.applicant, leave_type=key.leave_type,
                                                year=key.start_date.year)
                #count.remaining_leaves += value / 2
                count.remaining_leaves += value
                count.save()
            elif key.leave_type == 'Earned':
                count = LeavesCount.objects.get(user=leave.applicant, leave_type=key.leave_type,
                                                year=key.start_date.year)
                #count.remaining_leaves += 2.0 * value
                count.remaining_leaves += value
                count.save()
            else:
                count = LeavesCount.objects.get(user=leave.applicant, leave_type=key.leave_type,
                                        year=key.start_date.year)
                count.remaining_leaves += value
                count.save()
        except:
            pass
        """count = LeavesCount.objects.get(user=leave.applicant, leave_type=key.leave_type,
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
            pass"""


def deduct_leave_balance(leave,check):
    """
    Function definition: deduct_leave_balance(leave,check)

    Parameter list:
        - leave: an instance of a leave application
        - check: a boolean variable indicating whether to check if leave balance is sufficient or not

    Short description: 
    
        This function deducts the leave balance for a given leave application and updates the LeavesCount table.

    Results generated: 
    
        This function does not return any value. It updates the remaining leave balance in the LeavesCount table for the applicant of the leave application.
    """
    to_deduct = get_leaves(leave,check)
    for key, value in to_deduct.items():
        
        try:
            if key.leave_type == 'Vacation':
                count = LeavesCount.objects.get(user=leave.applicant, leave_type=key.leave_type,
                                                year=key.start_date.year)
                #count.remaining_leaves -= value / 2
                count.remaining_leaves -= value
                count.save()
            elif key.leave_type == 'Earned':
                count = LeavesCount.objects.get(user=leave.applicant, leave_type=key.leave_type,
                                                year=key.start_date.year)
                #count.remaining_leaves -= 2.0 * value
                count.remaining_leaves -= value
                count.save()
            else:
                count = LeavesCount.objects.get(user=leave.applicant, leave_type=key.leave_type,
                                        year=key.start_date.year)
                count.remaining_leaves -= value
                count.save()
        except:
            pass

def deduct_leave_balance_student(leave, count, user):
    data = ExtraInfo.objects.get(user=user)

    if leave.name.lower() == 'medical':
            data.rem_medical_leave -= count
    elif leave.name.lower() == 'casual':
        data.rem_casual_leave -= count
    elif leave.name.lower() == 'vacational':
        data.rem_vacational_leave -= count
    else:
        data.rem_special_leave -= count
        
    data.save()


def get_pending_leave_requests(user):
    """
    Function definition: get_pending_leave_requests(user)

    Parameter list:

        - user: an instance of a user for whom pending leave requests are to be retrieved.

    Short description:

        This function retrieves all pending leave requests for a user, based on their current designation.

    Results:

        This function returns a queryset of all pending leave requests for the user. If no pending leave requests exist, an empty queryset is returned.
    """

    users = list(x.user for x in user.current_designation.all())
    requests = LeaveRequest.objects.filter(Q(requested_from__in=users), Q(status='pending'))
    return requests


def get_processed_leave_requests(user):
    pass


def create_migrations(leave):
    """
    Function definition: create_migrations(leave)

    Parameter list:

        - leave: an instance of LeaveRequest model

    Short description:
    
        This function creates LeaveMigration objects for each replacement segment of a leave request.

    Results:
    
        This function does not return anything. It creates LeaveMigration objects and saves them to the database.
    """
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
