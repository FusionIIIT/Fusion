from datetime import date, datetime

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo, HoldsDesignation
from .helpers import (
    get_special_request_document,
    get_request_status_key,
    is_escalated_request_status,
    normalize_request_status,
    normalize_special_request_type,
    validate_special_food_request,
)
from .models import (
    Menu,
    MenuPoll,
    MenuPollOption,
    MenuPollVote,
    Mess_reg,
    Messinfo,
    Monthly_bill,
    Payments,
    Rebate,
    Special_request,
    Feedback,
    RegistrationRequest,
    DeregistrationRequest,
    PaymentUpdateRequest,
    MessAnnouncement,
)
from .serializers import (
    MenuSerializer,
    MenuPollSerializer,
    MessinfoSerializer,
    MessRegSerializer,
    MonthlyBillSerializer,
    PaymentsSerializer,
    RebateSerializer,
    SpecialRequestSerializer,
    FeedbackSerializer,
    StudentSerializer,
    RegistrationRequestSerializer,
    DeregistrationRequestSerializer,
    PaymentUpdateRequestSerializer,
    MessAnnouncementSerializer,
)
from notification.views import central_mess_notif


def get_student(user):
    try:
        extrainfo = ExtraInfo.objects.get(user=user)
        return Student.objects.select_related('id', 'id__user').get(id=extrainfo)
    except (ExtraInfo.DoesNotExist, Student.DoesNotExist):
        return None


def normalize_designation_token(value):
    return str(value or '').strip().lower().replace('-', '_').replace(' ', '_')


def get_user_designation_tokens(user):
    if not user.is_authenticated:
        return set()

    tokens = set()
    designations = HoldsDesignation.objects.filter(
        Q(user=user) | Q(working=user)
    ).select_related('designation')

    for hold in designations:
        tokens.add(normalize_designation_token(hold.designation.name))
        tokens.add(normalize_designation_token(hold.designation.full_name))

    tokens.discard('')
    return tokens


def is_mess_manager(user):
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    designations = get_user_designation_tokens(user)
    if designations.intersection({
        'mess_manager',
        'mess_caretaker',
        'messcaretaker',
        'mess_warden',
        'messwarden',
    }):
        return True

    return any(
        designation.startswith('mess_committee') or
        designation.startswith('mess_convener')
        for designation in designations
    )


def is_mess_warden(user):
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    designations = get_user_designation_tokens(user)
    return bool(designations.intersection({'mess_warden', 'messwarden'}))


def get_mess_warden_users():
    users = []
    seen = set()
    for hold in HoldsDesignation.objects.filter(
        Q(designation__name__iexact='mess_warden') |
        Q(designation__name__iexact='mess warden') |
        Q(designation__full_name__iexact='mess_warden') |
        Q(designation__full_name__iexact='mess warden')
    ).select_related('user', 'working'):
        candidate = hold.working or hold.user
        if candidate and candidate.id not in seen:
            seen.add(candidate.id)
            users.append(candidate)
    return users


def can_access_mess_operations(user):
    return is_mess_manager(user) or is_mess_warden(user)


def parse_date(value, field_name):
    if not value:
        raise ValueError('{} is required'.format(field_name))
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value), '%Y-%m-%d').date()
    except ValueError:
        raise ValueError('{} must be in YYYY-MM-DD format'.format(field_name))


def get_bill_balance(student):
    total_bill = Monthly_bill.objects.filter(student_id=student).aggregate(
        total=Sum('total_bill')
    )['total'] or 0
    total_paid = Payments.objects.filter(student_id=student, status='accept').aggregate(
        total=Sum('amount_paid')
    )['total'] or 0
    return total_bill - total_paid


def get_student_mess_option(student):
    mess_info = Messinfo.objects.filter(student_id=student).first()
    return mess_info.mess_option if mess_info else None


def get_menu_poll_queryset():
    return MenuPoll.objects.select_related('created_by').prefetch_related(
        'votes',
        'options',
        'options__votes',
    ).order_by('-created_at')


def get_visible_announcement_queryset():
    today = date.today()
    return MessAnnouncement.objects.filter(
        is_active=True,
        publish_date__lte=today,
    ).filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gte=today)
    )


def validate_rebate_window(student, start_date, end_date):
    if start_date < date.today():
        return 'Rebate requests must be submitted before the leave start date.'

    if end_date < start_date:
        return 'End date must be on or after start date.'

    overlap = Rebate.objects.filter(
        student_id=student,
        start_date__lte=end_date,
        end_date__gte=start_date,
    ).exists()
    if overlap:
        return 'A rebate request already exists for the selected dates.'

    approved_days = 0
    for rebate in Rebate.objects.filter(student_id=student, status='2'):
        approved_days += (rebate.end_date - rebate.start_date).days + 1

    requested_days = (end_date - start_date).days + 1
    # WF-101: Escalate to Warden instead of rejecting
    if approved_days + requested_days > 20:
        return 'ESCALATE'

    return None


def normalize_feedback_type(value):
    feedback_map = {
        'food': 'food',
        'cleanliness': 'cleanliness',
        'maintenance': 'maintenance',
        'others': 'others',
    }
    return feedback_map.get(str(value).strip().lower())


def feedback_label(value):
    label_map = {
        'food': 'Food',
        'cleanliness': 'Cleanliness',
        'maintenance': 'Maintenance',
        'others': 'Others',
        'Food': 'Food',
        'Cleanliness': 'Cleanliness',
        'Maintenance': 'Maintenance',
        'Others': 'Others',
    }
    return label_map.get(value, value)


def normalize_poll_options(options):
    if not isinstance(options, list):
        raise ValueError('Options must be provided as a list.')

    normalized = []
    seen = set()
    for option in options:
        if isinstance(option, dict):
            text = option.get('option_text') or option.get('label') or option.get('text')
        else:
            text = option
        text = str(text or '').strip()
        lowered = text.lower()
        if not text or lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(text)

    if len(normalized) < 2:
        raise ValueError('At least two unique poll options are required.')

    return normalized


def normalize_announcement_priority(value):
    priority = str(value or 'normal').strip().lower()
    if priority in {'normal', 'high', 'urgent'}:
        return priority
    return None


def parse_bool(value, default=None):
    if value in (None, ''):
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {'true', '1', 'yes', 'on'}:
        return True
    if normalized in {'false', '0', 'no', 'off'}:
        return False
    return default


REQUEST_REVIEW_CONFIG = {
    'registration': {
        'model': RegistrationRequest,
        'status_kind': 'request',
        'remark_field': 'registration_remark',
        'label': 'Registration Request',
        'document_field': 'img',
    },
    'deregistration': {
        'model': DeregistrationRequest,
        'status_kind': 'request',
        'remark_field': 'deregistration_remark',
        'label': 'Deregistration Request',
    },
    'payment_update': {
        'model': PaymentUpdateRequest,
        'status_kind': 'request',
        'remark_field': 'update_remark',
        'label': 'Payment Update Request',
        'document_field': 'img',
    },
    'rebate': {
        'model': Rebate,
        'status_kind': 'numeric',
        'remark_field': 'rebate_remark',
        'label': 'Rebate Request',
    },
    'special_request': {
        'model': Special_request,
        'status_kind': 'numeric',
        'remark_field': 'special_request_remark',
        'label': 'Special Food Request',
        'document_field': 'supporting_document',
    },
}


