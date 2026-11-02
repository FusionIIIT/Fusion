from django.contrib.auth.signals import user_logged_in
from django.db.models import Q
from django.dispatch import receiver
from django.utils import timezone

from applications.globals.models import ExtraInfo, HoldsDesignation, ModuleAccess


def user_logged_in_middleware(get_response):
    @receiver(user_logged_in)
    def user_logged_in_handler(sender, user, request, **kwargs):
        if 'function_executed' in request.session or not user.is_authenticated:
            return

        try:
            extra_info = user.extrainfo
        except ExtraInfo.DoesNotExist:
            extra_info = None

        now = timezone.now()
        assignments = (HoldsDesignation.objects
                       .select_related('designation')
                       .filter(working=user)
                       .filter(Q(start_time__isnull=True) | Q(start_time__lte=now))
                       .filter(Q(end_time__isnull=True) | Q(end_time__gt=now)))
        user_type = extra_info.user_type if extra_info else None
        designations = [user_type] if user_type == 'student' else []

        for assignment in assignments:
            role_name = str(assignment.designation)
            if role_name != user_type:
                designations.append(role_name)
        if not designations and user_type:
            designations.append(user_type)

        selected = designations[0] if designations else None
        request.session['currentDesignationSelected'] = selected or 'default_value'
        request.session['allDesignations'] = designations

        access_rights = {}
        if selected:
            module_access = ModuleAccess.objects.filter(designation=selected).first()
            if module_access:
                field_names = [
                    field.name for field in ModuleAccess._meta.get_fields()
                    if field.name not in ['id', 'designation']
                ]
                access_rights = {
                    field_name: getattr(module_access, field_name)
                    for field_name in field_names
                }
        request.session['moduleAccessRights'] = access_rights
        request.session['function_executed'] = True

    def middleware(request):
        if request.user.is_authenticated:
            user_logged_in_handler(request.user, request.user, request)
        return get_response(request)

    return middleware
