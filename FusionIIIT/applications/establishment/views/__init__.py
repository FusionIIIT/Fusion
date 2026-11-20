from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from .permissions import *
from .cpda import *
from .ltc import *
from .appraisal import *


@login_required(login_url='/accounts/login')
def establishment(request):
    """
        Renders ltc.
    """
    if not is_faculty(request) and not is_staff(request):
        return HttpResponseRedirect('/dashboard/')

    return ltc(request)


@login_required(login_url='/accounts/login')
def cpda(request):
    """
        Function handles generation and submission of CPDA form.
    """

    if not is_faculty(request) and not is_director(request):
        return HttpResponseRedirect('/dashboard/')

    response = {'director':False}
    # Check if establishment variables exist, if not create some fields or ask for them
    response.update(initial_checks(request))
    # Submission of CPDA Form
    if is_admin(request) and request.method == "POST":
        handle_cpda_admin(request)
        
    if is_eligible(request) and request.method == "POST":
        handle_cpda_eligible(request)

    # Generation of CPDA Form
    if is_admin(request):
        response.update(generate_cpda_admin_lists(request))

    if is_eligible(request):
        response.update(generate_cpda_eligible_lists(request))

    response.update({'cpda':True,'ltc':False,'appraisal':False,'leave':False}) 
    return render(request, 'establishment/hr1_form.html', response)


@login_required(login_url='/accounts/login')
def ltc(request):
    """
        Function handles generation and submission of LTC form.
    """

    if not is_faculty(request) and not is_staff(request):
        return HttpResponseRedirect('/dashboard/')

    response = {'director':False}
    # Check if establishment variables exist, if not create some fields or ask for them
    response.update(initial_checks(request))
    # Submission of LTC Form
    if is_admin(request) and request.method == "POST":
        handle_ltc_admin(request)

    if is_eligible(request) and request.method == "POST":
        handle_ltc_eligible(request)
    
    # Generation of LTC Form
    if is_admin(request):
        response.update(generate_ltc_admin_lists(request))

    if is_eligible(request):
        response.update(generate_ltc_eligible_lists(request))

    response.update({'cpda':False,'ltc':True,'appraisal':False,'leave':False})
    return render(request, 'establishment/hr1_form.html', response)


@login_required(login_url='/accounts/login')
def appraisal(request):
    """
        Function handles generation and submission of Appraisal form.
    """

    if not is_faculty(request) and not is_staff(request):
        return HttpResponseRedirect('/dashboard/')
        
    response = {'director':False}
    # Check if establishment variables exist, if not create some fields or ask for them
    app = None
    response.update(initial_checks(request))
    if is_eligible(request) and request.method == "POST":
        app = handle_appraisal(request)
    if is_eligible(request):
        response.update(generate_appraisal_lists(request))
    if is_eligible(request) and request.method == "POST" and 'filter_eis_details' in request.POST:
        response.update(update_appraisal_lists(request))
    # If user has designation "HOD"
    if is_hod(request):
        response.update(generate_appraisal_lists_hod(request))
    # If user has designation "Director"
    if is_director(request):
        response.update(generate_appraisal_lists_director(request))

    if is_admin(request):
        response.update(generate_appraisal_lists_admin(request))
    response.update({'cpda':False,'ltc':False,'appraisal':True,'leave':False})
    return render(request, 'establishment/hr1_form.html', response)