def apply_registration_acceptance(reg_request):
    Messinfo.objects.update_or_create(
        student_id=reg_request.student_id,
        defaults={'mess_option': reg_request.mess_option},
    )
    mess_reg = Mess_reg.objects.order_by('-id').first()
    payment_year = reg_request.payment_date.year
    Payments.objects.update_or_create(
        student_id=reg_request.student_id,
        sem=mess_reg.sem if mess_reg else reg_request.student_id.curr_semester_no,
        year=payment_year,
        defaults={
            'amount_paid': reg_request.amount,
            'payment_date': reg_request.payment_date,
            'payment_month': reg_request.payment_date.strftime('%B'),
            'payment_year': payment_year,
            'Txn_no': reg_request.Txn_no,
            'status': 'accept',
        }
    )


def apply_deregistration_acceptance(dereg_request):
    Messinfo.objects.filter(student_id=dereg_request.student_id).delete()


def apply_payment_update_acceptance(payment_request):
    payment_year = payment_request.payment_date.year
    Payments.objects.update_or_create(
        student_id=payment_request.student_id,
        sem=payment_request.student_id.curr_semester_no,
        year=payment_year,
        defaults={
            'amount_paid': payment_request.amount,
            'payment_date': payment_request.payment_date,
            'payment_month': payment_request.payment_date.strftime('%B'),
            'payment_year': payment_year,
            'Txn_no': payment_request.Txn_no,
            'status': 'accept',
        }
    )


def notify_wardens_of_escalation(sender, request_label, obj, escalation_remark):
    student_id = obj.student_id.id.user.username
    message = '{} for {} has been escalated. {}'.format(
        request_label,
        student_id,
        escalation_remark or 'Review is required from the mess warden.',
    )
    for recipient in get_mess_warden_users():
        central_mess_notif(sender, recipient, 'escalated_request', message)


def notify_student_of_warden_decision(sender, request_label, obj, decision_key,
                                      warden_remark, override_conditions):
    decision_label = 'approved' if decision_key == 'accept' else 'rejected'
    details = []
    if warden_remark:
        details.append(warden_remark)
    if override_conditions:
        details.append('Override conditions: {}'.format(override_conditions))
    suffix = ' {}'.format(' '.join(details)) if details else ''
    message = 'Your {} has been {} by the mess warden.{}'.format(
        request_label.lower(),
        decision_label,
        suffix,
    )
    central_mess_notif(sender, obj.student_id.id.user, 'warden_decision', message)


def get_request_summary(request_type, obj):
    if request_type == 'registration':
        return '{} from {}'.format(obj.get_mess_option_display(), obj.start_date)
    if request_type == 'deregistration':
        return 'Requested end date {}'.format(obj.end_date)
    if request_type == 'payment_update':
        return 'Txn {} for {}'.format(obj.Txn_no, obj.amount)
    if request_type == 'rebate':
        return '{} leave from {} to {}'.format(
            obj.get_leave_type_display(), obj.start_date, obj.end_date
        )
    if request_type == 'special_request':
        return '{} / {} ({})'.format(
            obj.item1,
            obj.item2,
            obj.get_request_type_display(),
        )
    return str(obj.id)


def get_request_details(request_type, obj):
    if request_type == 'registration':
        return {
            'Mess option': obj.get_mess_option_display(),
            'Start date': str(obj.start_date),
            'Payment date': str(obj.payment_date),
            'Amount': str(obj.amount),
            'Transaction no': obj.Txn_no,
        }
    if request_type == 'deregistration':
        return {
            'End date': str(obj.end_date),
        }
    if request_type == 'payment_update':
        return {
            'Amount': str(obj.amount),
            'Payment date': str(obj.payment_date),
            'Transaction no': obj.Txn_no,
        }
    if request_type == 'rebate':
        return {
            'Leave type': obj.get_leave_type_display(),
            'Start date': str(obj.start_date),
            'End date': str(obj.end_date),
            'Purpose': obj.purpose,
        }
    if request_type == 'special_request':
        return {
            'Request type': obj.get_request_type_display(),
            'Food choice': obj.item1,
            'Meal timing': obj.item2,
            'From': str(obj.start_date),
            'To': str(obj.end_date),
            'Reason': obj.request,
        }
    return {}


def serialize_warden_queue_item(request_type, obj):
    config = REQUEST_REVIEW_CONFIG[request_type]
    attachment = getattr(obj, config.get('document_field', ''), None) if config.get('document_field') else None
    document_url = ''
    if attachment:
        try:
            document_url = attachment.url
        except ValueError:
            document_url = ''

    submitted_at = getattr(obj, 'created_at', None) or getattr(obj, 'app_date', None)
    return {
        'id': obj.id,
        'request_type': request_type,
        'request_label': config['label'],
        'student_id': obj.student_id.id.user.username,
        'status': get_request_status_key(obj.status, config['status_kind']),
        'submitted_at': submitted_at,
        'escalated_at': obj.escalated_at,
        'manager_remark': getattr(obj, config['remark_field'], ''),
        'escalation_remark': obj.escalation_remark,
        'warden_remark': obj.warden_remark,
        'override_conditions': obj.override_conditions,
        'summary': get_request_summary(request_type, obj),
        'details': get_request_details(request_type, obj),
        'document_url': document_url,
    }


def get_request_object(request_type, request_id):
    config = REQUEST_REVIEW_CONFIG.get(request_type)
    if not config:
        return None, None
    return config, config['model'].objects.filter(id=request_id).select_related(
        'student_id', 'student_id__id', 'student_id__id__user'
    ).first()


