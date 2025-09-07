# Password Email Management Views for Student Management

import json
import smtplib
import secrets
import string
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.hashers import check_password

from .models_student_management import StudentBatchUpload
from .models_password_email import (
    PasswordEmailLog, BulkPasswordEmailOperation, 
    StudentPasswordHistory, EmailTemplate
)


# =============================================================================
# PASSWORD GENERATION AND EMAIL UTILITIES
# =============================================================================

def generate_random_password(length=8):
    """
    Generate a secure random password
    """
    # Ensure password has at least one from each category
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%"
    
    # Generate password with guaranteed character variety
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase), 
        secrets.choice(digits),
        secrets.choice(special)
    ]
    
    # Fill remaining length with random choices
    all_chars = lowercase + uppercase + digits + special
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))
    
    # Shuffle the password list
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_email_template_context(student, password, additional_context=None):
    """
    Create context for email templates
    """
    context = {
        'student_name': student.name,
        'roll_number': student.roll_number or 'Not Assigned',
        'institute_email': student.institute_email,
        'jee_app_no': student.jee_app_no,
        'password': password,
        'programme': student.get_programme_name(),
        'branch': student.get_display_branch(),
        'year': student.year,
        'fusion_url': getattr(settings, 'FUSION_URL', 'http://fusion.iiitdmj.ac.in'),
        'current_date': datetime.now().strftime('%B %d, %Y'),
        'email_host_user': settings.EMAIL_HOST_USER,
        'institute_name': 'PDPM IIITDM Jabalpur'
    }
    
    if additional_context:
        context.update(additional_context)
    
    return context


