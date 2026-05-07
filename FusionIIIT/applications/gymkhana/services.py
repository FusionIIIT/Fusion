from django.db import transaction
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import Club_info, Club_member, Session_info, Event_info
from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo, Faculty, HoldsDesignation, Designation
from notification.views import gymkhana_session, gymkhana_event
import logging

logger = logging.getLogger(__name__)


class ClubService:
    """Compatibility wrapper for the legacy unit tests."""

    @staticmethod
    def _validate_student(student_id):
        try:
            extra = ExtraInfo.objects.get(id=student_id, user_type='student')
            return Student.objects.get(id=extra)
        except (ExtraInfo.DoesNotExist, Student.DoesNotExist):
            return None

@transaction.atomic
def create_club(data, request_user):
    """
    Create a new club
    Matches V3 from your plan - extracted from new_club()
    """
    try:
        club_name = data.get('club_name')
        category = data.get('category')
        co_ordinator_id = data.get('co_ordinator')
        co_coordinator_id = data.get('co_coordinator')
        faculty_name = data.get('faculty_incharge')
        description = data.get('description')
        
        # Get coordinator student
        co_extra = get_object_or_404(ExtraInfo, id=co_ordinator_id, user_type='student')
        co_student = get_object_or_404(Student, id=co_extra)
        
        # Get co-coordinator student
        coco_extra = get_object_or_404(ExtraInfo, id=co_coordinator_id, user_type='student')
        coco_student = get_object_or_404(Student, id=coco_extra)
        
        # Get faculty
        faculty_parts = faculty_name.split()
        faculty_user = User.objects.filter(
            first_name__icontains=faculty_parts[0],
            last_name__icontains=faculty_parts[-1] if len(faculty_parts) > 1 else ''
        ).first()
        faculty_extra = get_object_or_404(ExtraInfo, user=faculty_user, user_type='faculty')
        faculty_inc = get_object_or_404(Faculty, id=faculty_extra)
        
        # Create club
        club = Club_info.objects.create(
            club_name=club_name,
            category=category,
            co_ordinator=co_student,
            co_coordinator=coco_student,
            faculty_incharge=faculty_inc,
            description=description,
            status='open'
        )
        
        return {"success": True, "club": club, "message": "Club created successfully"}
        
    except Exception as e:
        logger.error(f"Error creating club: {e}")
        return {"success": False, "message": str(e)}

@transaction.atomic
def approve_membership(club_name, member_ids, remarks_list):
    """
    Approve club membership requests
    Matches V3 - extracted from approve()
    """
    try:
        club = get_object_or_404(Club_info, club_name=club_name)
        approved_count = 0
        
        for member_id, remarks in zip(member_ids, remarks_list):
            # Get member
            extra = get_object_or_404(ExtraInfo, id=member_id, user_type='student')
            student = get_object_or_404(Student, id=extra)
            
            # Update or create membership
            member, created = Club_member.objects.update_or_create(
                club=club,
                member=student,
                defaults={'status': 'confirmed', 'remarks': remarks}
            )
            approved_count += 1
        
        return {"success": True, "approved": approved_count, "message": f"Approved {approved_count} members"}
        
    except Exception as e:
        logger.error(f"Error approving membership: {e}")
        return {"success": False, "message": str(e)}


@transaction.atomic
def create_membership_request(club_name, member_id, description=""):
    """Create a club membership request if one does not already exist."""
    try:
        club = get_object_or_404(Club_info, club_name=club_name)
        extra = get_object_or_404(ExtraInfo, id=member_id, user_type='student')
        student = get_object_or_404(Student, id=extra)

        member, created = Club_member.objects.get_or_create(
            club=club,
            member=student,
            defaults={
                'description': description,
                'status': 'open',
            },
        )
        if not created:
            return {"success": False, "message": "Membership request already exists"}

        return {"success": True, "member": member, "message": "Membership request sent"}
    except Exception as e:
        logger.error(f"Error creating membership request: {e}")
        return {"success": False, "message": str(e)}

@transaction.atomic
def create_session(data, club, request_user):
    """
    Create a new session
    Matches V4 - extracted from new_session()
    """
    try:
        venue = data.get('venue')
        session_poster = data.get('session_poster')
        date = data.get('date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        details = data.get('details')
        
        session = Session_info.objects.create(
            club=club,
            venue=venue,
            date=date,
            start_time=start_time,
            end_time=end_time,
            session_poster=session_poster,
            details=details,
            status='open'
        )
        
        # Send notifications
        from applications.globals.models import ExtraInfo
        students = ExtraInfo.objects.filter(user_type='student')
        recipients = User.objects.filter(extrainfo__in=students)
        gymkhana_session(request_user, recipients, "new_session", club, details, venue)
        
        return {"success": True, "session": session, "message": "Session created successfully"}
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return {"success": False, "message": str(e)}

@transaction.atomic
def create_event(data, club, request_user):
    """
    Create a new event
    Matches V5 - extracted from new_event()
    """
    try:
        event_name = data.get('event_name')
        incharge = data.get('incharge')
        venue = data.get('venue')
        event_poster = data.get('event_poster')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        details = data.get('details')
        
        event = Event_info.objects.create(
            club=club,
            event_name=event_name,
            incharge=incharge,
            venue=venue,
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            event_poster=event_poster,
            details=details,
            status='open'
        )
        
        # Send notifications
        from applications.globals.models import ExtraInfo
        students = ExtraInfo.objects.filter(user_type='student')
        recipients = User.objects.filter(extrainfo__in=students)
        gymkhana_event(request_user, recipients, "new_event", club, event_name, details, venue)
        
        return {"success": True, "event": event, "message": "Event created successfully"}
        
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        return {"success": False, "message": str(e)}

@transaction.atomic
def bulk_delete_objects(model, ids, user, permission_check=True):
    """
    Generic bulk delete utility
    Matches R2 from your plan
    """
    try:
        objects = model.objects.filter(id__in=ids)
        count = objects.count()
        
        if permission_check:
            # Add custom permission logic here
            pass
        
        objects.delete()
        return {"success": True, "deleted": count, "message": f"Deleted {count} items"}
        
    except Exception as e:
        logger.error(f"Error in bulk delete: {e}")
        return {"success": False, "message": str(e)}
    
@transaction.atomic
def bulk_approve_membership(club_name, member_ids, remarks_list):
    """
    Bulk approve multiple membership requests
    """
    club = get_object_or_404(Club_info, club_name=club_name)
    approved_count = 0
    
    for member_id, remarks in zip(member_ids, remarks_list):
        extra = get_object_or_404(ExtraInfo, id=member_id, user_type='student')
        student = get_object_or_404(Student, id=extra)
        
        member, created = Club_member.objects.update_or_create(
            club=club,
            member=student,
            defaults={'status': 'confirmed', 'remarks': remarks}
        )
        approved_count += 1
    
    return {"success": True, "approved": approved_count}
