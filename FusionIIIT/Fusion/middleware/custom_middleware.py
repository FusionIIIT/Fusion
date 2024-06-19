# custom_middleware.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from applications.globals.models import (ExtraInfo, Feedback, HoldsDesignation,
                                         Issue, IssueImage, DepartmentInfo,ModuleAccess)
from django.shortcuts import get_object_or_404, redirect, render

def user_logged_in_middleware(get_response):
    @receiver(user_logged_in)
    def user_logged_in_handler(sender, user, request, **kwargs):
        if 'function_executed' not in request.session:
            # Run the function only if the flag is not set
            # Assuming user is a model with the desired data field, retrieve the data
            # For example, if your User model has a field named 'custom_field', you can access it like:
            if user.is_authenticated:
                desig = list(HoldsDesignation.objects.select_related('user','working','designation').all().filter(working = request.user).values_list('designation'))
                print(desig)
                b = [i for sub in desig for i in sub]
                design = HoldsDesignation.objects.select_related('user','designation').filter(working=request.user)

                designation=[]
                if str(user.extrainfo.user_type) == "student":
                    designation.append(str(user.extrainfo.user_type))


                for i in design:
                    if str(i.designation) != str(user.extrainfo.user_type):
                        print('-------')
                        print(i.designation)
                        print(user.extrainfo.user_type)
                        print('')
                        designation.append(str(i.designation))

                for i in designation:
                    print(i)

                request.session['currentDesignationSelected'] = designation[0]
                request.session['allDesignations'] = designation 
                first_designation = designation[0]
                module_access = ModuleAccess.objects.filter(designation=first_designation).first()
                
                if module_access:
                    access_rights = {}
    
                    field_names = [field.name for field in ModuleAccess._meta.get_fields() if field.name not in ['id', 'designation']]
    
                    for field_name in field_names:
                        access_rights[field_name] = getattr(module_access, field_name)
    
                request.session['moduleAccessRights'] = access_rights           
                print("logged iN")
                
            # Set the flag in the session to indicate that the function has bee+n executed
            request.session['function_executed'] = True
        
    def middleware(request):
        if request.user.is_authenticated:
            user_logged_in_handler(request.user, request.user, request)
        response = get_response(request)
        return response
    
    return middleware 