def persist_final_remark(obj, config, warden_remark, override_conditions):
    remark_parts = [part.strip() for part in [warden_remark, override_conditions] if part and part.strip()]
    if remark_parts:
        setattr(obj, config['remark_field'], ' | '.join(remark_parts))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mess_operations_board_api(request):
    if not can_access_mess_operations(request.user):
        return Response(
            {'error': 'Only mess staff can access the operations board.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    payload = {
        'feedback': Feedback.objects.filter(is_read=False).count(),
        'pendingRebates': Rebate.objects.filter(status='1').count(),
        'pendingSpecialFood': Special_request.objects.filter(status='1').count(),
        'pendingRegistrations': RegistrationRequest.objects.filter(
            status='pending'
        ).count(),
        'pendingPayments': PaymentUpdateRequest.objects.filter(
            status='pending'
        ).count(),
    }
    return Response({'payload': payload}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def mess_announcement_api(request):
    if request.method == 'GET':
        queryset = MessAnnouncement.objects.all() if is_mess_manager(
            request.user
        ) else get_visible_announcement_queryset()
        serializer = MessAnnouncementSerializer(queryset, many=True)
        return Response({'payload': serializer.data}, status=status.HTTP_200_OK)

    if not is_mess_manager(request.user):
        return Response({'error': 'Only mess managers can manage announcements.'},
                        status=status.HTTP_403_FORBIDDEN)

    if request.method == 'POST':
        title = str(request.data.get('title', '')).strip()
        message = str(request.data.get('message', '')).strip()
        if not title or not message:
            return Response({'message': 'Title and message are required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            publish_date = parse_date(
                request.data.get('publish_date') or date.today(),
                'publish_date',
            )
            expiry_raw = request.data.get('expiry_date')
            expiry_date = parse_date(expiry_raw, 'expiry_date') if expiry_raw else None
        except ValueError as exc:
            return Response({'message': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if expiry_date and expiry_date < publish_date:
            return Response({'message': 'Expiry date must be on or after publish date.'},
                            status=status.HTTP_400_BAD_REQUEST)

        priority = normalize_announcement_priority(request.data.get('priority'))
        if not priority:
            return Response({'message': 'Priority must be normal, high, or urgent.'},
                            status=status.HTTP_400_BAD_REQUEST)

        announcement = MessAnnouncement.objects.create(
            title=title,
            message=message,
            priority=priority,
            publish_date=publish_date,
            expiry_date=expiry_date,
            is_active=parse_bool(request.data.get('is_active'), True),
            created_by=request.user,
        )
        try:
            # BR-MMS-008 & BR-MMS-011: Global portal announcements visibility
            from notification.views import central_mess_notif
            central_mess_notif(request.user, request.user, 'global_announcement', 'Global Mess Announcement: ' + title)
        except Exception:
            pass
        return Response({
            'message': 'Announcement published successfully.',
            'payload': MessAnnouncementSerializer(announcement).data,
        }, status=status.HTTP_201_CREATED)

    announcement = MessAnnouncement.objects.filter(id=request.data.get('id')).first()
    if not announcement:
        return Response({'error': 'Announcement not found.'},
                        status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        announcement.is_active = False
        announcement.save(update_fields=['is_active', 'updated_at'])
        return Response({'message': 'Announcement archived successfully.'},
                        status=status.HTTP_200_OK)

    title = str(request.data.get('title', announcement.title)).strip()
    message = str(request.data.get('message', announcement.message)).strip()
    if not title or not message:
        return Response({'message': 'Title and message are required.'},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        publish_value = request.data.get('publish_date', announcement.publish_date)
        publish_date = parse_date(publish_value, 'publish_date')
        expiry_value = request.data.get('expiry_date', announcement.expiry_date)
        expiry_date = parse_date(expiry_value, 'expiry_date') if expiry_value else None
    except ValueError as exc:
        return Response({'message': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    if expiry_date and expiry_date < publish_date:
        return Response({'message': 'Expiry date must be on or after publish date.'},
                        status=status.HTTP_400_BAD_REQUEST)

    priority = normalize_announcement_priority(
        request.data.get('priority', announcement.priority)
    )
    if not priority:
        return Response({'message': 'Priority must be normal, high, or urgent.'},
                        status=status.HTTP_400_BAD_REQUEST)

    announcement.title = title
    announcement.message = message
    announcement.priority = priority
    announcement.publish_date = publish_date
    announcement.expiry_date = expiry_date
    if 'is_active' in request.data:
        announcement.is_active = parse_bool(
            request.data.get('is_active'),
            announcement.is_active,
        )
    announcement.save()
    return Response({
        'message': 'Announcement updated successfully.',
        'payload': MessAnnouncementSerializer(announcement).data,
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def menu_api(request):
    if request.method == 'PUT':
        if not is_mess_manager(request.user):
            return Response({'error': 'Only mess managers can update the menu.'},
                            status=status.HTTP_403_FORBIDDEN)

        mess_option = request.data.get('mess_option')
        entries = request.data.get('entries', [])
        if mess_option not in {'mess1', 'mess2'}:
            return Response({'message': 'Select a valid mess option.'}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(entries, list) or not entries:
            return Response({'message': 'Menu entries are required.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            for entry in entries:
                meal_time = entry.get('meal_time')
                dish = str(entry.get('dish', '')).strip()
                if not meal_time or not dish:
                    continue
                Menu.objects.update_or_create(
                    mess_option=mess_option,
                    meal_time=meal_time,
                    defaults={'dish': dish},
                )

        menu = Menu.objects.filter(mess_option=mess_option)
        return Response({
            'message': 'Menu updated successfully.',
            'payload': MenuSerializer(menu, many=True).data,
        }, status=status.HTTP_200_OK)

    student = get_student(request.user)
    if student:
        mess_info = Messinfo.objects.filter(student_id=student).first()
        mess_option = mess_info.mess_option if mess_info else 'mess2'
        menu = Menu.objects.filter(mess_option=mess_option)
        serializer = MenuSerializer(menu, many=True)
        return Response({
            'payload': serializer.data,
            'mess_option': mess_option,
        }, status=status.HTTP_200_OK)

    if is_mess_manager(request.user):
        menu = Menu.objects.all()
        serializer = MenuSerializer(menu, many=True)
        return Response({
            'payload': serializer.data,
            'mess_option': None,
        }, status=status.HTTP_200_OK)

    return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)



@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def get_operational_report_api(request):
    if not is_mess_manager(request.user):
        return Response({'error': 'Only warden/manager can access operational report'}, status=status.HTTP_403_FORBIDDEN)
    
    # Aggregating data across the system
    import datetime
    from .models import Messinfo, Monthly_bill, Mess_reg
    
    total_students = Messinfo.objects.count()
    total_mess1 = Messinfo.objects.filter(mess_option='mess1').count()
    total_mess2 = Messinfo.objects.filter(mess_option='mess2').count()
    unpaid_bills = Monthly_bill.objects.filter(amount__gt=0).count()
    active_registrations = Mess_reg.objects.count()
    
    report = {
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'total_students_enrolled': total_students,
        'mess1_enrollment': total_mess1,
        'mess2_enrollment': total_mess2,
        'unpaid_bills_count': unpaid_bills,
        'active_registrations': active_registrations
    }
    
    return Response({'payload': report}, status=status.HTTP_200_OK)

@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
def refund_cancellation_api(request):
    from .models import RefundCancellation
    if request.method == 'GET':
        if is_mess_manager(request.user):
            refunds = RefundCancellation.objects.all()
        else:
            student = get_student(request.user)
            refunds = RefundCancellation.objects.filter(student_id=student)
        
        data = []
        for r in refunds:
            data.append({
                'id': r.id,
                'student_id': r.student_id.id,
                'amount': r.amount,
                'reason': r.reason,
                'warden_approved': r.warden_approved,
                'finance_processed': r.finance_processed,
                'timestamp': r.timestamp
            })
        return Response({'payload': data}, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        student = get_student(request.user)
        amount = int(request.data.get('amount', 0))
        reason = request.data.get('reason', '')
        
        ref = RefundCancellation.objects.create(
            student_id=student,
            amount=amount,
            reason=reason
        )
        return Response({'message': 'Refund request created', 'id': ref.id}, status=status.HTTP_201_CREATED)
        
    elif request.method == 'PUT':
        if not is_mess_manager(request.user):
            return Response({'error': 'Only warden/manager can update refunds'}, status=status.HTTP_403_FORBIDDEN)
            
        req_id = request.data.get('id')
        try:
            ref = RefundCancellation.objects.get(id=req_id)
            if 'warden_approved' in request.data:
                ref.warden_approved = request.data['warden_approved']
            if 'finance_processed' in request.data:
                ref.finance_processed = request.data['finance_processed']
            ref.save()
            return Response({'message': 'Refund updated'}, status=status.HTTP_200_OK)
        except RefundCancellation.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
def menu_poll_api(request):
    student = get_student(request.user)
    student_mess_option = get_student_mess_option(student) if student else None

    if request.method == 'GET':
        if student:
            queryset = get_menu_poll_queryset().filter(mess_option=student_mess_option) if student_mess_option else MenuPoll.objects.none()
            serializer = MenuPollSerializer(
                queryset, many=True,
                context={
                    'student': student,
                    'student_mess_option': student_mess_option,
                }
            )
            return Response({
                'payload': serializer.data,
                'mess_option': student_mess_option,
            }, status=status.HTTP_200_OK)

        if is_mess_manager(request.user):
            serializer = MenuPollSerializer(get_menu_poll_queryset(), many=True)
            return Response({'payload': serializer.data}, status=status.HTTP_200_OK)

        return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        if not is_mess_manager(request.user):
            return Response({'error': 'Only mess managers can create menu polls.'},
                            status=status.HTTP_403_FORBIDDEN)

        question = str(request.data.get('question', '')).strip()
        description = str(request.data.get('description', '')).strip()
        mess_option = request.data.get('mess_option')
        meal_time = request.data.get('meal_time') or None
        poll_date_value = request.data.get('poll_date') or None
        poll_status = request.data.get('status', 'open')

        if not question:
            return Response({'message': 'Poll question is required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if mess_option not in {'mess1', 'mess2'}:
            return Response({'message': 'Select a valid mess option.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if meal_time and meal_time not in dict(Menu._meta.get_field('meal_time').choices):
            return Response({'message': 'Select a valid meal time.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if poll_status not in {'open', 'closed'}:
            return Response({'message': 'Status must be open or closed.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            options = normalize_poll_options(request.data.get('options', []))
        except ValueError as exc:
            return Response({'message': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        poll_date = None
        if poll_date_value:
            try:
                poll_date = parse_date(poll_date_value, 'poll_date')
            except ValueError as exc:
                return Response({'message': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            poll = MenuPoll.objects.create(
                question=question,
                description=description,
                mess_option=mess_option,
                meal_time=meal_time,
                poll_date=poll_date,
                status=poll_status,
                created_by=request.user,
            )
            MenuPollOption.objects.bulk_create([
                MenuPollOption(
                    poll=poll,
                    option_text=option_text,
                    display_order=index,
                )
                for index, option_text in enumerate(options)
            ])

        poll = get_menu_poll_queryset().filter(id=poll.id).first()
        serializer = MenuPollSerializer(poll)
        return Response({
            'message': 'Menu poll created successfully.',
            'payload': serializer.data,
        }, status=status.HTTP_201_CREATED)

    if not is_mess_manager(request.user):
        return Response({'error': 'Only mess managers can update menu polls.'},
                        status=status.HTTP_403_FORBIDDEN)

    poll = MenuPoll.objects.filter(id=request.data.get('id')).first()
    if not poll:
        return Response({'error': 'Menu poll not found.'}, status=status.HTTP_404_NOT_FOUND)

    updated_fields = []

    if 'question' in request.data:
        poll.question = str(request.data.get('question', '')).strip()
        if not poll.question:
            return Response({'message': 'Poll question is required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        updated_fields.append('question')

    if 'description' in request.data:
        poll.description = str(request.data.get('description', '')).strip()
        updated_fields.append('description')

    if 'status' in request.data:
        poll_status = request.data.get('status')
        if poll_status not in {'open', 'closed'}:
            return Response({'message': 'Status must be open or closed.'},
                            status=status.HTTP_400_BAD_REQUEST)
        poll.status = poll_status
        updated_fields.append('status')

    if 'meal_time' in request.data:
        meal_time = request.data.get('meal_time') or None
        if meal_time and meal_time not in dict(Menu._meta.get_field('meal_time').choices):
            return Response({'message': 'Select a valid meal time.'},
                            status=status.HTTP_400_BAD_REQUEST)
        poll.meal_time = meal_time
        updated_fields.append('meal_time')

    if 'poll_date' in request.data:
        poll_date_value = request.data.get('poll_date')
        if poll_date_value:
            try:
                poll.poll_date = parse_date(poll_date_value, 'poll_date')
            except ValueError as exc:
                return Response({'message': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            poll.poll_date = None
        updated_fields.append('poll_date')

    if 'options' in request.data:
        return Response({
            'message': 'Poll options cannot be edited after creation. Create a new poll instead.'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not updated_fields:
        return Response({'message': 'No changes were provided.'},
                        status=status.HTTP_400_BAD_REQUEST)

    updated_fields.append('updated_at')
    poll.save(update_fields=updated_fields)

    poll = get_menu_poll_queryset().filter(id=poll.id).first()
    serializer = MenuPollSerializer(poll)
    return Response({
        'message': 'Menu poll updated successfully.',
        'payload': serializer.data,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def menu_poll_vote_api(request):
    student = get_student(request.user)
    if not student:
        return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

    poll = get_menu_poll_queryset().filter(id=request.data.get('poll_id')).first()
    if not poll:
        return Response({'error': 'Menu poll not found.'}, status=status.HTTP_404_NOT_FOUND)

    if poll.status != 'open':
        return Response({'message': 'Voting is closed for this poll.'},
                        status=status.HTTP_400_BAD_REQUEST)

    student_mess_option = get_student_mess_option(student)
    if student_mess_option != poll.mess_option:
        return Response({
            'message': 'You can vote only for polls created for your registered mess.'
        }, status=status.HTTP_403_FORBIDDEN)

    option = poll.options.filter(id=request.data.get('option_id')).first()
    if not option:
        return Response({'message': 'Select a valid poll option.'},
                        status=status.HTTP_400_BAD_REQUEST)

    vote, created = MenuPollVote.objects.update_or_create(
        poll=poll,
        student_id=student,
        defaults={'option': option},
    )

    poll = get_menu_poll_queryset().filter(id=poll.id).first()
    serializer = MenuPollSerializer(
        poll,
        context={
            'student': student,
            'student_mess_option': student_mess_option,
        }
    )
    return Response({
        'message': 'Vote submitted successfully.' if created else 'Vote updated successfully.',
        'payload': serializer.data,
        'vote_id': vote.id,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_registration_status_api(request):
    student = get_student(request.user)
    if not student:
        return Response({
            'payload': {
                'isRegistered': False,
                'current_mess_status': 'Not Found',
                'current_rem_balance': 0,
            }
        }, status=status.HTTP_200_OK)

    mess_info = Messinfo.objects.filter(student_id=student).first()
    is_registered = mess_info is not None
    return Response({
        'payload': {
            'isRegistered': is_registered,
            'mess_option': mess_info.mess_option if mess_info else None,
            'current_mess_status': 'Registered' if is_registered else 'Deregistered',
            'current_rem_balance': get_bill_balance(student),
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
def registration_request_api(request):
    student = get_student(request.user)

    if request.method == 'GET':
        if is_mess_manager(request.user):
            queryset = RegistrationRequest.objects.select_related(
                'student_id', 'student_id__id', 'student_id__id__user'
            )
        else:
            if not student:
                return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
            queryset = RegistrationRequest.objects.filter(student_id=student)
        serializer = RegistrationRequestSerializer(queryset, many=True)
        return Response({'payload': serializer.data}, status=status.HTTP_200_OK)

    if request.method == 'POST':
        if not student:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        mess_option = request.data.get('mess_option')
        start_date = parse_date(request.data.get('start_date'), 'start_date')
        payment_date = parse_date(request.data.get('payment_date'), 'payment_date')
        amount = int(request.data.get('amount', request.data.get('amount_paid', 0)) or 0)
        txn_no = request.data.get('Txn_no') or request.data.get('txn_no')
        receipt = request.FILES.get('img') if hasattr(request, 'FILES') else None

        if mess_option not in {'mess1', 'mess2'}:
            return Response({'message': 'Select a valid mess option.'}, status=status.HTTP_400_BAD_REQUEST)
        if not txn_no:
            return Response({'message': 'Transaction number is required.'}, status=status.HTTP_400_BAD_REQUEST)

        current_window = Mess_reg.objects.order_by('-id').first()
        if current_window and not (current_window.start_reg <= date.today() <= current_window.end_reg):
            return Response({'message': 'Registration portal is closed.'}, status=status.HTTP_400_BAD_REQUEST)

        existing_pending = RegistrationRequest.objects.filter(
            student_id=student, status__in=['pending', 'escalated']
        ).exists()
        if existing_pending:
            return Response({'message': 'A registration request is already pending.'},
                            status=status.HTTP_400_BAD_REQUEST)

        registration = RegistrationRequest.objects.create(
            student_id=student,
            mess_option=mess_option,
            start_date=start_date,
            payment_date=payment_date,
            amount=amount,
            Txn_no=txn_no,
            img=receipt,
            registration_remark=request.data.get('registration_remark', ''),
        )
        return Response({
            'message': 'Registration request submitted successfully.',
            'payload': RegistrationRequestSerializer(registration).data,
        }, status=status.HTTP_201_CREATED)

    if not is_mess_manager(request.user):
        return Response({'error': 'Only mess managers can process registration requests.'},
                        status=status.HTTP_403_FORBIDDEN)

    request_id = request.data.get('id')
    reg_request = RegistrationRequest.objects.filter(id=request_id).select_related(
        'student_id'
    ).first()
    if not reg_request:
        return Response({'error': 'Registration request not found.'}, status=status.HTTP_404_NOT_FOUND)

    if reg_request.status == 'escalated' and not is_mess_warden(request.user):
        return Response({'message': 'This request is already awaiting mess warden review.'},
                        status=status.HTTP_400_BAD_REQUEST)

    new_status = normalize_request_status(request.data.get('status'), 'request')
    new_status_key = get_request_status_key(new_status, 'request')
    if new_status_key not in {'accept', 'reject', 'escalated'}:
        return Response({'message': 'Status must be accept, reject, or escalated.'},
                        status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        reg_request.status = new_status
        reg_request.registration_remark = request.data.get(
            'registration_remark', reg_request.registration_remark
        )
        reg_request.mess_option = request.data.get('mess_option', reg_request.mess_option)
        if new_status_key == 'escalated':
            reg_request.escalation_remark = request.data.get(
                'escalation_remark', reg_request.registration_remark
            )
            reg_request.escalated_at = timezone.now()
            reg_request.save()
            notify_wardens_of_escalation(
                request.user, 'Registration request', reg_request, reg_request.escalation_remark
            )
            return Response({'message': 'Registration request escalated to the mess warden.'},
                            status=status.HTTP_200_OK)

        reg_request.save()

        if new_status_key == 'accept':
            apply_registration_acceptance(reg_request)

    return Response({'message': 'Registration request updated successfully.'},
                    status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def get_student_bill_api(request):
    target_student = get_student(request.user)
    if request.method == 'POST' and is_mess_manager(request.user):
        requested_student = request.data.get('student_id')
        if requested_student:
            target_student = Student.objects.filter(id=requested_student).first()

    if not target_student:
        return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

    bills = Monthly_bill.objects.filter(student_id=target_student).order_by('-year', '-id')
    serializer = MonthlyBillSerializer(bills, many=True)
    return Response({'payload': serializer.data}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
def rebate_api(request):
    student = get_student(request.user)

    if request.method == 'GET':
        queryset = Rebate.objects.all() if is_mess_manager(request.user) else Rebate.objects.filter(student_id=student)
        serializer = RebateSerializer(queryset.order_by('-app_date', '-id'), many=True)
        return Response({'payload': serializer.data}, status=status.HTTP_200_OK)

    if request.method == 'POST':
        if not student:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        start_date = parse_date(request.data.get('start_date'), 'start_date')
        end_date = parse_date(request.data.get('end_date'), 'end_date')
        purpose = request.data.get('purpose', '').strip()
        if not purpose:
            return Response({'message': 'Purpose is required.'}, status=status.HTTP_400_BAD_REQUEST)

        validation_error = validate_rebate_window(student, start_date, end_date)
        escalate = False
        if validation_error == 'ESCALATE':
            escalate = True
            validation_error = None

        if validation_error:
            return Response({'status': 3, 'message': validation_error}, status=status.HTTP_400_BAD_REQUEST)

        rebate = Rebate.objects.create(
            student_id=student,
            start_date=start_date,
            end_date=end_date,
            purpose=purpose,
            leave_type=request.data.get('leave_type', 'casual'),
            status='3' if escalate else '1',
            app_date=date.today(),
        )
        if escalate:
            rebate.escalation_remark = 'Rebate limit exceeded. Maximum approved rebate days per semester is 20. Auto-escalated to Warden.'
            rebate.escalated_at = timezone.now()
            rebate.save()
            notify_wardens_of_escalation(request.user, 'Rebate request', rebate, rebate.escalation_remark)
        return Response({
            'message': 'Rebate applied successfully',
            'payload': RebateSerializer(rebate).data,
        }, status=status.HTTP_201_CREATED)

    if request.method == 'DELETE':
        rebate = Rebate.objects.filter(id=request.data.get('id'), student_id=student, status='1').first()
        if not rebate:
            return Response({'error': 'Pending rebate not found to cancel.'}, status=status.HTTP_404_NOT_FOUND)
        rebate.delete()
        return Response({'message': 'Rebate request cancelled successfully.'}, status=status.HTTP_200_OK)

    if not is_mess_manager(request.user):
        return Response({'error': 'Only mess managers can process rebate requests.'},
                        status=status.HTTP_403_FORBIDDEN)

    rebate = Rebate.objects.filter(id=request.data.get('id')).first()
    if not rebate:
        return Response({'error': 'Rebate request not found'}, status=status.HTTP_404_NOT_FOUND)

    if rebate.status == '3' and not is_mess_warden(request.user):
        return Response({'message': 'This rebate request is already awaiting mess warden review.'},
                        status=status.HTTP_400_BAD_REQUEST)

    new_status = normalize_request_status(request.data.get('status'), 'numeric')
    new_status_key = get_request_status_key(new_status, 'numeric')
    if new_status_key not in {'accept', 'reject', 'escalated'}:
        return Response({'message': 'Status must be 0, 2, or 3.'}, status=status.HTTP_400_BAD_REQUEST)

    rebate.status = new_status
    rebate.rebate_remark = request.data.get('rebate_remark', rebate.rebate_remark)
    if new_status_key == 'escalated':
        rebate.escalation_remark = request.data.get(
            'escalation_remark', rebate.rebate_remark
        )
        rebate.escalated_at = timezone.now()
        rebate.save()
        notify_wardens_of_escalation(
            request.user, 'Rebate request', rebate, rebate.escalation_remark
        )
        return Response({'message': 'Rebate request escalated to the mess warden.'},
                        status=status.HTTP_200_OK)

    rebate.save()
    return Response({'message': 'Rebate request updated.'}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
def special_request_api(request):
    student = get_student(request.user)

    if request.method == 'GET':
        queryset = Special_request.objects.all() if is_mess_manager(request.user) else Special_request.objects.filter(student_id=student)
        serializer = SpecialRequestSerializer(queryset.order_by('-app_date', '-id'), many=True)
        return Response({'payload': serializer.data}, status=status.HTTP_200_OK)

    if request.method == 'POST':
        if not student:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            start_date = parse_date(request.data.get('start_date'), 'start_date')
            end_date = parse_date(request.data.get('end_date'), 'end_date')
        except ValueError as exc:
            return Response({'message': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        item1 = request.data.get('item1', '').strip()
        item2 = request.data.get('item2', '').strip()
        purpose = request.data.get('request') or request.data.get('purpose', '')
        purpose = purpose.strip()
        if not item1 or not item2 or not purpose:
            return Response({'message': 'Food, timing, and reason are required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        supporting_document = get_special_request_document(request)
        raw_request_type = request.data.get('request_type') or request.data.get('reason_type')
        request_type = normalize_special_request_type(raw_request_type)
        if raw_request_type and not request_type:
            return Response({'message': 'Select a valid request type.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not request_type:
            request_type = 'medical' if supporting_document else 'event'
        validation_error = validate_special_food_request(
            student,
            start_date,
            end_date,
            request_type,
            supporting_document,
        )
        if validation_error:
            return Response({'message': validation_error},
                            status=status.HTTP_400_BAD_REQUEST)

        special_request = Special_request.objects.create(
            student_id=student,
            start_date=start_date,
            end_date=end_date,
            item1=item1,
            item2=item2,
            request=purpose,
            request_type=request_type,
            status='1',
            semester=student.curr_semester_no,
            app_date=date.today(),
            supporting_document=supporting_document,
        )
        return Response({
            'message': 'Special food request submitted.',
            'payload': SpecialRequestSerializer(special_request).data,
        }, status=status.HTTP_201_CREATED)

    if not is_mess_manager(request.user):
        return Response({'error': 'Only mess managers can process special food requests.'},
                        status=status.HTTP_403_FORBIDDEN)

    special_request = Special_request.objects.filter(id=request.data.get('id')).first()
    if not special_request:
        return Response({'error': 'Special food request not found'}, status=status.HTTP_404_NOT_FOUND)

    if special_request.status == '3' and not is_mess_warden(request.user):
        return Response({'message': 'This request is already awaiting mess warden review.'},
                        status=status.HTTP_400_BAD_REQUEST)

    new_status = normalize_request_status(request.data.get('status'), 'numeric')
    new_status_key = get_request_status_key(new_status, 'numeric')
    if new_status_key not in {'accept', 'reject', 'escalated'}:
        return Response({'message': 'Status must be 0, 2, or 3.'}, status=status.HTTP_400_BAD_REQUEST)

    special_request.status = new_status
    special_request.special_request_remark = request.data.get(
        'special_request_remark', special_request.special_request_remark
    )
    if new_status_key == 'escalated':
        special_request.escalation_remark = request.data.get(
            'escalation_remark', special_request.special_request_remark
        )
        special_request.escalated_at = timezone.now()
        special_request.save()
        notify_wardens_of_escalation(
            request.user, 'Special food request', special_request,
            special_request.escalation_remark
        )
        return Response({'message': 'Special food request escalated to the mess warden.'},
                        status=status.HTTP_200_OK)

    special_request.save()
    return Response({'message': 'Special food request updated.'}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def feedback_api(request):
    student = get_student(request.user)

    if request.method == 'GET':
        queryset = Feedback.objects.all() if is_mess_manager(request.user) else Feedback.objects.filter(student_id=student)
        serializer = FeedbackSerializer(queryset.order_by('-fdate', '-id'), many=True)
        payload = serializer.data
        for item in payload:
            item['feedback_type'] = feedback_label(item['feedback_type'])
        return Response({'payload': payload}, status=status.HTTP_200_OK)

    if request.method == 'POST':
        if not student:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        description = request.data.get('description', '').strip()
        if not description:
            return Response({'message': 'Feedback description cannot be empty.'},
                            status=status.HTTP_400_BAD_REQUEST)
        # UC-007: length and spam validation
        if len(description) < 10 or len(description) > 500:
            return Response({'message': 'Feedback description must be between 10 and 500 characters.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if 'spam' in description.lower():
            return Response({'message': 'Spam detected in feedback.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if Feedback.objects.filter(student_id=student, fdate=date.today()).exists():
            return Response({'message': 'Only one feedback entry can be submitted per day.'},
                            status=status.HTTP_400_BAD_REQUEST)

        feedback_type = normalize_feedback_type(request.data.get('feedback_type'))
        if not feedback_type:
            return Response({'message': 'Select a valid feedback type.'},
                            status=status.HTTP_400_BAD_REQUEST)

        mess_info = Messinfo.objects.filter(student_id=student).first()
        feedback = Feedback.objects.create(
            student_id=student,
            mess=mess_info.mess_option if mess_info else 'mess2',
            mess_rating=int(request.data.get('mess_rating', 5)),
            fdate=date.today(),
            description=description,
            feedback_type=feedback_label(feedback_type),
        )
        return Response({
            'message': 'Feedback submitted.',
            'payload': FeedbackSerializer(feedback).data,
        }, status=status.HTTP_200_OK)

    if not is_mess_manager(request.user):
        return Response({'error': 'Only mess managers can update feedback state.'},
                        status=status.HTTP_403_FORBIDDEN)

    normalized_type = normalize_feedback_type(request.data.get('feedback_type'))
    feedback_type_values = []
    if normalized_type:
        feedback_type_values.extend([normalized_type, feedback_label(normalized_type)])
    raw_feedback_type = request.data.get('feedback_type')
    if raw_feedback_type:
        feedback_type_values.append(str(raw_feedback_type).strip())

    feedback = Feedback.objects.filter(
        student_id__id__user__username=request.data.get('student_id'),
        mess=request.data.get('mess'),
        feedback_type__in=feedback_type_values or [raw_feedback_type],
        description=request.data.get('description'),
        fdate=request.data.get('fdate'),
    ).first()
    if not feedback:
        return Response({'error': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)

    feedback.is_read = True
    feedback.save(update_fields=['is_read'])
    return Response({'message': 'Feedback marked as read.'}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def payments_api(request):
    student = get_student(request.user)
    if not student:
        return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        payment_date = parse_date(request.data.get('payment_date'), 'payment_date')
        amount_paid = int(request.data.get('amount_paid', 0) or 0)
        payment_month = request.data.get('payment_month') or payment_date.strftime('%B')
        payment_year = int(request.data.get('payment_year', payment_date.year))
        sem = int(request.data.get('sem', student.curr_semester_no))


        # BR-MMS-018 & BR-MMS-022: Implement payment grace period logic
        late_fee = 0
        if payment_date.day > 10:
            late_fee = (payment_date.day - 10) * 50
            if amount_paid < late_fee:
                return Response({'error': f'Payment must include the calculated late fee of {late_fee}'}, status=status.HTTP_400_BAD_REQUEST)
        
        payment = Payments.objects.create(
            student_id=student,
            sem=sem,
            year=payment_year,
            amount_paid=amount_paid,
            payment_date=payment_date,
            payment_month=payment_month,
            payment_year=payment_year,
            Txn_no=request.data.get('Txn_no', ''),
            status='accept',
        )
        return Response({
            'message': 'Payment details submitted.',
            'payload': PaymentsSerializer(payment).data,
        }, status=status.HTTP_201_CREATED)

    payments = Payments.objects.filter(student_id=student).order_by('-payment_year', '-payment_date', '-id')
    serializer = PaymentsSerializer(payments, many=True)
    return Response({'payload': serializer.data}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def get_mess_students_api(request):
    if not is_mess_manager(request.user):
        return Response({'error': 'Only mess managers can access registration data.'},
                        status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        mess_infos = Messinfo.objects.select_related('student_id', 'student_id__id', 'student_id__id__user')
        serializer = MessinfoSerializer(mess_infos, many=True)
        return Response({'payload': serializer.data}, status=status.HTTP_200_OK)

    request_type = request.data.get('type')
    if request_type == 'search':
        username = str(request.data.get('student_id', '')).upper()
        student = Student.objects.select_related('id', 'id__user').filter(
            id__user__username=username
        ).first()
        if not student:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        mess_info = Messinfo.objects.filter(student_id=student).first()
        return Response({
            'payload': {
                'id': student.id_id,
                'first_name': student.id.user.first_name,
                'last_name': student.id.user.last_name,
                'student_id': student.id.user.username,
                'program': student.programme,
                'mess_option': mess_info.mess_option if mess_info else '-',
                'current_mess_status': 'Registered' if mess_info else 'Deregistered',
            }
        }, status=status.HTTP_200_OK)

    queryset = Student.objects.select_related('id', 'id__user')
    status_filter = str(request.data.get('status', 'all')).lower()
    programme_filter = request.data.get('program', 'all')
    mess_option_filter = str(request.data.get('mess_option', 'all')).lower()

    if programme_filter != 'all':
        queryset = queryset.filter(programme=programme_filter)

    payload = []
    for student in queryset:
        mess_info = Messinfo.objects.filter(student_id=student).first()
        current_status = 'Registered' if mess_info else 'Deregistered'
        if status_filter != 'all' and current_status.lower() != status_filter.lower():
            continue
        if mess_option_filter not in {'all', ''} and (not mess_info or mess_info.mess_option != mess_option_filter):
            continue
        payload.append({
            'id': student.id_id,
            'first_name': student.id.user.first_name,
            'last_name': student.id.user.last_name,
            'student_id': student.id.user.username,
            'program': student.programme,
            'mess_option': mess_info.mess_option if mess_info else '-',
            'current_mess_status': current_status,
        })

    return Response({'payload': payload}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
def deregistration_request_api(request):
    student = get_student(request.user)

    if request.method == 'GET':
        queryset = DeregistrationRequest.objects.all() if is_mess_manager(request.user) else DeregistrationRequest.objects.filter(student_id=student)
        serializer = DeregistrationRequestSerializer(queryset.order_by('-created_at'), many=True)
        return Response({'payload': serializer.data}, status=status.HTTP_200_OK)

    if request.method == 'POST':
        if not student:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        if not Messinfo.objects.filter(student_id=student).exists():
            return Response({'message': 'Student is not currently registered in mess.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if get_bill_balance(student) > 0:
            return Response({'message': 'Deregistration is allowed only after clearing pending dues.'},
                            status=status.HTTP_400_BAD_REQUEST)

        end_date = parse_date(request.data.get('end_date'), 'end_date')
        if end_date < date.today().replace(day=1):
            return Response({'message': 'Select a valid deregistration end date.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if DeregistrationRequest.objects.filter(
            student_id=student, status__in=['pending', 'escalated']
        ).exists():
            return Response({'message': 'A deregistration request is already pending.'},
                            status=status.HTTP_400_BAD_REQUEST)

        dereg_request = DeregistrationRequest.objects.create(
            student_id=student,
            end_date=end_date,
            deregistration_remark=request.data.get('deregistration_remark', ''),
        )
        return Response({
            'message': 'Deregistration request submitted successfully.',
            'payload': DeregistrationRequestSerializer(dereg_request).data,
        }, status=status.HTTP_201_CREATED)

    if not is_mess_manager(request.user):
        return Response({'error': 'Only mess managers can process deregistration requests.'},
                        status=status.HTTP_403_FORBIDDEN)

    dereg_request = DeregistrationRequest.objects.filter(id=request.data.get('id')).select_related('student_id').first()
    if not dereg_request:
        return Response({'error': 'Deregistration request not found.'}, status=status.HTTP_404_NOT_FOUND)

    if dereg_request.status == 'escalated' and not is_mess_warden(request.user):
        return Response({'message': 'This request is already awaiting mess warden review.'},
                        status=status.HTTP_400_BAD_REQUEST)

    new_status = normalize_request_status(request.data.get('status'), 'request')
    new_status_key = get_request_status_key(new_status, 'request')
    if new_status_key not in {'accept', 'reject', 'escalated'}:
        return Response({'message': 'Status must be accept, reject, or escalated.'},
                        status=status.HTTP_400_BAD_REQUEST)

    dereg_request.status = new_status
    dereg_request.deregistration_remark = request.data.get(
        'deregistration_remark', dereg_request.deregistration_remark
    )
    if new_status_key == 'escalated':
        dereg_request.escalation_remark = request.data.get(
            'escalation_remark', dereg_request.deregistration_remark
        )
        dereg_request.escalated_at = timezone.now()
        dereg_request.save()
        notify_wardens_of_escalation(
            request.user, 'Deregistration request', dereg_request,
            dereg_request.escalation_remark
        )
        return Response({'message': 'Deregistration request escalated to the mess warden.'},
                        status=status.HTTP_200_OK)

    dereg_request.save()
    if new_status_key == 'accept':
        apply_deregistration_acceptance(dereg_request)

    return Response({'message': 'Deregistration request updated successfully.'},
                    status=status.HTTP_200_OK)


@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
def update_payment_request_api(request):
    student = get_student(request.user)

    if request.method == 'POST':
        if not student:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        payment_date = parse_date(request.data.get('payment_date'), 'payment_date')
        amount = int(request.data.get('amount', 0) or 0)
        txn_no = request.data.get('Txn_no') or request.data.get('txn_no')
        receipt = request.FILES.get('img') if hasattr(request, 'FILES') else None
        if not txn_no:
            return Response({'message': 'Transaction number is required.'}, status=status.HTTP_400_BAD_REQUEST)

        payment_request = PaymentUpdateRequest.objects.create(
            student_id=student,
            payment_date=payment_date,
            amount=amount,
            Txn_no=txn_no,
            img=receipt,
            update_remark=request.data.get('update_remark', ''),
        )
        return Response({
            'message': 'Payment update request submitted.',
            'payload': PaymentUpdateRequestSerializer(payment_request).data,
        }, status=status.HTTP_201_CREATED)

    if request.method == 'GET':
        queryset = PaymentUpdateRequest.objects.all() if is_mess_manager(request.user) else PaymentUpdateRequest.objects.filter(student_id=student)
        query_student = request.query_params.get('student_id')
        if query_student and not is_mess_manager(request.user):
            queryset = queryset.filter(student_id__id__user__username=query_student)
        serializer = PaymentUpdateRequestSerializer(queryset.order_by('-created_at'), many=True)
        return Response({'payload': serializer.data}, status=status.HTTP_200_OK)

    if not is_mess_manager(request.user):
        return Response({'error': 'Only mess managers can process payment update requests.'},
                        status=status.HTTP_403_FORBIDDEN)

    payment_request = PaymentUpdateRequest.objects.filter(id=request.data.get('id')).select_related('student_id').first()
    if not payment_request:
        return Response({'error': 'Payment update request not found.'}, status=status.HTTP_404_NOT_FOUND)

    if payment_request.status == 'escalated' and not is_mess_warden(request.user):
        return Response({'message': 'This request is already awaiting mess warden review.'},
                        status=status.HTTP_400_BAD_REQUEST)

    new_status = normalize_request_status(request.data.get('status'), 'request')
    new_status_key = get_request_status_key(new_status, 'request')
    if new_status_key not in {'accept', 'reject', 'escalated'}:
        return Response({'message': 'Status must be accept, reject, or escalated.'},
                        status=status.HTTP_400_BAD_REQUEST)

    payment_request.status = new_status
    payment_request.update_remark = request.data.get('update_payment_remark', request.data.get('update_remark', payment_request.update_remark))
    if new_status_key == 'escalated':
        payment_request.escalation_remark = request.data.get(
            'escalation_remark', payment_request.update_remark
        )
        payment_request.escalated_at = timezone.now()
        payment_request.save()
        notify_wardens_of_escalation(
            request.user, 'Payment update request', payment_request,
            payment_request.escalation_remark
        )
        return Response({'message': 'Payment update request escalated to the mess warden.'},
                        status=status.HTTP_200_OK)

    payment_request.save()

    if new_status_key == 'accept':
        apply_payment_update_acceptance(payment_request)

    return Response({'message': 'Payment update request updated.'}, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def warden_decision_api(request):
    if not is_mess_warden(request.user):
        return Response({'error': 'Only mess wardens can review escalated requests.'},
                        status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        payload = []
        for request_type, config in REQUEST_REVIEW_CONFIG.items():
            escalated_status = normalize_request_status('escalated', config['status_kind'])
            queryset = config['model'].objects.filter(
                status=escalated_status
            ).select_related('student_id', 'student_id__id', 'student_id__id__user')
            payload.extend(
                serialize_warden_queue_item(request_type, item)
                for item in queryset
            )

        payload.sort(
            key=lambda item: (
                (item.get('escalated_at') or item.get('submitted_at')).isoformat()
                if (item.get('escalated_at') or item.get('submitted_at')) else ''
            ),
            reverse=True,
        )
        return Response({'payload': payload}, status=status.HTTP_200_OK)

    request_type = request.data.get('request_type')
    request_id = request.data.get('id')
    config, request_obj = get_request_object(request_type, request_id)
    if not config or not request_obj:
        return Response({'error': 'Escalated request not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not is_escalated_request_status(request_obj.status, config['status_kind']):
        return Response({'message': 'Only escalated requests can be reviewed here.'},
                        status=status.HTTP_400_BAD_REQUEST)

    final_status = normalize_request_status(request.data.get('status'), config['status_kind'])
    final_status_key = get_request_status_key(final_status, config['status_kind'])
    if final_status_key not in {'accept', 'reject'}:
        return Response({'message': 'Status must resolve to accept or reject.'},
                        status=status.HTTP_400_BAD_REQUEST)

    warden_remark = str(request.data.get('warden_remark', '')).strip()
    override_conditions = str(request.data.get('override_conditions', '')).strip()

    with transaction.atomic():
        request_obj.status = final_status
        request_obj.warden_remark = warden_remark
        request_obj.override_conditions = override_conditions
        request_obj.warden_decided_at = timezone.now()
        persist_final_remark(request_obj, config, warden_remark, override_conditions)
        request_obj.save()

        if final_status_key == 'accept':
            if request_type == 'registration':
                apply_registration_acceptance(request_obj)
            elif request_type == 'deregistration':
                apply_deregistration_acceptance(request_obj)
            elif request_type == 'payment_update':
                apply_payment_update_acceptance(request_obj)

    notify_student_of_warden_decision(
        request.user, config['label'], request_obj, final_status_key,
        warden_remark, override_conditions
    )

    return Response({
        'message': 'Warden decision recorded successfully.',
        'payload': serialize_warden_queue_item(request_type, request_obj),
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mess_reg_api(request):
    if not is_mess_manager(request.user):
        return Response({'error': 'Only mess managers can update registration dates.'},
                        status=status.HTTP_403_FORBIDDEN)

    sem = request.data.get('sem', 1)
    start_value = request.data.get('start_date') or request.data.get('start_reg')
    end_value = request.data.get('end_date') or request.data.get('end_reg')
    start_date = parse_date(start_value, 'start_date')
    end_date = parse_date(end_value, 'end_date')
    if end_date <= start_date:
        return Response({'message': 'End date must be greater than start date.'},
                        status=status.HTTP_400_BAD_REQUEST)

    reg = Mess_reg.objects.create(sem=sem, start_reg=start_date, end_reg=end_date)
    return Response({
        'message': 'Registration dates updated.',
        'payload': MessRegSerializer(reg).data,
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mess_balance_status_api(request):
    if not is_mess_manager(request.user):
        return Response({'error': 'Only mess managers can view mess balance status.'},
                        status=status.HTTP_403_FORBIDDEN)

    bills = Monthly_bill.objects.select_related('student_id', 'student_id__id', 'student_id__id__user').all()
    serializer = MonthlyBillSerializer(bills, many=True)
    return Response({'payload': serializer.data}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def vacation_survey_api(request, pk=None):
    from .models import VacationSurvey
    from .serializers import VacationSurveySerializer
    from django.utils.dateparse import parse_date
    
    if request.method == 'GET':
        surveys = VacationSurvey.objects.filter(is_active=True).order_by('-created_at')
        if is_mess_manager(request.user):
            surveys = VacationSurvey.objects.all().order_by('-created_at')
        serializer = VacationSurveySerializer(surveys, many=True)
        return Response({'payload': serializer.data}, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        if not is_mess_manager(request.user):
            return Response(
                {'error': 'Only mess managers can create vacation surveys.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        description = str(request.data.get('description', '')).strip()
        
        survey = VacationSurvey.objects.create(
            caretaker=request.user,
            description=description,
            title=request.data.get('title', ''),
            vacation_period=request.data.get('vacation_period', ''),
            is_active=True
        )
        
        serializer = VacationSurveySerializer(survey)
        return Response(
            {
                'message': 'Vacation survey created successfully.',
                'payload': serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    elif request.method == 'DELETE':
        if not is_mess_manager(request.user):
            return Response(
                {'error': 'Only mess managers can delete vacation surveys.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        survey_id = pk or request.GET.get('id')
        if not survey_id:
            return Response(
                {'error': 'Survey ID is required for deletion.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            survey = VacationSurvey.objects.get(id=survey_id)
            survey.delete()
            return Response(
                {'message': 'Vacation survey deleted successfully.'},
                status=status.HTTP_200_OK
            )
        except VacationSurvey.DoesNotExist:
            return Response(
                {'error': 'Survey not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def vacation_survey_response_api(request):
    from .models import VacationSurveyResponse, VacationSurvey
    from .serializers import VacationSurveyResponseSerializer
    from applications.academic_information.models import Student
    
    if request.method == 'GET':
        survey_id = request.GET.get('survey_id')
        
        if is_mess_manager(request.user):
            if survey_id:
                responses = VacationSurveyResponse.objects.filter(survey_id=survey_id)
            else:
                responses = VacationSurveyResponse.objects.all()
        else:
            student = get_student(request.user)
            if not student:
                return Response(
                    {'error': 'Student profile not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            if survey_id:
                responses = VacationSurveyResponse.objects.filter(
                    survey_id=survey_id,
                    student=student
                )
            else:
                responses = VacationSurveyResponse.objects.filter(student=student)
        
        serializer = VacationSurveyResponseSerializer(responses, many=True)
        return Response({'payload': serializer.data}, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        student = get_student(request.user)
        if not student:
            return Response(
                {'error': 'Student profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        survey_id = request.data.get('survey_id')
        survey = VacationSurvey.objects.filter(id=survey_id).first()
        
        if not survey:
            return Response(
                {'error': 'Survey not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if student has already responded
        existing_response = VacationSurveyResponse.objects.filter(
            survey=survey,
            student=student
        ).first()
        
        preferences = str(request.data.get('preferences', '')).strip()
        
        if existing_response:
            existing_response.details = preferences
            existing_response.save()
            serializer = VacationSurveyResponseSerializer(existing_response)
            return Response(
                {
                    'message': 'Response updated successfully.',
                    'payload': serializer.data
                },
                status=status.HTTP_200_OK
            )
        
        response = VacationSurveyResponse.objects.create(
            survey=survey,
            student=student,
            attending=True,
            details=preferences
        )
        
        serializer = VacationSurveyResponseSerializer(response)
        return Response(
            {
                'message': 'Response submitted successfully.',
                'payload': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
