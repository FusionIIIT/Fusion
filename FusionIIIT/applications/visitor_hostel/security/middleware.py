"""
Security Middleware for Visitor Hostel Module
Provides additional security layers and monitoring
"""

import time
import json
from django.http import JsonResponse
from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin
from applications.visitor_hostel.logging_config import vh_logger
from .rbac import get_user_vh_roles, get_user_permissions

class VHSecurityMiddleware(MiddlewareMixin):
    """
    Security middleware for Visitor Hostel API endpoints
    Provides additional authentication validation and security logging
    """
    
    # Endpoints that require authentication
    PROTECTED_ENDPOINTS = [
        'visitorhostel_api:pending_bookings',
        'visitorhostel_api:active_bookings',
        'visitorhostel_api:completed_bookings',
        'visitorhostel_api:booking_detail',
        'visitorhostel_api:request_booking',
        'visitorhostel_api:confirm_booking',
        'visitorhostel_api:cancel_booking',
        'visitorhostel_api:check_in',
        'visitorhostel_api:check_out',
        'visitorhostel_api:settle_bill',
        'visitorhostel_api:bill_generation',
        'visitorhostel_api:inventory_list',
        'visitorhostel_api:add_to_inventory',
        'visitorhostel_api:update_inventory',
        'visitorhostel_api:booking_reports',
        'visitorhostel_api:inventory_reports',
        'visitorhostel_api:bill_between_dates',
    ]
    
    # Staff-only endpoints
    STAFF_ONLY_ENDPOINTS = [
        'visitorhostel_api:confirm_booking',
        'visitorhostel_api:reject_booking',
        'visitorhostel_api:forward_booking',
        'visitorhostel_api:check_in',
        'visitorhostel_api:check_out',
        'visitorhostel_api:bill_generation',
        'visitorhostel_api:settle_bill',
        'visitorhostel_api:detect_no_shows',
        'visitorhostel_api:detect_overstays',
        'visitorhostel_api:detect_due_checkouts',
        'visitorhostel_api:edit_room_status',
        'visitorhostel_api:inventory_reports',
        'visitorhostel_api:booking_reports',
        'visitorhostel_api:approve_replenishment',
        'visitorhostel_api:reject_replenishment',
    ]
    
    # Incharge-only endpoints
    INCHARGE_ONLY_ENDPOINTS = [
        'visitorhostel_api:confirm_booking',
        'visitorhostel_api:reject_booking',
        'visitorhostel_api:settle_bill',
        'visitorhostel_api:approve_replenishment',
        'visitorhostel_api:reject_replenishment',
    ]

    def process_request(self, request):
        """Process incoming request for security validation"""
        
        # Skip non-API requests
        if not request.path.startswith('/visitorhostel/api/'):
            return None
        
        # Skip health check
        if 'health' in request.path:
            return None
        
        try:
            # Get URL name
            resolved = resolve(request.path)
            url_name = f"{resolved.namespace}:{resolved.url_name}" if resolved.namespace else resolved.url_name
            
            # Log all API access attempts
            vh_logger.log_security_event('api_access_attempt', request.user if hasattr(request, 'user') else None, {
                'path': request.path,
                'method': request.method,
                'url_name': url_name,
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown')
            })
            
            # Check authentication for protected endpoints
            if url_name in self.PROTECTED_ENDPOINTS:
                if not hasattr(request, 'user') or not request.user.is_authenticated:
                    vh_logger.log_security_event('unauthorized_api_access', None, {
                        'path': request.path,
                        'ip_address': self.get_client_ip(request),
                        'reason': 'not_authenticated'
                    })
                    return JsonResponse({
                        'error': 'Authentication required',
                        'code': 'AUTH_REQUIRED'
                    }, status=401)
            
            # Check staff permissions
            if url_name in self.STAFF_ONLY_ENDPOINTS:
                if not self.is_vh_staff(request.user):
                    vh_logger.log_security_event('unauthorized_api_access', request.user, {
                        'path': request.path,
                        'url_name': url_name,
                        'reason': 'insufficient_staff_permissions',
                        'user_roles': get_user_vh_roles(request.user)
                    })
                    return JsonResponse({
                        'error': 'VH staff access required',
                        'code': 'STAFF_ACCESS_REQUIRED'
                    }, status=403)
            
            # Check incharge permissions
            if url_name in self.INCHARGE_ONLY_ENDPOINTS:
                if not self.is_vh_incharge(request.user):
                    vh_logger.log_security_event('unauthorized_api_access', request.user, {
                        'path': request.path,
                        'url_name': url_name,
                        'reason': 'insufficient_incharge_permissions',
                        'user_roles': get_user_vh_roles(request.user)
                    })
                    return JsonResponse({
                        'error': 'VH Incharge access required',
                        'code': 'INCHARGE_ACCESS_REQUIRED'
                    }, status=403)
            
        except Exception as e:
            vh_logger.log_security_event('security_middleware_error', getattr(request, 'user', None), {
                'error': str(e),
                'path': request.path
            })
        
        return None
    
    def process_response(self, request, response):
        """Process response for security logging"""
        
        # Log security-relevant responses
        if hasattr(request, 'path') and request.path.startswith('/visitorhostel/api/'):
            if response.status_code >= 400:
                vh_logger.log_security_event('api_error_response', getattr(request, 'user', None), {
                    'path': request.path,
                    'status_code': response.status_code,
                    'method': request.method
                })
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_vh_staff(self, user):
        """Check if user is VH staff"""
        if not user or not user.is_authenticated:
            return False
        
        user_roles = get_user_vh_roles(user)
        return ('VhIncharge' in user_roles or 'VhCaretaker' in user_roles or 
                'admin' in user_roles or user.is_staff)
    
    def is_vh_incharge(self, user):
        """Check if user is VH Incharge"""
        if not user or not user.is_authenticated:
            return False
        
        user_roles = get_user_vh_roles(user)
        return ('VhIncharge' in user_roles or 'admin' in user_roles or user.is_staff)

class VHRateLimitingMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware for VH API endpoints
    Prevents API abuse and brute force attempts
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.request_counts = {}  # In production, use Redis/Memcached
        self.blocked_ips = set()
    
    def process_request(self, request):
        """Apply rate limiting"""
        
        # Skip non-API requests
        if not request.path.startswith('/visitorhostel/api/'):
            return None
        
        client_ip = self.get_client_ip(request)
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            vh_logger.log_security_event('blocked_ip_access_attempt', None, {
                'ip_address': client_ip,
                'path': request.path
            })
            return JsonResponse({
                'error': 'Access denied - IP blocked',
                'code': 'IP_BLOCKED'
            }, status=429)
        
        # Rate limiting logic (simplified)
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window
        
        # Clean old entries
        if client_ip in self.request_counts:
            self.request_counts[client_ip] = [
                timestamp for timestamp in self.request_counts[client_ip] 
                if timestamp > window_start
            ]
        else:
            self.request_counts[client_ip] = []
        
        # Add current request
        self.request_counts[client_ip].append(current_time)
        
        # Check rate limit (60 requests per minute)
        if len(self.request_counts[client_ip]) > 60:
            vh_logger.log_security_event('rate_limit_exceeded', getattr(request, 'user', None), {
                'ip_address': client_ip,
                'request_count': len(self.request_counts[client_ip]),
                'path': request.path
            })
            
            # Block IP for repeated violations
            violations = sum(1 for ts in self.request_counts[client_ip] if ts > current_time - 300)
            if violations > 200:  # 200 requests in 5 minutes
                self.blocked_ips.add(client_ip)
                vh_logger.log_security_event('ip_blocked', None, {
                    'ip_address': client_ip,
                    'reason': 'repeated_rate_limit_violations'
                })
            
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'code': 'RATE_LIMIT_EXCEEDED'
            }, status=429)
        
        return None
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class VHDataProtectionMiddleware(MiddlewareMixin):
    """
    Data protection middleware to prevent data leaks
    """
    
    def process_response(self, request, response):
        """Process response to remove sensitive data"""
        
        # Only process VH API responses
        if not hasattr(request, 'path') or not request.path.startswith('/visitorhostel/api/'):
            return response
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # For error responses, sanitize sensitive information
        if response.status_code >= 400 and hasattr(response, 'content'):
            try:
                content = response.content.decode('utf-8')
                if 'traceback' in content.lower() or 'sql' in content.lower():
                    vh_logger.log_security_event('sensitive_data_in_response', getattr(request, 'user', None), {
                        'path': request.path,
                        'status_code': response.status_code
                    })
                    
                    # In production, replace with generic error message for non-staff users
                    if not getattr(request, 'user', None) or not request.user.is_staff:
                        response.content = json.dumps({
                            'error': 'An internal error occurred. Please contact support.',
                            'code': 'INTERNAL_ERROR'
                        }).encode('utf-8')
                        
            except Exception:
                pass
        
        return response