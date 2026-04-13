from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError
from django.utils import timezone
from applications.academic_information.models import Student
from applications.globals.models import HoldsDesignation

from . import serializers
from .. import selectors, services
from ..models import (
    Award_and_scholarship, Director_gold, Director_silver, Proficiency_dm,
    ExtendedScholarshipType, ScholarshipApplication, Award, AwardRecipient
)


def _is_admin(user):
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


def _require_admin(request):
    if not _is_admin(request.user):
        return Response({"error": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)
    return None


class ActiveAwardsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = selectors.get_student_by_user(request.user)
        if not student:
            return Response({"error": "Student profile required."}, status=status.HTTP_403_FORBIDDEN)
        releases = selectors.get_active_releases(student.batch, student.programme)
        serializer = serializers.ReleaseSerializer(releases, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentApplicationsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = selectors.get_student_by_user(request.user)
        if not student:
            return Response({"error": "Student profile required."}, status=status.HTTP_403_FORBIDDEN)
        applications = selectors.get_student_applications(student.id)
        serializer = serializers.ApplicationReadSerializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class McmSubmissionAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        student = selectors.get_student_by_user(request.user)
        serializer = serializers.McmCreateSerializer(data=request.data)
        if serializer.is_valid():
            income_cert = request.FILES.get('income_certificate')
            if not income_cert:
                return Response({"error": "Income certificate file is required."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                award = Award_and_scholarship.objects.get(id=serializer.validated_data['award_id'])
                services.submit_mcm_application(
                    student=student, award=award,
                    mcm_data=serializer.validated_data, income_certificate=income_cert
                )
                return Response({"message": "MCM Application submitted successfully."}, status=status.HTTP_201_CREATED)
            except Award_and_scholarship.DoesNotExist:
                return Response({"error": "Invalid Award ID."}, status=status.HTTP_404_NOT_FOUND)
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MedalSubmissionAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        student = selectors.get_student_by_user(request.user)
        serializer = serializers.MedalCreateSerializer(data=request.data)
        medal_type = request.data.get('medal_type')
        model_map = {'GOLD': Director_gold, 'SILVER': Director_silver, 'PROFICIENCY': Proficiency_dm}
        if medal_type not in model_map:
            return Response({"error": "Invalid medal_type."}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            document = request.FILES.get('relevant_document')
            if not document:
                return Response({"error": "Supporting document is required."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                award = Award_and_scholarship.objects.get(id=serializer.validated_data['award_id'])
                services.submit_medal_application(
                    student=student, award=award,
                    model_class=model_map[medal_type], data=serializer.validated_data, document=document
                )
                return Response({"message": f"{medal_type} Application submitted."}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConvenerActionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, application_id):
        application = selectors.get_application_by_id(application_id)
        if not application:
            return Response({"error": "Application not found."}, status=status.HTTP_404_NOT_FOUND)
        new_status = request.data.get('status')
        remarks = request.data.get('remarks', '')
        try:
            services.update_application_status(
                application=application, status=new_status, remarks=remarks, user=request.user
            )
            return Response({"message": f"Application marked as {new_status}."})
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ScholarshipTypesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = ExtendedScholarshipType.objects.prefetch_related('applicable_programmes', 'applicable_batches')
        category = request.GET.get('category')
        if category:
            qs = qs.filter(category=category)
        active_only = request.GET.get('active_only', 'false').lower() == 'true'
        if active_only:
            qs = qs.filter(is_active=True)
        serializer = serializers.ExtendedScholarshipTypeSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        admin_error = _require_admin(request)
        if admin_error:
            return admin_error
        serializer = serializers.ExtendedScholarshipTypeCreateSerializer(data=request.data)
        if serializer.is_valid():
            scholarship_type = serializer.save()
            return Response(
                serializers.ExtendedScholarshipTypeSerializer(scholarship_type).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScholarshipApplicationsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        student = selectors.get_student_by_user(request.user)
        scope = request.GET.get('scope')

        if scope == 'all':
            admin_error = _require_admin(request)
            if admin_error:
                return admin_error
            qs = ScholarshipApplication.objects.select_related('student', 'scholarship_type', 'reviewed_by')
            status_filter = request.GET.get('status')
            if status_filter:
                qs = qs.filter(status=status_filter)
            academic_year = request.GET.get('academic_year')
            if academic_year:
                qs = qs.filter(academic_year=academic_year)
        elif student:
            qs = ScholarshipApplication.objects.filter(student=student).select_related(
                'scholarship_type', 'reviewed_by'
            )
        else:
            return Response({"error": "Student profile required."}, status=status.HTTP_403_FORBIDDEN)

        serializer = serializers.ScholarshipApplicationReadSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        student = selectors.get_student_by_user(request.user)
        if not student:
            return Response({"error": "Student profile required to apply."}, status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.ScholarshipApplicationCreateSerializer(data=request.data)
        if serializer.is_valid():
            scholarship_type_id = serializer.validated_data['scholarship_type'].id
            academic_year = serializer.validated_data['academic_year']
            semester_no = serializer.validated_data['semester']
            document_file = request.FILES.get('supporting_documents') or request.FILES.get('documents')
            application, reasons = services.create_extended_scholarship_application(
                student=student,
                scholarship_type_id=scholarship_type_id,
                academic_year=academic_year,
                semester=semester_no,
                remarks=serializer.validated_data.get('remarks', ''),
                document=document_file
            )
            if application is None:
                return Response({"error": "Not eligible", "reasons": reasons}, status=status.HTTP_400_BAD_REQUEST)
            return Response(
                serializers.ScholarshipApplicationReadSerializer(application).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScholarshipApplicationApproveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, application_id):
        admin_error = _require_admin(request)
        if admin_error:
            return admin_error

        try:
            application = ScholarshipApplication.objects.select_related(
                'student', 'scholarship_type'
            ).get(id=application_id)
        except ScholarshipApplication.DoesNotExist:
            return Response({"error": "Application not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = serializers.ScholarshipApplicationApproveSerializer(data=request.data)
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            try:
                updated = services.process_application_status_change(
                    application=application,
                    new_status=new_status,
                    reviewer_user=request.user,
                    review_remarks=serializer.validated_data.get('review_remarks', ''),
                    amount_approved=serializer.validated_data.get('amount_approved'),
                    transaction_reference=serializer.validated_data.get('transaction_reference', '')
                )
                return Response(
                    serializers.ScholarshipApplicationReadSerializer(updated).data,
                    status=status.HTTP_200_OK
                )
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AwardsManagementAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        awarded_qs = ScholarshipApplication.objects.filter(
            status__in=['APPROVED', 'DISBURSED']
        ).select_related('student', 'scholarship_type').order_by('-review_date', '-application_date')

        data = []
        for app in awarded_qs:
            data.append({
                'id': app.id,
                'student_id': str(app.student.id.id) if app.student and app.student.id else '',
                'scholarship_type_id': app.scholarship_type.id,
                'scholarship_name': app.scholarship_type.name,
                'amount': str(app.amount_approved or app.scholarship_type.amount or 0),
                'status': app.status,
                'award_date': app.disbursement_date.date().isoformat() if app.disbursement_date else None,
                'approved_at': app.review_date,
            })
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        admin_error = _require_admin(request)
        if admin_error:
            return admin_error

        application_id = request.data.get('application_id')
        amount = request.data.get('amount')
        transaction_reference = request.data.get('transaction_reference', '')

        if not application_id:
            return Response({"error": "application_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            application = ScholarshipApplication.objects.get(id=application_id)
        except ScholarshipApplication.DoesNotExist:
            return Response({"error": "Application not found."}, status=status.HTTP_404_NOT_FOUND)

        if application.status not in ['APPROVED', 'DISBURSED']:
            return Response({"error": "Only approved applications can be awarded."}, status=status.HTTP_400_BAD_REQUEST)

        application.status = 'DISBURSED'
        application.disbursement_date = timezone.now()
        if amount is not None:
            application.amount_approved = amount
        if transaction_reference:
            application.transaction_reference = transaction_reference
        application.save()

        return Response({
            'id': application.id,
            'student_id': str(application.student.id.id),
            'scholarship_type_id': application.scholarship_type.id,
            'amount': str(application.amount_approved or application.scholarship_type.amount or 0),
            'award_date': application.disbursement_date.date().isoformat(),
            'status': application.status,
        }, status=status.HTTP_201_CREATED)


class AwardDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, award_id):
        try:
            award = Award.objects.prefetch_related('applicable_programmes', 'recipients').get(id=award_id)
        except Award.DoesNotExist:
            return Response({"error": "Award not found."}, status=status.HTTP_404_NOT_FOUND)
        recipients = AwardRecipient.objects.filter(award=award).select_related('student', 'awarded_by')
        data = serializers.AwardDetailSerializer(award).data
        data['recipients'] = serializers.AwardRecipientSerializer(recipients, many=True).data
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, award_id):
        admin_error = _require_admin(request)
        if admin_error:
            return admin_error

        try:
            award = Award.objects.get(id=award_id)
        except Award.DoesNotExist:
            return Response({"error": "Award not found."}, status=status.HTTP_404_NOT_FOUND)
        data = request.data.copy()
        data['award'] = award_id
        serializer = serializers.AwardRecipientCreateSerializer(data=data)
        if serializer.is_valid():
            recipient = serializer.save()
            return Response(
                serializers.AwardRecipientSerializer(recipient).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EligibleStudentsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, scholarship_id):
        try:
            scholarship = ExtendedScholarshipType.objects.get(id=scholarship_id)
        except ExtendedScholarshipType.DoesNotExist:
            return Response({"error": "Scholarship not found."}, status=status.HTTP_404_NOT_FOUND)

        eligible_students = services.get_eligible_students_for_scholarship(scholarship)
        page_size = min(int(request.GET.get('page_size', 50)), 200)
        page = max(int(request.GET.get('page', 1)), 1)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = eligible_students[start_idx:end_idx]

        return Response({
            'scholarship_id': scholarship_id,
            'scholarship_name': scholarship.name,
            'total_count': len(eligible_students),
            'eligible_count': sum(1 for s in eligible_students if s.get('eligibility_status') == 'ELIGIBLE'),
            'page': page,
            'page_size': page_size,
            'students': paginated
        }, status=status.HTTP_200_OK)


class MeritListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, batch_id=None):
        if not batch_id:
            return Response({"error": "Batch ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        academic_year = request.GET.get('academic_year', '2024-25')
        semester = request.GET.get('semester', 1)
        programme = request.GET.get('programme')
        try:
            semester = int(semester)
        except (ValueError, TypeError):
            semester = 1

        merit_list = services.generate_merit_list(
            batch=batch_id, academic_year=academic_year, semester=semester, programme=programme
        )
        if not merit_list:
            return Response({
                "message": "No merit list data available for this batch.",
                "batch": batch_id, "academic_year": academic_year, "semester": semester,
                "merit_list": []
            }, status=status.HTTP_200_OK)

        return Response({
            'batch': batch_id,
            'academic_year': academic_year,
            'semester': semester,
            'programme': programme,
            'generated_at': timezone.now().isoformat(),
            'total_students': len(merit_list),
            'merit_list': merit_list
        }, status=status.HTTP_200_OK)



class GenerateMeritListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        allowed = _is_admin(request.user) or _has_designation(request.user, ["spacsconvenor"])
        if not allowed:
            return Response({"error": "Only SPACS convener can generate merit list."}, status=status.HTTP_403_FORBIDDEN)

        application_type = str(request.data.get("application_type") or "MCM").strip().upper()
        batch = str(request.data.get("batch") or "").strip()

        if application_type != "MCM":
            return Response({"error": "Merit list generation is only for MCM scholarship."}, status=status.HTTP_400_BAD_REQUEST)

        valid_batches = {"2023", "2024", "2025", "2026", "all"}
        if batch not in valid_batches:
            return Response({"error": "Batch must be one of 2023, 2024, 2025, 2026 or 'all'."}, status=status.HTTP_400_BAD_REQUEST)

        # "all" is our UI convention for full refresh
        target_batch = None if batch == 'all' else batch
        result = services.generate_mcm_merit_list(batch=target_batch)

        if "Error" in result.get("message", ""):
            return Response({"error": result.get("message")}, status=status.HTTP_400_BAD_REQUEST)

        if result.get("generated_count", 0) == 0:
            return Response({
                "message": result.get("message", "No applications found to generate merit list."),
                "generated_count": 0,
                "application_type": "MCM",
                "batch": batch,
                "entries": []
            }, status=status.HTTP_200_OK)

        return Response({
            "message": "Merit list generated successfully",
            "generated_count": result.get("generated_count", 0),
            "application_type": "MCM",
            "batch": batch,
            "entries": result.get("entries", [])
        }, status=status.HTTP_200_OK)
class StudentEligibilityCheckAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        student_id = request.data.get('student_id')
        scholarship_id = request.data.get('scholarship_id')
        if not student_id or not scholarship_id:
            return Response({"error": "Both student_id and scholarship_id are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from applications.academic_information.models import Student
            student = Student.objects.get(id=student_id)
            scholarship = ExtendedScholarshipType.objects.get(id=scholarship_id)
            is_eligible, reasons = services.check_scholarship_eligibility(student, scholarship)
            student_data = services.auto_populate_application_data(student)
            return Response({
                'student_id': student_id,
                'scholarship_id': scholarship_id,
                'scholarship_name': scholarship.name,
                'is_eligible': is_eligible,
                'reasons': reasons if not is_eligible else [],
                'student_data': student_data
            }, status=status.HTTP_200_OK)
        except Student.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
        except ExtendedScholarshipType.DoesNotExist:
            return Response({"error": "Scholarship not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error checking eligibility: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BatchStatisticsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from applications.academic_information.models import Student
            from django.db.models import Count, Q
            stats = Student.objects.values('batch', 'programme', 'category').annotate(
                total_students=Count('id'),
                applied_scholarships=Count('extended_scholarship_applications'),
                approved_scholarships=Count(
                    'extended_scholarship_applications',
                    filter=Q(extended_scholarship_applications__status='APPROVED')
                )
            )
            batch_stats = {}
            for stat in stats:
                batch = str(stat['batch'])
                if batch not in batch_stats:
                    batch_stats[batch] = {'batch': batch, 'programmes': {}}
                prog = stat['programme']
                if prog not in batch_stats[batch]['programmes']:
                    batch_stats[batch]['programmes'][prog] = {'programme': prog, 'categories': {}}
                batch_stats[batch]['programmes'][prog]['categories'][stat['category']] = {
                    'category': stat['category'],
                    'total_students': stat['total_students'],
                    'applied_scholarships': stat['applied_scholarships'],
                    'approved_scholarships': stat['approved_scholarships']
                }
            return Response(list(batch_stats.values()), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error generating statistics: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



def _has_designation(user, names):
    if not user or not user.is_authenticated:
        return False
    return HoldsDesignation.objects.filter(working=user, designation__name__in=names).exists()


def _build_student_profile_payload(student):
    full_name = (f"{student.id.user.first_name} {student.id.user.last_name}").strip()
    branch = ""
    if student.batch_id and getattr(student.batch_id, "discipline", None):
        branch = student.batch_id.discipline.acronym
    elif student.id and student.id.department:
        branch = student.id.department.name

    return {
        "name": full_name or student.id.user.username,
        "roll_no": str(student.id.id),
        "cgpa": student.cpi,
        "batch": str(student.batch) if student.batch is not None else "",
        "programme": student.programme,
        "degree": student.programme,
        "branch": branch,
    }


class StudentProfileLookupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        roll_no = request.GET.get("roll_no")

        if roll_no:
            allowed = _is_admin(request.user) or _has_designation(request.user, ["spacsassistant", "spacsconvenor"])
            if not allowed:
                return Response({"error": "Only SPACS assistant/convener can look up other students."}, status=status.HTTP_403_FORBIDDEN)

            student = Student.objects.select_related("id__user", "id__department", "batch_id__discipline").filter(id__id=roll_no).first()
            if not student:
                return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response(_build_student_profile_payload(student), status=status.HTTP_200_OK)

        student = selectors.get_student_by_user(request.user)
        if not student:
            # Handle non-student administrators
            if _is_admin(request.user) or _has_designation(request.user, ["spacsassistant", "spacsconvenor"]):
                return Response({
                    "full_name": request.user.get_full_name() or request.user.username,
                    "is_staff": True,
                    "role": "admin"
                }, status=status.HTTP_200_OK)
            return Response({"error": "Student profile required."}, status=status.HTTP_403_FORBIDDEN)

        return Response(_build_student_profile_payload(student), status=status.HTTP_200_OK)

from ..models import McmApplication, SingleParentApplication, MeritListRecord
from .serializers import McmApplicationSerializer, SingleParentApplicationSerializer

STATUS = {
    "PENDING": "pending",
    "REVERTED": "reverted",
    "VERIFIED": "verified",
    "APPROVED": "approved",
    "REJECTED": "rejected",
}

FINAL_STATUSES = {STATUS["APPROVED"], STATUS["REJECTED"]}


def _normalize_status(value):
    text = str(value or "").strip().lower()
    synonyms = {
        "submitted": STATUS["PENDING"],
        "in_review": STATUS["VERIFIED"],
        "under_review": STATUS["VERIFIED"],
        "forwarded_to_convenor": STATUS["VERIFIED"],
        "correction_required": STATUS["REVERTED"],
    }
    return synonyms.get(text, text)


class McmApplicationViewSet(viewsets.ModelViewSet):
    queryset = McmApplication.objects.all()
    serializer_class = McmApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if _is_admin(user) or _has_designation(user, ['spacsassistant', 'spacsconvenor']):
            queryset = self.queryset
        else:
            student = selectors.get_student_by_user(user)
            if student:
                queryset = self.queryset.filter(student=student)
            else:
                queryset = self.queryset.none()

        status_filter = _normalize_status(self.request.query_params.get('status'))
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        batch_filter = str(self.request.query_params.get('batch') or '').strip()
        if batch_filter:
            queryset = queryset.filter(batch=batch_filter)

        return queryset

    def _validate_mcm_payload(self, *, batch, category, current_cpi, current_spi, jee_uceed_rank, jee_uceed_scorecard_link):
        normalized_batch = str(batch or '').strip()
        is_first_year = normalized_batch == '2026'

        if is_first_year:
            if current_cpi not in (None, '') or current_spi not in (None, ''):
                raise DRFValidationError({"detail": "For batch 2026, CPI/SPI fields are not allowed. Submit JEE details instead."})

            if jee_uceed_rank in (None, ''):
                raise DRFValidationError({"jee_uceed_rank": "JEE rank is required for batch 2026."})

            try:
                rank = int(str(jee_uceed_rank).strip())
                if rank <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                raise DRFValidationError({"jee_uceed_rank": "JEE rank must be a positive integer."})

            if not str(jee_uceed_scorecard_link or '').strip():
                raise DRFValidationError({"jee_uceed_scorecard_link": "JEE scorecard link is required for batch 2026."})
            return

        if current_cpi in (None, ''):
            raise DRFValidationError({"current_cpi": "Current CPI is required."})

        if current_spi in (None, ''):
            raise DRFValidationError({"current_spi": "Current SPI is required."})

        try:
            cpi = float(current_cpi)
        except (TypeError, ValueError):
            raise DRFValidationError({"current_cpi": "Current CPI must be a valid number."})

        try:
            float(current_spi)
        except (TypeError, ValueError):
            raise DRFValidationError({"current_spi": "Current SPI must be a valid number."})

        normalized_category = (category or '').upper()
        high_threshold_categories = {'GEN', 'OBC', 'EWS', 'GEN-EWS'}
        low_threshold_categories = {'SC', 'ST'}

        if normalized_category in high_threshold_categories and cpi < 8.0:
            raise DRFValidationError({"detail": "Minimum CPI should be 8.0 or more for GEN/OBC/EWS."})

        if normalized_category in low_threshold_categories and cpi < 7.0:
            raise DRFValidationError({"detail": "Minimum CPI should be 7.0 or more for SC/ST."})

    def perform_create(self, serializer):
        student = selectors.get_student_by_user(self.request.user)
        if not student:
            raise DRFValidationError({"detail": "Student profile required."})

        if McmApplication.objects.filter(student=student).exists():
            raise DRFValidationError({
                "detail": "You have already submitted an MCM application. Please edit the existing application."
            })

        payload = serializer.validated_data
        batch = payload.get('batch')

        self._validate_mcm_payload(
            batch=batch,
            category=payload.get('category'),
            current_cpi=payload.get('current_cpi'),
            current_spi=payload.get('current_spi'),
            jee_uceed_rank=payload.get('jee_uceed_rank'),
            jee_uceed_scorecard_link=payload.get('jee_uceed_scorecard_link')
        )

        save_kwargs = {
            "student": student,
            "status": STATUS["PENDING"],
            "revert_reason": None,
        }
        if str(batch or '').strip() == '2026':
            save_kwargs.update({"current_cpi": None, "current_spi": None})
        else:
            save_kwargs.update({"jee_uceed_rank": None, "jee_uceed_scorecard_link": None})

        serializer.save(**save_kwargs)

    def perform_update(self, serializer):
        instance = serializer.instance
        user = self.request.user
        is_admin = _is_admin(user)
        is_assistant = _has_designation(user, ['spacsassistant'])
        is_convenor = _has_designation(user, ['spacsconvenor'])
        is_student = not (is_admin or is_assistant or is_convenor)

        current_status = _normalize_status(instance.status)
        requested_status = _normalize_status(serializer.validated_data.get('status', current_status))

        if current_status in FINAL_STATUSES:
            raise DRFValidationError({"detail": "This application is finalized and cannot be updated."})

        if is_student:
            if current_status != STATUS["REVERTED"]:
                raise DRFValidationError({"detail": "You can edit only reverted applications."})
            requested_status = STATUS["PENDING"]
        elif is_assistant and not is_admin:
            if current_status != STATUS["PENDING"]:
                raise DRFValidationError({"detail": "Assistant can act only on pending applications."})
            if requested_status not in {STATUS["VERIFIED"], STATUS["REVERTED"]}:
                raise DRFValidationError({"detail": "Assistant can only verify or revert applications."})
        elif is_convenor and not is_admin:
            if current_status != STATUS["VERIFIED"]:
                raise DRFValidationError({"detail": "Convenor can act only on verified applications."})
            if requested_status not in {STATUS["APPROVED"], STATUS["REJECTED"]}:
                raise DRFValidationError({"detail": "Convenor can only approve or reject applications."})

        batch = serializer.validated_data.get('batch', instance.batch)
        payload = serializer.validated_data

        self._validate_mcm_payload(
            batch=batch,
            category=payload.get('category', instance.category),
            current_cpi=payload.get('current_cpi', instance.current_cpi),
            current_spi=payload.get('current_spi', instance.current_spi),
            jee_uceed_rank=payload.get('jee_uceed_rank', instance.jee_uceed_rank),
            jee_uceed_scorecard_link=payload.get('jee_uceed_scorecard_link', instance.jee_uceed_scorecard_link)
        )

        save_kwargs = {"status": requested_status}
        if requested_status in {STATUS["PENDING"], STATUS["VERIFIED"], STATUS["APPROVED"], STATUS["REJECTED"]}:
            save_kwargs["revert_reason"] = None

        if requested_status == STATUS["REVERTED"]:
            reason = serializer.validated_data.get('revert_reason')
            if not str(reason or '').strip():
                raise DRFValidationError({"revert_reason": "Revert reason is required."})
            save_kwargs["revert_reason"] = reason

        if str(batch or '').strip() == '2026':
            save_kwargs.update({"current_cpi": None, "current_spi": None})
        else:
            save_kwargs.update({"jee_uceed_rank": None, "jee_uceed_scorecard_link": None})

        serializer.save(**save_kwargs)


class SingleParentApplicationViewSet(viewsets.ModelViewSet):
    queryset = SingleParentApplication.objects.all()
    serializer_class = SingleParentApplicationSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        if _is_admin(user) or _has_designation(user, ['spacsassistant', 'spacsconvenor']):
            queryset = self.queryset
        else:
            student = selectors.get_student_by_user(user)
            if student:
                queryset = self.queryset.filter(student=student)
            else:
                queryset = self.queryset.none()

        status_filter = _normalize_status(self.request.query_params.get('status'))
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        batch_filter = str(self.request.query_params.get('batch') or '').strip()
        if batch_filter:
            queryset = queryset.filter(batch=batch_filter)

        return queryset

    def _validate_single_parent_cpi(self, batch, current_cpi):
        try:
            cpi = float(current_cpi)
        except (TypeError, ValueError):
            raise DRFValidationError({"detail": "Current CPI must be a valid number."})

        restricted_batches = {'2023', '2024', '2025'}
        if str(batch) in restricted_batches and cpi < 7.0:
            raise DRFValidationError({
                "detail": "For batch 2023/2024/2025, minimum CPI should be 7.0 or more."
            })

    def perform_create(self, serializer):
        student = selectors.get_student_by_user(self.request.user)
        if not student:
            raise DRFValidationError({"detail": "Student profile required."})

        if SingleParentApplication.objects.filter(student=student).exists():
            raise DRFValidationError({
                "detail": "You have already submitted a Single Parent scholarship application. Please edit the existing application."
            })

        self._validate_single_parent_cpi(
            serializer.validated_data.get('batch'),
            serializer.validated_data.get('current_cpi')
        )

        serializer.save(student=student, status=STATUS["PENDING"], revert_reason=None)

    def perform_update(self, serializer):
        instance = serializer.instance
        user = self.request.user
        is_admin = _is_admin(user)
        is_assistant = _has_designation(user, ['spacsassistant'])
        is_convenor = _has_designation(user, ['spacsconvenor'])
        is_student = not (is_admin or is_assistant or is_convenor)

        current_status = _normalize_status(instance.status)
        requested_status = _normalize_status(serializer.validated_data.get('status', current_status))

        if current_status in FINAL_STATUSES:
            raise DRFValidationError({"detail": "This application is finalized and cannot be updated."})

        if is_student:
            if current_status != STATUS["REVERTED"]:
                raise DRFValidationError({"detail": "You can edit only reverted applications."})
            requested_status = STATUS["PENDING"]
        elif is_assistant and not is_admin:
            if current_status != STATUS["PENDING"]:
                raise DRFValidationError({"detail": "Assistant can act only on pending applications."})
            if requested_status not in {STATUS["VERIFIED"], STATUS["REVERTED"]}:
                raise DRFValidationError({"detail": "Assistant can only verify or revert applications."})
        elif is_convenor and not is_admin:
            if current_status != STATUS["VERIFIED"]:
                raise DRFValidationError({"detail": "Convenor can act only on verified applications."})
            if requested_status not in {STATUS["APPROVED"], STATUS["REJECTED"]}:
                raise DRFValidationError({"detail": "Convenor can only approve or reject applications."})

        batch = serializer.validated_data.get('batch', instance.batch)
        current_cpi = serializer.validated_data.get('current_cpi', instance.current_cpi)
        self._validate_single_parent_cpi(batch, current_cpi)

        save_kwargs = {"status": requested_status}
        if requested_status in {STATUS["PENDING"], STATUS["VERIFIED"], STATUS["APPROVED"], STATUS["REJECTED"]}:
            save_kwargs["revert_reason"] = None

        if requested_status == STATUS["REVERTED"]:
            reason = serializer.validated_data.get('revert_reason')
            if not str(reason or '').strip():
                raise DRFValidationError({"revert_reason": "Revert reason is required."})
            save_kwargs["revert_reason"] = reason

        serializer.save(**save_kwargs)


class ConvenorMcmMeritListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        allowed = _is_admin(request.user) or _has_designation(request.user, ['spacsconvenor'])
        if not allowed:
            return Response({"error": "Only SPACS convenor can view merit list."}, status=status.HTTP_403_FORBIDDEN)

        # Sort by batch, branch, then cpi (desc) and roll_no (since Rank is stored in cpi for 2026)
        queryset = MeritListRecord.objects.all().order_by('batch', 'branch', '-cpi', 'roll_no')

        batch = request.GET.get('batch')
        branch = request.GET.get('branch')

        if batch:
            queryset = queryset.filter(batch=str(batch).strip())

        if branch:
            queryset = queryset.filter(branch=branch)

        data = [
            {
                'id': row.id,
                'batch': row.batch,
                'branch': row.branch,
                'full_name': row.full_name,
                'roll_no': row.roll_no,
                'cpi': str(row.cpi) if row.cpi else None,
            }
            for row in queryset
        ]

        return Response(data, status=status.HTTP_200_OK)



