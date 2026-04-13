"""
API views for T22 (Analytics Dashboard), T23 (User Feedback), and T24 (Health Check/Verification).
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from applications.otheracademic.analytics_models import (
    Analytics, Feedback, FeedbackHelpfulness, SystemHealthCheck, APICallLog
)
from applications.otheracademic.analytics_service import AnalyticsService
from applications.otheracademic.verification_service import VerificationService


class AnalyticsDashboardViewSet(viewsets.ViewSet):
    """T22: Analytics dashboard endpoints."""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get dashboard summary with all key metrics."""
        user = request.user
        
        # Check if user is admin/staff
        if not (user.is_staff or user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        summary = AnalyticsService.get_dashboard_summary()
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def departments(self, request):
        """Get analytics for all departments."""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = AnalyticsService.get_all_departments_analytics()
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def escalations(self, request):
        """Get escalation statistics."""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
        except (ValueError, TypeError):
            days = 30
        
        data = AnalyticsService.get_escalation_analytics(days=days)
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def timeline(self, request):
        """Get clearance timeline."""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
        except (ValueError, TypeError):
            days = 30
        
        data = AnalyticsService.get_clearance_timeline(days=days)
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def turnaround_time(self, request):
        """Get turnaround time statistics."""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = AnalyticsService.get_turnaround_time_analytics()
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def department_detail(self, request):
        """Get detailed analytics for specific department."""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        dept = request.query_params.get('dept')
        if not dept:
            return Response(
                {'error': 'Missing dept parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = AnalyticsService.get_department_analytics(dept)
        return Response(data)
    
    @action(detail=False, methods=['post'])
    def generate_daily(self, request):
        """Manually trigger daily analytics generation."""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            results = AnalyticsService.generate_daily_analytics()
            return Response({
                'status': 'success',
                'results': results,
                'timestamp': timezone.now().isoformat(),
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FeedbackViewSet(viewsets.ModelViewSet):
    """T23: User feedback collection and management."""
    queryset = Feedback.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter feedback based on user role."""
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            return Feedback.objects.all().order_by('-created_at')
        
        # Students see their own + public responses to their feedback
        return Feedback.objects.filter(user=user).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Submit new feedback."""
        user = request.user
        
        data = request.data
        try:
            feedback = Feedback.objects.create(
                user=user,
                category=data.get('category', 'other'),
                rating=int(data.get('rating', 3)),
                title=data.get('title', 'Feedback'),
                comment=data.get('comment', ''),
                is_anonymous=data.get('is_anonymous', False),
            )
            
            return Response({
                'id': feedback.id,
                'status': 'success',
                'message': 'Feedback submitted successfully',
                'feedback': {
                    'id': feedback.id,
                    'category': feedback.category,
                    'rating': feedback.rating,
                    'title': feedback.title,
                    'created_at': feedback.created_at.isoformat(),
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def mark_helpful(self, request, pk=None):
        """Mark feedback as helpful."""
        try:
            feedback = self.get_object()
        except Feedback.DoesNotExist:
            return Response(
                {'error': 'Feedback not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        is_helpful = request.data.get('is_helpful', True)
        
        # Create or update helpfulness
        helpfulness, created = FeedbackHelpfulness.objects.update_or_create(
            feedback=feedback,
            user=request.user,
            defaults={'is_helpful': is_helpful}
        )
        
        # Update feedback helpful count
        feedback.helpful_count = FeedbackHelpfulness.objects.filter(
            feedback=feedback,
            is_helpful=True
        ).count()
        feedback.save(update_fields=['helpful_count'])
        
        return Response({
            'status': 'success',
            'is_helpful': is_helpful,
            'helpful_count': feedback.helpful_count,
        })
    
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Admin response to feedback."""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            feedback = self.get_object()
        except Feedback.DoesNotExist:
            return Response(
                {'error': 'Feedback not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        admin_response = request.data.get('admin_response', '')
        
        feedback.admin_response = admin_response
        feedback.responded_by = request.user
        feedback.responded_at = timezone.now()
        feedback.save()
        
        return Response({
            'status': 'success',
            'message': 'Response submitted',
            'responded_at': feedback.responded_at.isoformat(),
        })
    
    @action(detail=False, methods=['get'])
    def aggregated_ratings(self, request):
        """Get aggregated rating statistics."""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = Feedback.get_aggregated_ratings()
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent feedback that needs response."""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        limit = request.query_params.get('limit', 10)
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 10
        
        feedback_list = Feedback.objects.filter(admin_response__isnull=True).order_by('-created_at')[:limit]
        
        return Response([
            {
                'id': f.id,
                'user': 'Anonymous' if f.is_anonymous else f.user.username,
                'category': f.category,
                'rating': f.rating,
                'title': f.title,
                'comment': f.comment,
                'created_at': f.created_at.isoformat(),
            }
            for f in feedback_list
        ])


class HealthCheckViewSet(viewsets.ViewSet):
    """T24: System health checks and verification."""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def full_system_check(self, request):
        """Run comprehensive system verification."""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            results = VerificationService.run_full_verification()
            return Response(results)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def check_models(self, request):
        """Check if all required models exist."""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            results = VerificationService.check_models()
            return Response(results)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def check_migrations(self, request):
        """Check if all migrations are applied."""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            results = VerificationService.check_migrations()
            return Response(results)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def check_permissions(self, request):
        """Check RBAC permission enforcement."""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            results = VerificationService.check_permissions()
            return Response(results)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def check_endpoints(self, request):
        """Verify all API endpoints are accessible."""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            results = VerificationService.check_endpoints()
            return Response(results)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def check_audit_logging(self, request):
        """Verify audit logging is working."""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            results = VerificationService.check_audit_logging()
            return Response(results)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def check_database_integrity(self, request):
        """Verify database integrity and constraints."""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            results = VerificationService.check_database_integrity()
            return Response(results)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def latest_checks(self, request):
        """Get latest health check results."""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        checks = SystemHealthCheck.objects.order_by('-timestamp')[:20]
        return Response([
            {
                'check_type': c.check_type,
                'status': c.status,
                'message': c.message,
                'timestamp': c.timestamp.isoformat(),
            }
            for c in checks
        ])
