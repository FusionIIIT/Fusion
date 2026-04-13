"""
No Dues escalation service - Handles automated reminders and escalations.

Workflow:
- Day 0-6: Student has clear/notclear
- Day 7: Send 7-day reminder notification
- Day 14: Send 14-day reminder notification
- Day 21: Send 21-day reminder notification
- Day 30: Auto-mark as clear (if not already marked) and escalate record
- Day 30+: Record escalated to Dean/Director for investigation
"""
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings

from applications.otheracademic.models import NoDues
from applications.otheracademic.audit_models import (
    NoDuesEscalation,
    NoDuesClearanceHistory,
    AuditLog,
)
from notification.views import otheracademic_notif


class NoDuesEscalationService:
    """Service for handling No Dues escalation workflow."""
    
    # Day thresholds for escalation actions
    REMINDER_7_DAYS = 7
    REMINDER_14_DAYS = 14
    REMINDER_21_DAYS = 21
    AUTO_MARK_DAYS = 30
    ESCALATE_DEAN_DAYS = 31
    ESCALATE_DIRECTOR_DAYS = 45
    
    # Department/field mapping for No Dues
    CLEAR_FIELDS = {
        'library': 'library_clear',
        'hostel': 'hostel_clear',
        'mess': 'mess_clear',
        'ece': 'ece_clear',
        'physics_lab': 'physics_lab_clear',
        'mechatronics_lab': 'mechatronics_lab_clear',
        'cc': 'cc_clear',
        'workshop': 'workshop_clear',
        'signal_processing_lab': 'signal_processing_lab_clear',
        'vlsi': 'vlsi_clear',
        'design_studio': 'design_studio_clear',
        'design_project': 'design_project_clear',
        'bank': 'bank_clear',
        'icard_dsa': 'icard_dsa_clear',
        'account': 'account_clear',
        'btp_supervisor': 'btp_supervisor_clear',
        'discipline_office': 'discipline_office_clear',
        'student_gymkhana': 'student_gymkhana_clear',
        'alumni': 'alumni_clear',
        'placement_cell': 'placement_cell_clear',
    }
    
    NOT_CLEAR_FIELDS = {
        'library': 'library_notclear',
        'hostel': 'hostel_notclear',
        'mess': 'mess_notclear',
        'ece': 'ece_notclear',
        'physics_lab': 'physics_lab_notclear',
        'mechatronics_lab': 'mechatronics_lab_notclear',
        'cc': 'cc_notclear',
        'workshop': 'workshop_notclear',
        'signal_processing_lab': 'signal_processing_lab_notclear',
        'vlsi': 'vlsi_notclear',
        'design_studio': 'design_studio_notclear',
        'design_project': 'design_project_notclear',
        'bank': 'bank_notclear',
        'icard_dsa': 'icard_dsa_notclear',
        'account': 'account_notclear',
        'btp_supervisor': 'btp_supervisor_notclear',
        'discipline_office': 'discipline_office_notclear',
        'student_gymkhana': 'student_gymkhana_notclear',
        'alumni': 'alumni_notclear',
        'placement_cell': 'placement_cell_notclear',
    }
    
    @staticmethod
    def check_and_escalate_all():
        """
        Main escalation check - should be run daily via Celery beat task.
        Checks all No Dues records and triggers escalations as needed.
        """
        results = {
            'checked': 0,
            'reminders_sent': 0,
            'auto_marked': 0,
            'escalated_dean': 0,
            'escalated_director': 0,
            'errors': []
        }
        
        try:
            # Get all No Dues records where any field is not cleared
            records_to_check = NoDues.objects.all()
            
            for record in records_to_check:
                results['checked'] += 1
                try:
                    result = NoDuesEscalationService.check_and_escalate_record(record)
                    results['reminders_sent'] += result.get('reminders_sent', 0)
                    results['auto_marked'] += result.get('auto_marked', 0)
                    results['escalated_dean'] += result.get('escalated_dean', 0)
                    results['escalated_director'] += result.get('escalated_director', 0)
                except Exception as e:
                    results['errors'].append(f"Error processing {record.roll_no}: {str(e)}")
        
        except Exception as e:
            results['errors'].append(f"Fatal error in escalation check: {str(e)}")
        
        return results
    
    @staticmethod
    def check_and_escalate_record(no_dues_record):
        """
        Check a single No Dues record and trigger escalations if needed.
        
        Args:
            no_dues_record: NoDues model instance
        
        Returns:
            dict with escalation results
        """
        result = {
            'reminders_sent': 0,
            'auto_marked': 0,
            'escalated_dean': 0,
            'escalated_director': 0,
        }
        
        student = no_dues_record.roll_no.user
        
        # Check each department for missing clearance
        for dept_name, clear_field in NoDuesEscalationService.CLEAR_FIELDS.items():
            notclear_field = NoDuesEscalationService.NOT_CLEAR_FIELDS.get(dept_name)
            if not notclear_field:
                continue
            
            is_clear = getattr(no_dues_record, clear_field, False)
            is_notclear = getattr(no_dues_record, notclear_field, False)
            
            # Skip if already cleared or marked not clear
            if is_clear or is_notclear:
                continue
            
            # Find or create escalation record
            escalation_rec, created = NoDuesEscalation.objects.get_or_create(
                no_dues=no_dues_record,
                student=student,
                department=dept_name,
                clear_field=clear_field,
            )
            
            # Get creation date and calculate days elapsed
            days_elapsed = (timezone.now() - escalation_rec.created_at).days
            
            # Check escalation thresholds
            if days_elapsed >= NoDuesEscalationService.AUTO_MARK_DAYS:
                # Auto-mark as clear
                if not escalation_rec.escalation_type or escalation_rec.status != 'completed':
                    NoDuesEscalationService._auto_mark_clear(no_dues_record, student, dept_name)
                    result['auto_marked'] += 1
                    escalation_rec.escalation_type = 'auto_mark_30day'
                    escalation_rec.status = 'completed'
                    escalation_rec.completed_at = timezone.now()
                    escalation_rec.save()
            
            elif days_elapsed >= NoDuesEscalationService.REMINDER_21_DAYS:
                # Send 21-day reminder
                if not NoDuesEscalation.objects.filter(
                    no_dues=no_dues_record,
                    student=student,
                    department=dept_name,
                    escalation_type='reminder_21day',
                    status='sent'
                ).exists():
                    NoDuesEscalationService._send_reminder(
                        no_dues_record, student, dept_name, 'reminder_21day', 21
                    )
                    result['reminders_sent'] += 1
            
            elif days_elapsed >= NoDuesEscalationService.REMINDER_14_DAYS:
                # Send 14-day reminder
                if not NoDuesEscalation.objects.filter(
                    no_dues=no_dues_record,
                    student=student,
                    department=dept_name,
                    escalation_type='reminder_14day',
                    status='sent'
                ).exists():
                    NoDuesEscalationService._send_reminder(
                        no_dues_record, student, dept_name, 'reminder_14day', 14
                    )
                    result['reminders_sent'] += 1
            
            elif days_elapsed >= NoDuesEscalationService.REMINDER_7_DAYS:
                # Send 7-day reminder
                if not NoDuesEscalation.objects.filter(
                    no_dues=no_dues_record,
                    student=student,
                    department=dept_name,
                    escalation_type='reminder_7day',
                    status='sent'
                ).exists():
                    NoDuesEscalationService._send_reminder(
                        no_dues_record, student, dept_name, 'reminder_7day', 7
                    )
                    result['reminders_sent'] += 1
        
        return result
    
    @staticmethod
    def _send_reminder(no_dues_record, student, department, reminder_type, days):
        """Send reminder notification to student."""
        try:
            # Create escalation record
            escalation = NoDuesEscalation.objects.create(
                no_dues=no_dues_record,
                student=student,
                escalation_type=reminder_type,
                status='sent',
                triggered_at=timezone.now(),
                department=department,
                clear_field=NoDuesEscalationService.CLEAR_FIELDS.get(department, ''),
                notification_sent_to=student.email,
            )
            
            # Send notification
            try:
                message = f"No Dues clearance from {department} is pending for {days} days. Please complete the process."
                otheracademic_notif(user=student, message=message, sender_name='No Dues System')
            except Exception as e:
                escalation.notification_response = f"Error sending notification: {str(e)}"
                escalation.save()
            
            # Log the action
            AuditLog.log_change(
                user=student,
                model_name='NoDues',
                object_id=no_dues_record.id,
                action='escalate',
                field_name=NoDuesEscalationService.CLEAR_FIELDS.get(department, ''),
                new_value=reminder_type,
                description=f"Automated {days}-day reminder for {department} clearance",
                department=department,
                related_user=student,
            )
            
            return True
        except Exception as e:
            print(f"Error sending reminder for {student.username}: {str(e)}")
            return False
    
    @staticmethod
    def _auto_mark_clear(no_dues_record, student, department):
        """
        Auto-mark a department as clear after 30 days of inactivity.
        
        This is a default action for fairness - student shouldn't be blocked
        forever due to administrative delays.
        """
        try:
            clear_field = NoDuesEscalationService.CLEAR_FIELDS.get(department)
            if not clear_field:
                return False
            
            # Store old value for audit
            old_value = getattr(no_dues_record, clear_field, False)
            
            # Mark as clear
            setattr(no_dues_record, clear_field, True)
            no_dues_record.save(update_fields=[clear_field])
            
            # Record history
            NoDuesClearanceHistory.objects.create(
                no_dues=no_dues_record,
                student=student,
                department=department,
                clear_field=clear_field,
                previous_status='pending',
                new_status='clear',
                changed_by=None,  # System action
                reason='Auto-marked after 30 days of inactivity (fairness rule)',
            )
            
            # Log the action
            AuditLog.log_change(
                user=student,
                model_name='NoDues',
                object_id=no_dues_record.id,
                action='auto_mark_30day',
                field_name=clear_field,
                old_value=old_value,
                new_value=True,
                description=f"Auto-marked {department} as clear after 30 days",
                department=department,
                related_user=student,
            )
            
            # Send notification to student
            message = f"No Dues clearance for {department} has been auto-approved after 30 days. You can now complete your graduation/clearance process."
            otheracademic_notif(user=student, message=message, sender_name='No Dues System')
            
            return True
        except Exception as e:
            print(f"Error auto-marking {department} for {student.username}: {str(e)}")
            return False
    
    @staticmethod
    def mark_clear_manually(no_dues_record, department, admin_user, reason=''):
        """
        Manually mark a department as clear (admin action).
        
        Args:
            no_dues_record: NoDues instance
            department: Department name
            admin_user: User making the change
            reason: Reason for clearing
        
        Returns:
            bool - Success/failure
        """
        try:
            student = no_dues_record.roll_no.user
            clear_field = NoDuesEscalationService.CLEAR_FIELDS.get(department)
            notclear_field = NoDuesEscalationService.NOT_CLEAR_FIELDS.get(department)
            
            if not clear_field:
                raise ValueError(f"Invalid department: {department}")
            
            # Store old values
            old_clear = getattr(no_dues_record, clear_field, False)
            old_notclear = getattr(no_dues_record, notclear_field, False)
            
            # Mark as clear and remove notclear
            setattr(no_dues_record, clear_field, True)
            setattr(no_dues_record, notclear_field, False)
            no_dues_record.save(update_fields=[clear_field, notclear_field])
            
            # Record history
            NoDuesClearanceHistory.objects.create(
                no_dues=no_dues_record,
                student=student,
                department=department,
                clear_field=clear_field,
                previous_status='pending' if not old_notclear else 'notclear',
                new_status='clear',
                changed_by=admin_user,
                reason=reason,
            )
            
            # Log the action
            AuditLog.log_change(
                user=admin_user,
                model_name='NoDues',
                object_id=no_dues_record.id,
                action='approve',
                field_name=clear_field,
                old_value={'clear': old_clear, 'notclear': old_notclear},
                new_value={'clear': True, 'notclear': False},
                description=f"Manually approved {department} clearance" + (f": {reason}" if reason else ""),
                department=department,
                related_user=student,
            )
            
            return True
        except Exception as e:
            print(f"Error marking {department} clear for {student.username}: {str(e)}")
            return False
    
    @staticmethod
    def mark_notclear_manually(no_dues_record, department, admin_user, reason=''):
        """
        Manually mark a department as NOT clear (admin action).
        
        Args:
            no_dues_record: NoDues instance
            department: Department name
            admin_user: User making the change
            reason: Reason for marking not clear
        
        Returns:
            bool - Success/failure
        """
        try:
            student = no_dues_record.roll_no.user
            clear_field = NoDuesEscalationService.CLEAR_FIELDS.get(department)
            notclear_field = NoDuesEscalationService.NOT_CLEAR_FIELDS.get(department)
            
            if not notclear_field:
                raise ValueError(f"Invalid department: {department}")
            
            # Store old values
            old_clear = getattr(no_dues_record, clear_field, False)
            old_notclear = getattr(no_dues_record, notclear_field, False)
            
            # Mark as not clear and remove clear
            setattr(no_dues_record, clear_field, False)
            setattr(no_dues_record, notclear_field, True)
            no_dues_record.save(update_fields=[clear_field, notclear_field])
            
            # Record history
            NoDuesClearanceHistory.objects.create(
                no_dues=no_dues_record,
                student=student,
                department=department,
                clear_field=clear_field,
                previous_status='clear' if old_clear else 'pending',
                new_status='notclear',
                changed_by=admin_user,
                reason=reason,
            )
            
            # Log the action
            AuditLog.log_change(
                user=admin_user,
                model_name='NoDues',
                object_id=no_dues_record.id,
                action='reject',
                field_name=clear_field,
                old_value={'clear': old_clear, 'notclear': old_notclear},
                new_value={'clear': False, 'notclear': True},
                description=f"Marked {department} as not clear" + (f": {reason}" if reason else ""),
                department=department,
                related_user=student,
            )
            
            # Send notification
            message = f"No Dues clearance for {department} has been marked as not clear. Reason: {reason}. Please contact the {department} office."
            otheracademic_notif(user=student, message=message, sender_name='No Dues System')
            
            return True
        except Exception as e:
            print(f"Error marking {department} not clear for {student.username}: {str(e)}")
            return False
    
    @staticmethod
    def get_escalation_status(student):
        """Get escalation status for a student."""
        escalations = NoDuesEscalation.objects.filter(student=student).order_by('-created_at')
        return {
            'total_escalations': escalations.count(),
            'pending': escalations.filter(status='pending').count(),
            'sent': escalations.filter(status='sent').count(),
            'recent': [
                {
                    'department': e.department,
                    'type': e.escalation_type,
                    'status': e.status,
                    'created': e.created_at.isoformat(),
                }
                for e in escalations[:10]
            ]
        }
    
    @staticmethod
    def get_student_history(student):
        """Get complete clearance history for a student."""
        history = NoDuesClearanceHistory.objects.filter(student=student).order_by('-changed_at')
        return [
            {
                'department': h.department,
                'from_status': h.previous_status,
                'to_status': h.new_status,
                'changed_by': h.changed_by.username if h.changed_by else 'System',
                'changed_at': h.changed_at.isoformat(),
                'reason': h.reason,
            }
            for h in history
        ]
