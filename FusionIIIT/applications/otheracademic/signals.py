"""
Django signals for automatic audit logging.

These signals automatically log all changes to key models without requiring manual API calls.
Connects to post_save and pre_delete signals to track all modifications.

Coverage:
- NoDues model changes (any field update)
- LeavePG model changes (for T1-11 integration)
- Assistantship model changes
- Any model that updates a field tracked in audit

Signal Pattern:
1. pre_save: Capture old values
2. post_save: Log the change
3. pre_delete: Prepare for deletion log
"""
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
import json

from applications.otheracademic.audit_models import AuditLog


# Dictionary to store old values before save (for comparison)
_pre_save_values = {}


@receiver(pre_save)
def capture_pre_save_values(sender, instance, **kwargs):
    """
    Capture model instance field values BEFORE saving.
    
    Stores in _pre_save_values dictionary keyed by (model_name, instance.pk).
    Used in post_save to determine what changed.
    """
    if not should_audit_model(sender):
        return
    
    model_name = sender.__name__
    model_key = (model_name, instance.pk)
    
    # If instance is new (no pk), no need to capture old values
    if instance.pk is None:
        _pre_save_values[model_key] = None
        return
    
    # Get previous values from database
    try:
        old_instance = sender.objects.get(pk=instance.pk)
        old_values = {}
        for field in instance._meta.fields:
            old_values[field.name] = getattr(old_instance, field.name)
        _pre_save_values[model_key] = old_values
    except sender.DoesNotExist:
        _pre_save_values[model_key] = None


@receiver(post_save)
def log_model_changes(sender, instance, created, **kwargs):
    """
    Log model changes to AuditLog after saving.
    
    Creates audit log entry for:
    - New instances (action='create')
    - Modified instances (action='update' with field name)
    """
    if not should_audit_model(sender):
        return
    
    # Get request from middleware context if available
    request = get_request_from_middleware()
    user = getattr(request, 'user', None) if request else None
    
    model_name = sender.__name__
    model_key = (model_name, instance.pk)
    
    try:
        if created:
            # New instance - log creation
            AuditLog.log_change(
                user=user,
                model_name=model_name,
                object_id=instance.pk,
                action='create',
                description=f'Created new {model_name}',
                request=request,
            )
        else:
            # Modified instance - check what changed
            old_values = _pre_save_values.get(model_key)
            if old_values:
                for field in instance._meta.fields:
                    new_value = getattr(instance, field.name)
                    old_value = old_values.get(field.name)
                    
                    # Skip if no actual change
                    if old_value == new_value:
                        continue
                    
                    # Skip large text fields for brevity
                    if field.get_internal_type() in ['TextField', 'FileField']:
                        continue
                    
                    # Log the change
                    AuditLog.log_change(
                        user=user,
                        model_name=model_name,
                        object_id=instance.pk,
                        action='update',
                        field_name=field.name,
                        old_value=serialize_value(old_value),
                        new_value=serialize_value(new_value),
                        description=f'Updated {field.name}',
                        request=request,
                    )
            
            # Clean up stored values
            if model_key in _pre_save_values:
                del _pre_save_values[model_key]
    
    except Exception as e:
        # Log errors but don't break the save
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in audit logging for {model_name}: {str(e)}")


@receiver(pre_delete)
def log_model_deletion(sender, instance, **kwargs):
    """
    Log model instance deletion.
    
    Creates audit log entry with action='delete'.
    """
    if not should_audit_model(sender):
        return
    
    request = get_request_from_middleware()
    user = getattr(request, 'user', None) if request else None
    
    model_name = sender.__name__
    
    try:
        AuditLog.log_change(
            user=user,
            model_name=model_name,
            object_id=instance.pk,
            action='delete',
            description=f'Deleted {model_name}',
            request=request,
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error logging deletion for {model_name}: {str(e)}")


def should_audit_model(model_class):
    """
    Determine if a model should be audited.
    
    Audited models:
    - NoDues
    - LeavePG
    - Assistantship
    - LeaveFormTable
    - others based on settings
    """
    model_name = model_class.__name__
    
    # Explicitly audited models
    audited_models = [
        'NoDues',
        'LeavePG',
        'Assistantship',
        'LeaveFormTable',
        'Leave',
        'OnlineComplaint',
        'AcademicHold',
    ]
    
    if model_name in audited_models:
        return True
    
    # Check settings if defined
    audited_from_settings = getattr(settings, 'AUDIT_MODELS', [])
    if model_name in audited_from_settings:
        return True
    
    return False


def serialize_value(value):
    """
    Serialize a Python value for JSON storage in AuditLog.
    
    Handles special types:
    - datetime objects → ISO format string
    - dict/list → JSON serializable
    - Django model instances → string repr
    - bool/None/int/str → pass through
    """
    if value is None:
        return None
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, (int, float, str)):
        return value
    
    if isinstance(value, (list, dict)):
        return value
    
    # Handle datetime
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    
    # Handle Django models
    if hasattr(value, '_meta'):
        return f"{value.__class__.__name__}({value.pk})"
    
    # Default to string representation
    return str(value)


def get_request_from_middleware():
    """
    Extract current request from thread-local middleware storage.
    
    Returns:
        HttpRequest or None
    
    Note:
        This requires a middleware to store request in threading.local()
        See RequestMiddleware below.
    """
    try:
        from threading import local
        thread_data = getattr(settings, '_thread_locals', None)
        if thread_data:
            return thread_data.request
    except Exception:
        pass
    
    return None


# Middleware to make request available to signals
class RequestMiddleware:
    """
    Middleware to store current request in thread-local storage for signal handlers.
    
    Add to MIDDLEWARE in settings.py:
    'applications.otheracademic.signals.RequestMiddleware'
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Store request in thread-local for signals to access
        if not hasattr(settings, '_thread_locals'):
            settings._thread_locals = type('obj', (object,), {})()
        settings._thread_locals.request = request
        
        response = self.get_response(request)
        
        # Clean up
        settings._thread_locals.request = None
        
        return response


"""
INTEGRATION INSTRUCTIONS:

1. Add middleware to settings.py MIDDLEWARE:
   
   MIDDLEWARE = [
       ...existing middleware...,
       'applications.otheracademic.signals.RequestMiddleware',
   ]

2. Import signals in apps.py:
   
   from django.apps import AppConfig
   from django.db.models.signals import post_migrate
   
   class OtheracademicConfig(AppConfig):
       name = 'applications.otheracademic'
       
       def ready(self):
           # Import signals to register them
           import applications.otheracademic.signals
           
           # Optionally, connect audit logging to all post_save
           # from applications.otheracademic import signals
           # post_migrate.connect(signals.initialize_data, sender=self)

3. Verify in logs:
   - Check APPLICATION LOGS for "Error in audit logging" messages
   - Query AuditLog model to verify entries are being created
   - Test with: python manage.py test applications.otheracademic.tests.AuditSignalTests

4. Performance tuning (if needed):
   - Disable audit logging for specific fields (add to should_audit_model)
   - Use Django's @transaction.atomic for batch operations
   - Consider using async_logging setting for high-traffic models
"""