def send_password_email_smtp(student_email, student_name, password, roll_number, student=None):
    """
    Send password email using SMTP configuration
    """
    try:
        # Validate required email settings
        if not hasattr(settings, 'EMAIL_HOST_USER') or not settings.EMAIL_HOST_USER:
            return False, "EMAIL_HOST_USER setting is not configured"
        
        if not hasattr(settings, 'EMAIL_HOST_USER') or not settings.EMAIL_HOST_USER:
            return False, "EMAIL_HOST_USER setting is not configured"
        
        # Get email template or use default
        try:
            template = EmailTemplate.objects.get(
                template_type='INITIAL_PASSWORD', 
                is_active=True
            )
            
            context = get_email_template_context(student, password)
            subject = template.render_subject(context)
            html_content = template.render_html(context)
            
        except EmailTemplate.DoesNotExist:
            # Default email template
            subject = f"FUSION - Login Credentials - {roll_number}"
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                        <h2 style="color: #007bff; margin-top: 0;">Welcome to FUSION Portal</h2>
                        <p style="font-size: 16px; margin-bottom: 0;">PDPM IIITDM Jabalpur</p>
                    </div>
                    
                    <p>Dear <strong>{student_name}</strong>,</p>
                    
                    <p>Your FUSION account has been created successfully. Please find your login credentials below:</p>
                    
                    <div style="background-color: #e3f2fd; padding: 20px; border-left: 4px solid #2196f3; margin: 20px 0; border-radius: 4px;">
                        <p style="margin: 8px 0;"><strong>URL:</strong> <a href="http://fusion.iiitdmj.ac.in" style="color: #1976d2;">http://fusion.iiitdmj.ac.in</a></p>
                        <p style="margin: 8px 0;"><strong>Username:</strong> <code style="background-color: #f5f5f5; padding: 4px 8px; border-radius: 3px; font-family: monospace;">{roll_number}</code></p>
                        <p style="margin: 8px 0;"><strong>Password:</strong> <code style="background-color: #fff3cd; padding: 4px 8px; border-radius: 3px; font-family: monospace; color: #856404; border: 1px solid #ffeaa7;">{password}</code></p>
                    </div>
                    
                    <div style="background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0; border-radius: 4px;">
                        <h4 style="margin-top: 0; color: #155724;">📞 Need Help?</h4>
                        <p style="margin-bottom: 0; color: #155724;">
                            For any login issues or technical support, please contact:<br>
                            📧 <a href="mailto:{settings.EMAIL_HOST_USER}" style="color: #155724;">{settings.EMAIL_HOST_USER}</a><br>
                            🏢 PDPM IIITDM Jabalpur
                        </p>
                    </div>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                        <p style="margin-bottom: 0;">Best regards,<br>
                        <strong>Fusion Development Team</strong><br>
                        PDPM IIITDM Jabalpur</p>
                    </div>
                    
                    <div style="margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 4px; font-size: 12px; color: #6c757d; text-align: center;">
                        This is an automated message generated by FUSION. Please do not reply to this email.
                        <br>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                    </div>
                </div>
            </body>
            </html>
            """
        
        # Use Django's email backend
        from django.core.mail import EmailMultiAlternatives
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=f"Your FUSION login credentials - Username: {roll_number}, Password: {password}",
            from_email=settings.EMAIL_HOST_USER,
            to=[student_email]
        )
        
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        return True, "Email sent successfully"
        
    except Exception as e:
        return False, str(e)


# =============================================================================
# PASSWORD EMAIL API ENDPOINTS
# =============================================================================

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def send_student_password(request):
    """
    Send password email to individual student
    """
    try:
        data = json.loads(request.body)
        student_id = data.get('studentId')
        student_email = data.get('studentEmail')
        student_name = data.get('studentName')
        
        # Validate required fields
        if not all([student_id, student_email, student_name]):
            return JsonResponse({
                'success': False, 
                'error': 'Missing required fields: studentId, studentEmail, studentName'
            })
        
        # Get student from database
        try:
            student = StudentBatchUpload.objects.get(id=student_id)
        except StudentBatchUpload.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': f'Student with ID {student_id} not found'
            })
        
        # Create email log entry
        email_log = PasswordEmailLog.objects.create(
            student=student,
            sent_to_email=student_email,
            sent_by=request.user,
            email_status='PENDING',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:200]
        )
        
        # Generate password and create/update user account
        with transaction.atomic():
            # Check if this is an initial password before creating/updating the account
            is_initial_password = not student.has_user_account()
            
            # Use the student model's built-in user account creation
            if student.has_user_account():
                # User exists, generate new password
                password = student.generate_secure_password()
                student.update_user_password(password)
                user = student.get_user_account()
            else:
                # Create new user account with hashed password in auth_user table
                user, password = student.create_user_account()
            
            # Create password history record
            StudentPasswordHistory.objects.create(
                student=student,
                password_hash=user.password,
                created_by=request.user,
                is_initial_password=is_initial_password,
                is_active=True
            )
        
        # Send email
        success, message = send_password_email_smtp(
            student_email=student_email,
            student_name=student_name,
            password=password,
            roll_number=student.roll_number or student.jee_app_no,
            student=student
        )
        
        if success:
            email_log.mark_as_sent(password)
            return JsonResponse({
                'success': True,
                'message': f'Password sent successfully to {student_email}',
                'email_log_id': email_log.id
            })
        else:
            email_log.mark_as_failed(message)
            return JsonResponse({
                'success': False,
                'error': f'Failed to send email: {message}',
                'email_log_id': email_log.id
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@login_required  
@require_http_methods(["POST"])
def bulk_send_passwords(request):
    """
    Send passwords to multiple students in bulk
    """
    try:
        data = json.loads(request.body)
        student_ids = data.get('studentIds', [])
        
        if not student_ids:
            return JsonResponse({'success': False, 'error': 'No students selected'})
        
        # Create bulk operation record
        operation_id = str(uuid.uuid4())[:8]
        bulk_operation = BulkPasswordEmailOperation.objects.create(
            operation_id=operation_id,
            initiated_by=request.user,
            total_students=len(student_ids),
            operation_status='IN_PROGRESS'
        )
        
        results = []
        successful_sends = 0
        failed_sends = 0
        
        for student_id in student_ids:
            try:
                student = StudentBatchUpload.objects.get(id=student_id)
                
                # Use institute email or personal email
                email_address = student.institute_email or student.personal_email
                if not email_address:
                    results.append({
                        'student_id': student_id,
                        'student_name': student.name,
                        'success': False,
                        'message': 'No email address found'
                    })
                    failed_sends += 1
                    continue
                
                # Create email log
                email_log = PasswordEmailLog.objects.create(
                    student=student,
                    sent_to_email=email_address,
                    sent_by=request.user,
                    email_status='PENDING',
                    ip_address=get_client_ip(request)
                )
                
                # Generate password and create user
                with transaction.atomic():
                    # Check if this is an initial password before creating/updating the account
                    is_initial_password = not student.has_user_account()
                    
                    # Use the student model's built-in user account creation
                    if student.has_user_account():
                        # User exists, generate new password
                        password = student.generate_secure_password()
                        student.update_user_password(password)
                        user = student.get_user_account()
                    else:
                        # Create new user account with hashed password in auth_user table
                        user, password = student.create_user_account()
                    
                    StudentPasswordHistory.objects.create(
                        student=student,
                        password_hash=user.password,  # Already hashed by Django
                        created_by=request.user,
                        is_initial_password=is_initial_password,
                        is_active=True
                    )
                
                # Send email
                success, message = send_password_email_smtp(
                    student_email=email_address,
                    student_name=student.name,
                    password=password,
                    roll_number=student.roll_number or student.jee_app_no,
                    student=student
                )
                
                if success:
                    email_log.mark_as_sent(password)
                    successful_sends += 1
                    results.append({
                        'student_id': student_id,
                        'student_name': student.name,
                        'success': True,
                        'message': f'Password sent to {email_address}'
                    })
                else:
                    email_log.mark_as_failed(message)
                    failed_sends += 1
                    results.append({
                        'student_id': student_id,
                        'student_name': student.name,
                        'success': False,
                        'message': f'Failed to send: {message}'
                    })
                    
            except StudentBatchUpload.DoesNotExist:
                failed_sends += 1
                results.append({
                    'student_id': student_id,
                    'success': False,
                    'message': 'Student not found'
                })
            except Exception as e:
                failed_sends += 1
                results.append({
                    'student_id': student_id,
                    'success': False,
                    'message': str(e)
                })
        
        # Update bulk operation
        bulk_operation.emails_sent = successful_sends
        bulk_operation.emails_failed = failed_sends
        bulk_operation.mark_completed()
        
        return JsonResponse({
            'success': True,
            'message': f'Bulk operation completed. {successful_sends}/{len(student_ids)} emails sent successfully.',
            'operation_id': operation_id,
            'successful_sends': successful_sends,
            'failed_sends': failed_sends,
            'results': results
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@login_required
@require_http_methods(["GET"])
def password_email_status(request, email_log_id):
    """
    Get status of a specific password email
    """
    try:
        email_log = PasswordEmailLog.objects.get(id=email_log_id)
        
        return JsonResponse({
            'success': True,
            'email_log': {
                'id': email_log.id,
                'student_name': email_log.student.name,
                'sent_to_email': email_log.sent_to_email,
                'email_status': email_log.email_status,
                'sent_at': email_log.sent_at.isoformat(),
                'attempts_count': email_log.attempts_count,
                'error_message': email_log.error_message
            }
        })
        
    except PasswordEmailLog.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Email log not found'})


@csrf_exempt
@login_required
@require_http_methods(["GET"])
def bulk_operation_status(request, operation_id):
    """
    Get status of a bulk password email operation
    """
    try:
        operation = BulkPasswordEmailOperation.objects.get(operation_id=operation_id)
        
        return JsonResponse({
            'success': True,
            'operation': {
                'operation_id': operation.operation_id,
                'operation_status': operation.operation_status,
                'total_students': operation.total_students,
                'emails_sent': operation.emails_sent,
                'emails_failed': operation.emails_failed,
                'completion_rate': operation.calculate_completion_rate(),
                'start_time': operation.start_time.isoformat(),
                'end_time': operation.end_time.isoformat() if operation.end_time else None,
                'duration_seconds': operation.duration_seconds
            }
        })
        
    except BulkPasswordEmailOperation.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bulk operation not found'})


# =============================================================================
# EMAIL TEMPLATE MANAGEMENT
# =============================================================================

@csrf_exempt
@login_required
@require_http_methods(["GET", "POST"])
def manage_email_templates(request):
    """
    Manage email templates for password emails
    """
    if request.method == "GET":
        templates = EmailTemplate.objects.all()
        return JsonResponse({
            'success': True,
            'templates': [
                {
                    'id': t.id,
                    'template_type': t.template_type,
                    'template_type_display': t.get_template_type_display(),
                    'subject_template': t.subject_template,
                    'is_active': t.is_active,
                    'updated_at': t.updated_at.isoformat()
                }
                for t in templates
            ]
        })
    
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            
            template, created = EmailTemplate.objects.update_or_create(
                template_type=data['template_type'],
                defaults={
                    'subject_template': data['subject_template'],
                    'html_template': data['html_template'],
                    'text_template': data.get('text_template', ''),
                    'is_active': data.get('is_active', True),
                    'created_by': request.user
                }
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Template saved successfully',
                'template_id': template.id,
                'created': created
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
