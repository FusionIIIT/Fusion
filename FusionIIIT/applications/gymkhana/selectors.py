import datetime

from django.db.models import Prefetch, Q

from applications.academic_information.models import Student
from .models import Club_budget, Club_info, Club_member, Event_info, Session_info

# Club Selectors
def get_club_by_coordinator(user):
    """Get club where user is coordinator or co-coordinator"""
    try:
        student = Student.objects.get(id__user=user)
        club = Club_info.objects.filter(
            Q(co_ordinator=student) | Q(co_coordinator=student)
        ).select_related('co_ordinator', 'co_coordinator', 'faculty_incharge').first()
        return club
    except Student.DoesNotExist:
        return None

def get_all_clubs():
    """Get all clubs with optimized queries"""
    return Club_info.objects.select_related(
        'co_ordinator', 'co_coordinator', 'faculty_incharge'
    ).prefetch_related(
        Prefetch('this_club', queryset=Club_member.objects.select_related('member'))
    ).all()

def get_club_detail(club_name):
    """Get single club with details"""
    return Club_info.objects.select_related(
        'co_ordinator', 'co_coordinator', 'faculty_incharge'
    ).prefetch_related(
        Prefetch('this_club', queryset=Club_member.objects.select_related('member'))
    ).get(club_name=club_name)

def get_student_clubs(student_roll):
    """Get all clubs a student is member of"""
    return Club_member.objects.filter(
        member__id__id=student_roll,
        status='confirmed'
    ).select_related('club').values_list('club__club_name', flat=True)

def get_pending_members(club_name):
    """Get pending membership requests for a club"""
    return Club_member.objects.filter(
        club__club_name=club_name,
        status='open'
    ).select_related('member', 'member__id', 'member__id__user')

# Session/Event Selectors
def get_upcoming_events():
    """Get upcoming events"""
    today = datetime.date.today()
    return Event_info.objects.filter(
        date__gte=today,
        status='confirmed'
    ).select_related('club').order_by('date', 'start_time')

def get_past_events():
    """Get past events"""
    today = datetime.date.today()
    return Event_info.objects.filter(
        date__lt=today,
        status='confirmed'
    ).select_related('club').order_by('-date', '-start_time')

def get_club_events(club_name):
    """Get events for a specific club"""
    return Event_info.objects.filter(
        club__club_name=club_name
    ).select_related('club').order_by('-date')

def get_club_sessions(club_name):
    """Get sessions for a specific club"""
    today = datetime.date.today()
    return Session_info.objects.filter(
        club__club_name=club_name,
        date__gte=today
    ).select_related('club').order_by('date', 'start_time')

def check_session_conflict(date, start_time, end_time, venue, exclude_id=None):
    """Check if session time slot conflicts with existing sessions"""
    conflicts = Session_info.objects.filter(date=date, venue=venue)
    
    if exclude_id:
        conflicts = conflicts.exclude(id=exclude_id)
    
    start_time_obj = datetime.datetime.strptime(start_time, "%H:%M").time()
    end_time_obj = datetime.datetime.strptime(end_time, "%H:%M").time()
    
    for session in conflicts:
        if (start_time_obj < session.end_time and end_time_obj > session.start_time):
            return True
    return False

def check_event_conflict(date, start_time, end_time, venue, exclude_id=None):
    """Check if event time slot conflicts with existing events"""
    conflicts = Event_info.objects.filter(date=date, venue=venue)
    
    if exclude_id:
        conflicts = conflicts.exclude(id=exclude_id)
    
    start_time_obj = datetime.datetime.strptime(start_time, "%H:%M").time()
    end_time_obj = datetime.datetime.strptime(end_time, "%H:%M").time()
    
    for event in conflicts:
        if (start_time_obj < event.end_time and end_time_obj > event.start_time):
            return True
    return False

# Budget Selectors
def get_pending_budgets():
    """Get pending budget requests"""
    return Club_budget.objects.filter(status='open').select_related('club')

def get_club_budgets(club_name):
    """Get budgets for a specific club"""
    return Club_budget.objects.filter(
        club__club_name=club_name
    ).select_related('club').order_by('-id')
