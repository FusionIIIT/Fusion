"""
Security Audit Command for Visitor Hostel Module
Performs comprehensive security checks and generates audit reports
"""

import json
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.utils import timezone

from applications.visitor_hostel.models import BookingDetail, Inventory
from applications.visitor_hostel.security.rbac import (
    get_user_vh_roles, get_user_permissions, VHDataFilter,
    validate_booking_access, has_permission, VHPermission
)
from applications.visitor_hostel.logging_config import vh_logger

class Command(BaseCommand):
    help = 'Run comprehensive security audit for Visitor Hostel module'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-users',
            type=int,
            default=5,
            help='Number of test users to create for audit (default: 5)'
        )
        parser.add_argument(
            '--generate-report',
            action='store_true',
            help='Generate detailed security audit report'
        )
        parser.add_argument(
            '--check-permissions',
            action='store_true',
            help='Check permission matrix integrity'
        )
        parser.add_argument(
            '--test-data-access',
            action='store_true',
            help='Test data access controls'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show verbose output'
        )

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']
        self.verbose = options['verbose']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting security audit for Visitor Hostel module'
            )
        )
        
        audit_results = {
            'timestamp': timezone.now().isoformat(),
            'tests_run': [],
            'vulnerabilities': [],
            'recommendations': [],
            'security_score': 0
        }
        
        # Run permission matrix check
        if options['check_permissions']:
            self.stdout.write('Checking permission matrix...')
            perm_results = self.check_permission_matrix()
            audit_results['tests_run'].append('permission_matrix')
            audit_results['vulnerabilities'].extend(perm_results['vulnerabilities'])
            audit_results['recommendations'].extend(perm_results['recommendations'])
        
        # Test data access controls
        if options['test_data_access']:
            self.stdout.write('Testing data access controls...')
            access_results = self.test_data_access_controls(options['test_users'])
            audit_results['tests_run'].append('data_access_controls')
            audit_results['vulnerabilities'].extend(access_results['vulnerabilities'])
            audit_results['recommendations'].extend(access_results['recommendations'])
        
        # Check API security
        self.stdout.write('Checking API security...')
        api_results = self.check_api_security()
        audit_results['tests_run'].append('api_security')
        audit_results['vulnerabilities'].extend(api_results['vulnerabilities'])
        audit_results['recommendations'].extend(api_results['recommendations'])
        
        # Check authentication and session security
        self.stdout.write('Checking authentication security...')
        auth_results = self.check_authentication_security()
        audit_results['tests_run'].append('authentication_security')
        audit_results['vulnerabilities'].extend(auth_results['vulnerabilities'])
        audit_results['recommendations'].extend(auth_results['recommendations'])
        
        # Calculate security score
        total_vulnerabilities = len(audit_results['vulnerabilities'])
        critical_vulns = len([v for v in audit_results['vulnerabilities'] if v['severity'] == 'critical'])
        high_vulns = len([v for v in audit_results['vulnerabilities'] if v['severity'] == 'high'])
        
        # Security score calculation (0-100)
        base_score = 100
        score_deduction = (critical_vulns * 25) + (high_vulns * 15) + (total_vulnerabilities * 5)
        audit_results['security_score'] = max(0, base_score - score_deduction)
        
        # Generate report
        if options['generate_report']:
            self.generate_audit_report(audit_results)
        
        # Display summary
        self.display_audit_summary(audit_results)
        
        self.stdout.write(
            self.style.SUCCESS(f'Security audit completed. Score: {audit_results["security_score"]}/100')
        )

    def check_permission_matrix(self):
        """Check permission matrix for inconsistencies"""
        results = {'vulnerabilities': [], 'recommendations': []}
        
        try:
            # Check if all roles have defined permissions
            from applications.visitor_hostel.security.rbac import ROLE_PERMISSIONS, VHUserRole
            
            required_roles = [
                VHUserRole.VH_INCHARGE,
                VHUserRole.VH_CARETAKER,
                VHUserRole.FACULTY,
                VHUserRole.STUDENT,
                VHUserRole.STAFF
            ]
            
            for role in required_roles:
                if role not in ROLE_PERMISSIONS:
                    results['vulnerabilities'].append({
                        'type': 'missing_role_permissions',
                        'severity': 'high',
                        'description': f'Role {role} has no defined permissions',
                        'recommendation': f'Define permissions for role {role}'
                    })
                
                # Check for overly permissive roles
                role_perms = ROLE_PERMISSIONS.get(role, [])
                if VHPermission.VIEW_ALL_BOOKINGS in role_perms and role in [VHUserRole.STUDENT, VHUserRole.FACULTY]:
                    results['vulnerabilities'].append({
                        'type': 'overly_permissive_role',
                        'severity': 'medium',
                        'description': f'Role {role} has VIEW_ALL_BOOKINGS permission',
                        'recommendation': f'Remove VIEW_ALL_BOOKINGS from {role} role'
                    })
            
            if self.verbose:
                self.stdout.write(f'  ✓ Permission matrix check completed')
        
        except Exception as e:
            results['vulnerabilities'].append({
                'type': 'permission_matrix_error',
                'severity': 'critical',
                'description': f'Error checking permission matrix: {str(e)}',
                'recommendation': 'Fix permission matrix configuration'
            })
        
        return results

    def test_data_access_controls(self, num_test_users):
        """Test data access controls with different user types"""
        results = {'vulnerabilities': [], 'recommendations': []}
        
        try:
            # Create test users
            test_users = self.create_test_users(num_test_users)
            
            # Get sample bookings
            sample_bookings = BookingDetail.objects.all()[:10]
            
            for user in test_users:
                user_roles = get_user_vh_roles(user)
                
                for booking in sample_bookings:
                    # Test booking access
                    can_access = VHDataFilter.can_access_booking(booking, user)
                    should_access = (booking.intender == user or 
                                   any(role in ['VhIncharge', 'VhCaretaker', 'admin'] for role in user_roles))
                    
                    if can_access != should_access:
                        results['vulnerabilities'].append({
                            'type': 'data_access_violation',
                            'severity': 'high' if can_access and not should_access else 'medium',
                            'description': f'User {user.username} access to booking {booking.id} is {"allowed" if can_access else "denied"} but should be {"allowed" if should_access else "denied"}',
                            'recommendation': 'Fix data access filtering logic'
                        })
                    
                    # Test modification access
                    can_modify = VHDataFilter.can_modify_booking(booking, user)
                    should_modify = (booking.intender == user and booking.status in ['Pending', 'Forward']) or \
                                  any(role in ['VhIncharge'] for role in user_roles)
                    
                    if can_modify != should_modify:
                        results['vulnerabilities'].append({
                            'type': 'modification_access_violation',
                            'severity': 'critical' if can_modify and not should_modify else 'medium',
                            'description': f'User {user.username} modification access to booking {booking.id} is incorrect',
                            'recommendation': 'Fix booking modification access controls'
                        })
            
            if self.verbose:
                self.stdout.write(f'  ✓ Data access controls tested with {len(test_users)} users')
                
        except Exception as e:
            results['vulnerabilities'].append({
                'type': 'data_access_test_error',
                'severity': 'critical',
                'description': f'Error testing data access controls: {str(e)}',
                'recommendation': 'Fix data access testing implementation'
            })
        
        return results

    def check_api_security(self):
        """Check API endpoint security"""
        results = {'vulnerabilities': [], 'recommendations': []}
        
        try:
            # Check if views have proper authentication
            from applications.visitor_hostel.api.views import (
                ActiveBookingsApiView, PendingBookingsApiView, ConfirmBookingApiView
            )
            
            critical_views = [
                ActiveBookingsApiView,
                PendingBookingsApiView, 
                ConfirmBookingApiView
            ]
            
            for view_class in critical_views:
                # Check authentication classes
                auth_classes = getattr(view_class, 'authentication_classes', None)
                if not auth_classes:
                    results['vulnerabilities'].append({
                        'type': 'missing_authentication',
                        'severity': 'critical',
                        'description': f'View {view_class.__name__} has no authentication classes',
                        'recommendation': f'Add authentication_classes to {view_class.__name__}'
                    })
                
                # Check permission classes
                perm_classes = getattr(view_class, 'permission_classes', None)
                if not perm_classes:
                    results['vulnerabilities'].append({
                        'type': 'missing_permissions',
                        'severity': 'critical',
                        'description': f'View {view_class.__name__} has no permission classes',
                        'recommendation': f'Add permission_classes to {view_class.__name__}'
                    })
            
            if self.verbose:
                self.stdout.write(f'  ✓ API security check completed')
                
        except Exception as e:
            results['vulnerabilities'].append({
                'type': 'api_security_error',
                'severity': 'high',
                'description': f'Error checking API security: {str(e)}',
                'recommendation': 'Fix API security checking implementation'
            })
        
        return results

    def check_authentication_security(self):
        """Check authentication and session security"""
        results = {'vulnerabilities': [], 'recommendations': []}
        
        try:
            from django.conf import settings
            
            # Check session security settings
            session_checks = [
                ('SESSION_COOKIE_SECURE', True, 'Session cookies should be secure'),
                ('SESSION_COOKIE_HTTPONLY', True, 'Session cookies should be HTTP only'),
                ('CSRF_COOKIE_SECURE', True, 'CSRF cookies should be secure'),
                ('SECURE_SSL_REDIRECT', True, 'SSL redirect should be enabled'),
                ('SECURE_CONTENT_TYPE_NOSNIFF', True, 'Content type nosniff should be enabled'),
            ]
            
            for setting_name, expected_value, description in session_checks:
                actual_value = getattr(settings, setting_name, None)
                if actual_value != expected_value:
                    results['vulnerabilities'].append({
                        'type': 'insecure_setting',
                        'severity': 'medium',
                        'description': f'{setting_name} is {actual_value}, should be {expected_value}',
                        'recommendation': f'Set {setting_name} = {expected_value}'
                    })
            
            # Check password policies
            auth_password_validators = getattr(settings, 'AUTH_PASSWORD_VALIDATORS', [])
            if len(auth_password_validators) < 3:
                results['vulnerabilities'].append({
                    'type': 'weak_password_policy',
                    'severity': 'medium',
                    'description': 'Insufficient password validators configured',
                    'recommendation': 'Add more password validators for stronger passwords'
                })
            
            if self.verbose:
                self.stdout.write(f'  ✓ Authentication security check completed')
                
        except Exception as e:
            results['vulnerabilities'].append({
                'type': 'auth_security_error',
                'severity': 'medium',
                'description': f'Error checking authentication security: {str(e)}',
                'recommendation': 'Fix authentication security checking'
            })
        
        return results

    def create_test_users(self, count):
        """Create test users with different roles"""
        users = []
        
        try:
            # Create regular users
            for i in range(count):
                username = f'test_audit_user_{i}'
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': f'{username}@test.com',
                        'first_name': f'Test{i}',
                        'last_name': 'User'
                    }
                )
                users.append(user)
            
            return users
            
        except Exception as e:
            self.stdout.write(f'Error creating test users: {str(e)}')
            return []

    def generate_audit_report(self, audit_results):
        """Generate detailed audit report"""
        try:
            report_filename = f"vh_security_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Add system information
            audit_results['system_info'] = {
                'total_users': User.objects.count(),
                'total_bookings': BookingDetail.objects.count(),
                'total_inventory_items': Inventory.objects.count(),
                'django_version': getattr(settings, 'DJANGO_VERSION', 'unknown'),
            }
            
            with open(report_filename, 'w') as f:
                json.dump(audit_results, f, indent=2, default=str)
            
            self.stdout.write(f'Detailed audit report saved to: {report_filename}')
            
        except Exception as e:
            self.stdout.write(f'Error generating audit report: {str(e)}')

    def display_audit_summary(self, audit_results):
        """Display audit summary"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.HTTP_INFO('SECURITY AUDIT SUMMARY'))
        self.stdout.write('='*60)
        
        # Security score
        score = audit_results['security_score']
        if score >= 90:
            score_style = self.style.SUCCESS
            score_label = 'EXCELLENT'
        elif score >= 70:
            score_style = self.style.WARNING
            score_label = 'GOOD'
        elif score >= 50:
            score_style = self.style.ERROR
            score_label = 'NEEDS IMPROVEMENT'
        else:
            score_style = self.style.ERROR
            score_label = 'CRITICAL'
        
        self.stdout.write(f'Security Score: {score_style(f"{score}/100")} ({score_label})')
        
        # Vulnerability summary
        vulnerabilities = audit_results['vulnerabilities']
        critical = len([v for v in vulnerabilities if v['severity'] == 'critical'])
        high = len([v for v in vulnerabilities if v['severity'] == 'high'])
        medium = len([v for v in vulnerabilities if v['severity'] == 'medium'])
        
        self.stdout.write(f'\nVulnerabilities Found:')
        self.stdout.write(f'  Critical: {self.style.ERROR(str(critical))}')
        self.stdout.write(f'  High: {self.style.WARNING(str(high))}')
        self.stdout.write(f'  Medium: {str(medium)}')
        
        # Top recommendations
        if audit_results['recommendations']:
            self.stdout.write(f'\nTop Recommendations:')
            for i, rec in enumerate(audit_results['recommendations'][:5], 1):
                self.stdout.write(f'  {i}. {rec}')
        
        # Tests run
        self.stdout.write(f'\nTests Run: {", ".join(audit_results["tests_run"])}')
        
        self.stdout.write('\n' + '='*60)