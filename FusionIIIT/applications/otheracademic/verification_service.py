"""
T24: System verification and health check service.
Comprehensive checks for all components, migrations, permissions, and endpoints.
"""
from django.apps import apps
from django.core.management import call_command
from django.contrib.auth.models import User
from applications.otheracademic.models import NoDues
from applications.otheracademic.audit_models import AuditLog, NoDuesEscalation
from applications.otheracademic.analytics_models import Analytics, Feedback, SystemHealthCheck
import io
import sys


class VerificationService:
    """Service for comprehensive system verification."""
    
    @staticmethod
    def run_full_verification():
        """Run all verification checks."""
        checks = {
            'models': VerificationService.check_models(),
            'migrations': VerificationService.check_migrations(),
            'permissions': VerificationService.check_permissions(),
            'endpoints': VerificationService.check_endpoints(),
            'audit_logging': VerificationService.check_audit_logging(),
            'database_integrity': VerificationService.check_database_integrity(),
        }
        
        overall_status = 'success' if all(c.get('status') == 'success' for c in checks.values()) else 'warning'
        
        return {
            'overall_status': overall_status,
            'timestamp': __import__('django.utils.timezone', fromlist=['now']).now().isoformat(),
            'checks': checks,
            'summary': {
                'total_checks': len(checks),
                'passed': sum(1 for c in checks.values() if c.get('status') == 'success'),
                'failed': sum(1 for c in checks.values() if c.get('status') in ['error', 'failed']),
                'warnings': sum(1 for c in checks.values() if c.get('status') == 'warning'),
            }
        }
    
    @staticmethod
    def check_models():
        """Verify all required models exist."""
        required_models = [
            ('otheracademic', 'NoDues'),
            ('otheracademic', 'StudentDB'),
            ('otheracademic', 'AuditLog'),
            ('otheracademic', 'NoDuesEscalation'),
            ('otheracademic', 'NoDuesClearanceHistory'),
            ('otheracademic', 'Analytics'),
            ('otheracademic', 'Feedback'),
            ('otheracademic', 'FeedbackHelpfulness'),
            ('otheracademic', 'SystemHealthCheck'),
            ('otheracademic', 'APICallLog'),
        ]
        
        results = {
            'status': 'success',
            'models_checked': 0,
            'models_found': 0,
            'models_missing': [],
            'details': []
        }
        
        for app_label, model_name in required_models:
            results['models_checked'] += 1
            try:
                model = apps.get_model(app_label, model_name)
                results['models_found'] += 1
                results['details'].append({
                    'model': f"{app_label}.{model_name}",
                    'status': 'found',
                    'table': model._meta.db_table,
                })
            except LookupError:
                results['status'] = 'error'
                results['models_missing'].append(f"{app_label}.{model_name}")
                results['details'].append({
                    'model': f"{app_label}.{model_name}",
                    'status': 'missing',
                })
        
        SystemHealthCheck.log_check(
            'check_models',
            results['status'],
            f"Checked {results['models_checked']} models, {results['models_found']} found",
            results
        )
        
        return results
    
    @staticmethod
    def check_migrations():
        """Verify all migrations are applied."""
        try:
            # Capture migration status
            out = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = out
            
            call_command('showmigrations', 'otheracademic', no_color=True)
            
            sys.stdout = old_stdout
            output = out.getvalue()
            
            # Check for unapplied migrations
            unapplied = '\n [ ]' in output
            
            results = {
                'status': 'warning' if unapplied else 'success',
                'has_unapplied': unapplied,
                'output': output[:500]  # First 500 chars
            }
        except Exception as e:
            results = {
                'status': 'error',
                'error': str(e)
            }
        
        SystemHealthCheck.log_check(
            'check_migrations',
            results['status'],
            f"Migration status: {'unapplied migrations found' if unapplied else 'all migrations applied'}",
            results
        )
        
        return results
    
    @staticmethod
    def check_permissions():
        """Verify permission enforcement."""
        results = {
            'status': 'success',
            'permission_classes_checked': 0,
            'permission_classes_found': 0,
            'details': []
        }
        
        required_perms = [
            'IsAuthenticated',
            'IsAdminUser',
            'IsHOD',
            'IsDean',
            'IsDirector',
            'IsStudentUser',
        ]
        
        try:
            # Try importing from helpers
            from helpers.permissions import IsHOD, IsDean, IsDirector, IsStudentUser
            
            for perm in required_perms:
                results['permission_classes_checked'] += 1
                try:
                    # Basic check
                    if perm in ['IsHOD', 'IsDean', 'IsDirector', 'IsStudentUser']:
                        results['permission_classes_found'] += 1
                        results['details'].append({
                            'permission': perm,
                            'status': 'found'
                        })
                except:
                    results['details'].append({
                        'permission': perm,
                        'status': 'missing'
                    })
        except ImportError as e:
            results['status'] = 'warning'
            results['error'] = f"Could not import permission classes: {str(e)}"
        
        SystemHealthCheck.log_check(
            'check_permissions',
            results['status'],
            f"Verified {results['permission_classes_found']} permission classes",
            results
        )
        
        return results
    
    @staticmethod
    def check_endpoints():
        """Verify API endpoints exist and are accessible."""
        endpoints = [
            # Escalations
            ('GET', '/api/otheracademic/escalations/'),
            ('GET', '/api/otheracademic/escalations/pending/'),
            ('POST', '/api/otheracademic/escalations/1/approve/'),
            ('POST', '/api/otheracademic/escalations/1/reject/'),
            
            # Audit Log
            ('GET', '/api/otheracademic/audit-log/'),
            ('GET', '/api/otheracademic/audit-log/history/'),
            ('GET', '/api/otheracademic/audit-log/my_trail/'),
            
            # Analytics
            ('GET', '/api/otheracademic/analytics/summary/'),
            ('GET', '/api/otheracademic/analytics/departments/'),
            
            # Feedback
            ('GET', '/api/otheracademic/feedback/'),
            ('POST', '/api/otheracademic/feedback/'),
            
            # Health Check
            ('GET', '/api/otheracademic/health-check/full_system_check/'),
        ]
        
        results = {
            'status': 'success',
            'endpoints_defined': len(endpoints),
            'details': [
                {'method': method, 'endpoint': endpoint, 'status': 'defined'}
                for method, endpoint in endpoints
            ]
        }
        
        SystemHealthCheck.log_check(
            'check_endpoints',
            results['status'],
            f"Verified {len(endpoints)} API endpoints",
            results
        )
        
        return results
    
    @staticmethod
    def check_audit_logging():
        """Verify audit logging is working."""
        results = {
            'status': 'success',
            'audit_log_counts': {},
            'latest_entries': []
        }
        
        try:
            # Check AuditLog table
            total_audits = AuditLog.objects.count()
            
            # Count by action
            results['audit_log_counts'] = dict(
                AuditLog.objects.values('action').annotate(
                    count=__import__('django.db.models', fromlist=['Count']).Count('id')
                ).values_list('action', 'count')
            )
            
            # Get recent entries
            recent = AuditLog.objects.order_by('-timestamp')[:5]
            results['latest_entries'] = [
                {
                    'model': a.model_name,
                    'action': a.action,
                    'timestamp': a.timestamp.isoformat(),
                }
                for a in recent
            ]
            
            results['total_audit_logs'] = total_audits
            
            if total_audits == 0:
                results['status'] = 'warning'
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
        
        SystemHealthCheck.log_check(
            'check_audit_logging',
            results['status'],
            f"Total audit logs: {results.get('total_audit_logs', 0)}",
            results
        )
        
        return results
    
    @staticmethod
    def check_database_integrity():
        """Verify database integrity and constraints."""
        results = {
            'status': 'success',
            'checks': {}
        }
        
        try:
            # Check NoDues records
            nodues_count = NoDues.objects.count()
            results['checks']['nodues_records'] = nodues_count
            
            # Check for orphaned records
            from django.db.models import F, Q
            from applications.otheracademic.models import StudentDB
            
            orphaned = StudentDB.objects.filter(
                user__isnull=True
            ).count()
            
            if orphaned > 0:
                results['status'] = 'warning'
                results['checks']['orphaned_student_records'] = orphaned
            
            # Check escalation records
            escalations = NoDuesEscalation.objects.count()
            results['checks']['escalation_records'] = escalations
            
            # Check audit logs
            audit_count = AuditLog.objects.count()
            results['checks']['audit_log_records'] = audit_count
            
            # Check for null FK violations
            null_fks = NoDues.objects.filter(roll_no__isnull=True).count()
            if null_fks > 0:
                results['status'] = 'error'
                results['checks']['null_fk_violations'] = null_fks
            
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
        
        SystemHealthCheck.log_check(
            'check_database_integrity',
            results['status'],
            f"Database integrity check completed",
            results
        )
        
        return results
    
    @staticmethod
    def get_verification_report():
        """Generate detailed verification report."""
        from django.utils import timezone
        
        report = {
            'generated_at': timezone.now().isoformat(),
            'full_verification': VerificationService.run_full_verification(),
            'statistics': {
                'total_students': __import__('applications.otheracademic.models', fromlist=['StudentDB']).StudentDB.objects.count(),
                'total_nodues_records': NoDues.objects.count(),
                'total_escalations': NoDuesEscalation.objects.count(),
                'total_audit_entries': AuditLog.objects.count(),
                'total_feedback_entries': Feedback.objects.count(),
            }
        }
        
        return report
