"""
API views for No Dues escalation workflow and audit trail.

Endpoints:
- GET /api/otheracademic/escalations/ - List pending escalations (admin/dean/director)
- GET /api/otheracademic/escalations/<id>/ - Get escalation details
- POST /api/otheracademic/escalations/<id>/approve/ - Manual approval
- POST /api/otheracademic/escalations/<id>/reject/ - Manual rejection
- GET /api/otheracademic/audit-log/ - Query audit logs (admin only)
- GET /api/otheracademic/audit-log/<model>/<id>/ - Get change history for object
- GET /api/otheracademic/student-audit-trail/ - Get student's own audit trail
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from applications.otheracademic.models import NoDues
from applications.otheracademic.audit_models import (
    NoDuesEscalation,
    AuditLog,
    NoDuesClearanceHistory,
)
from applications.otheracademic.escalation_service import NoDuesEscalationService
from applications.otheracademic.api.permissions import (
    IsHOD,
    IsDean,
    IsDirector,
    IsTA_Supervisor,
)


class NoDuesEscalationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing No Dues escalations.
    
    Permissions:
    - List/Get: Students (own only), HOD/Dean/Director (all)
    - Approve/Reject: HOD/Dean/Director only
    """
    queryset = NoDuesEscalation.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter escalations based on user role."""
        user = self.request.user
        
        # Admins see all
        if user.is_staff or user.is_superuser:
            return NoDuesEscalation.objects.all().order_by('-created_at')
        
        # HOD sees escalations for their department
        if hasattr(user, 'holds_designation') and user.holds_designation.filter(
            designation__title__icontains='HOD'
        ).exists():
            dept = user.holds_designation.first().department
            return NoDuesEscalation.objects.filter(
                Q(department=dept) | Q(no_dues__department=dept)
            ).order_by('-created_at')
        
        # Dean sees all (adjust based on your institution structure)
        if hasattr(user, 'holds_designation') and user.holds_designation.filter(
            designation__title__icontains='Dean'
        ).exists():
            return NoDuesEscalation.objects.all().order_by('-created_at')
        
        # Students see only their own
        return NoDuesEscalation.objects.filter(student=user).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """List escalations with filtering options."""
        queryset = self.get_queryset()
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by department
        dept_filter = request.query_params.get('department')
        if dept_filter:
            queryset = queryset.filter(department=dept_filter)
        
        # Filter by type
        type_filter = request.query_params.get('escalation_type')
        if type_filter:
            queryset = queryset.filter(escalation_type=type_filter)
        
        # Filter by date range
        days_filter = request.query_params.get('days', 30)
        try:
            days = int(days_filter)
            cutoff = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(created_at__gte=cutoff)
        except (ValueError, TypeError):
            pass
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Get detailed escalation information."""
        try:
            escalation = self.get_queryset().get(pk=pk)
        except NoDuesEscalation.DoesNotExist:
            return Response(
                {'error': 'Escalation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(escalation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """
        Manually approve (mark as clear) No Dues for a department.
        
        Body:
        {
            "reason": "Verified and cleared",
            "department": "library",
        }
        """
        try:
            escalation = self.get_queryset().get(pk=pk)
        except NoDuesEscalation.DoesNotExist:
            return Response(
                {'error': 'Escalation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permission (must be admin or relevant HOD)
        user = request.user
        if not (user.is_staff or user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reason = request.data.get('reason', '')
        
        try:
            # Mark as clear using the service
            NoDuesEscalationService.mark_clear_manually(
                escalation.no_dues,
                escalation.department,
                user,
                reason
            )
            
            # Update escalation record
            escalation.status = 'completed'
            escalation.completed_at = timezone.now()
            escalation.save()
            
            return Response({
                'status': 'success',
                'message': f'{escalation.department} marked as clear',
                'escalation': {
                    'id': escalation.id,
                    'status': escalation.status,
                    'completed_at': escalation.completed_at.isoformat(),
                }
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        """
        Manually reject (mark as NOT clear) No Dues for a department.
        
        Body:
        {
            "reason": "Books not returned",
            "department": "library",
        }
        """
        try:
            escalation = self.get_queryset().get(pk=pk)
        except NoDuesEscalation.DoesNotExist:
            return Response(
                {'error': 'Escalation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permission
        user = request.user
        if not (user.is_staff or user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reason = request.data.get('reason', 'Standards not met')
        
        try:
            # Mark as not clear
            NoDuesEscalationService.mark_notclear_manually(
                escalation.no_dues,
                escalation.department,
                user,
                reason
            )
            
            # Update escalation record
            escalation.status = 'completed'
            escalation.completed_at = timezone.now()
            escalation.save()
            
            return Response({
                'status': 'success',
                'message': f'{escalation.department} marked as NOT clear',
                'escalation': {
                    'id': escalation.id,
                    'status': escalation.status,
                    'completed_at': escalation.completed_at.isoformat(),
                }
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def pending(self, request):
        """Get all pending escalations."""
        queryset = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_history(self, request):
        """Get escalation history for current student."""
        escalations = NoDuesEscalation.objects.filter(student=request.user).order_by('-created_at')
        history = NoDuesEscalationService.get_escalation_status(request.user)
        return Response(history)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for querying audit logs.
    
    Permissions:
    - Admin/Staff: Can see all audit logs
    - Students: Can only see their own audit trail
    
    Query Parameters:
    - model: Filter by model name (e.g., 'NoDues', 'LeavePG')
    - user: Filter by user who made the change
    - action: Filter by action type (create, update, delete, escalate, approve, reject)
    - department: Filter by department
    - days: Filter by date range (last N days)
    - student: Filter by student (for staff only)
    """
    queryset = AuditLog.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter audit logs based on user role."""
        user = self.request.user
        
        # Admins see all
        if user.is_staff or user.is_superuser:
            return AuditLog.objects.all().order_by('-timestamp')
        
        # Students see only their own
        return AuditLog.objects.filter(related_user=user).order_by('-timestamp')
    
    def list(self, request, *args, **kwargs):
        """List audit logs with filtering."""
        queryset = self.get_queryset()
        
        # Filter by model
        model_filter = request.query_params.get('model')
        if model_filter:
            queryset = queryset.filter(model_name=model_filter)
        
        # Filter by action
        action_filter = request.query_params.get('action')
        if action_filter:
            queryset = queryset.filter(action=action_filter)
        
        # Filter by department
        dept_filter = request.query_params.get('department')
        if dept_filter:
            queryset = queryset.filter(department=dept_filter)
        
        # Filter by user (admin only)
        if request.user.is_staff:
            user_filter = request.query_params.get('user')
            if user_filter:
                queryset = queryset.filter(user__username=user_filter)
        
        # Filter by date range
        days_filter = request.query_params.get('days', 90)
        try:
            days = int(days_filter)
            cutoff = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(timestamp__gte=cutoff)
        except (ValueError, TypeError):
            pass
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def history(self, request):
        """Get complete change history for a specific object."""
        model_name = request.query_params.get('model')
        object_id = request.query_params.get('id')
        
        if not model_name or not object_id:
            return Response(
                {'error': 'Missing model or id parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        history = AuditLog.get_history(model_name, object_id)
        
        if not history and not request.user.is_staff:
            return Response(
                {'error': 'Not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'model': model_name,
            'object_id': object_id,
            'changes': history,
            'total': len(history),
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def user_actions(self, request):
        """Get all actions by a specific user."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        username = request.query_params.get('user')
        limit = request.query_params.get('limit', 100)
        
        if not username:
            return Response(
                {'error': 'Missing user parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            limit = int(limit)
        except ValueError:
            limit = 100
        
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        actions = AuditLog.get_user_actions(user, limit)
        
        return Response({
            'user': username,
            'actions': actions,
            'total': len(actions),
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def student_trail(self, request):
        """Get complete audit trail for a student."""
        student_id = request.query_params.get('student_id')
        
        # Students can only view their own trail
        if not request.user.is_staff:
            student_id = request.user.id
        elif not student_id:
            return Response(
                {'error': 'Missing student_id parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.contrib.auth.models import User
        try:
            student = User.objects.get(id=student_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Student not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        actions = AuditLog.get_actions_for_student(student, limit=500)
        
        return Response({
            'student': student.username,
            'student_id': student.id,
            'actions': actions,
            'total': len(actions),
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_trail(self, request):
        """Get current user's own audit trail."""
        limit = request.query_params.get('limit', 100)
        try:
            limit = int(limit)
        except ValueError:
            limit = 100
        
        actions = AuditLog.get_actions_for_student(request.user, limit=limit)
        
        return Response({
            'user': request.user.username,
            'actions': actions,
            'total': len(actions),
        })


class NoDuesClearanceHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing No Dues clearance history.
    
    Shows who cleared/rejected what and when for each department.
    """
    queryset = NoDuesClearanceHistory.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter history based on user role."""
        user = self.request.user
        
        # Admins see all
        if user.is_staff or user.is_superuser:
            return NoDuesClearanceHistory.objects.all().order_by('-changed_at')
        
        # Students see only their own
        return NoDuesClearanceHistory.objects.filter(student=user).order_by('-changed_at')
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def student_history(self, request):
        """Get clearance history for a student."""
        history = NoDuesEscalationService.get_student_history(request.user)
        return Response({
            'student': request.user.username,
            'history': history,
            'total': len(history),
        })
