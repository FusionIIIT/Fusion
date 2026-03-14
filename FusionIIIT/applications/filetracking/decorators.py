from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, HoldsDesignation
from .sdk.methods import get_HoldsDesignation_obj


def user_check(request):
    """
    This function is used to check if the user is a student or not.
    Its return type is bool.
    @param:
        request - contains metadata about the requested page
        
    @Variables:
        current_user - get user from request
        user_details - extract details of the user from the database
        desig_id - check for designation
        student - designation for a student
        final_user - final designation of the request(our user)
    """
    try:
        current_user = get_object_or_404(User, username=request.user.username)
        user_details = ExtraInfo.objects.select_related('user','department').get(user=request.user)
        des = HoldsDesignation.objects.all().select_related().filter(user=request.user).first()
        if str(des.designation) == "student":
            return True
        else:
            return False
    except Exception as e:
        return False

def user_is_student(view_func): 
    def _wrapped_view(request, *args, **kwargs): 
        if user_check(request): 
            return render(request, 'filetracking/fileTrackingNotAllowed.html')
        else:
            return view_func(request, *args, **kwargs)  
    return _wrapped_view  

def dropdown_designation_valid(view_func):
    def _wrapped_view(request, *args, **kwargs):
        designation_name = request.session.get('currentDesignationSelected', 'default_value') #from dropdown
        username = request.user
        try:
            designation_id = get_HoldsDesignation_obj(
            username, designation_name).id 
        except:
            return render(request, 'filetracking/invalid_designation.html', {'curr_des' : designation_name})
        else:
            return view_func(request, *args, **kwargs)  
    return _wrapped_view  
