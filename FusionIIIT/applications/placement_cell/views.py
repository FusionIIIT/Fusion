from cgi import escape
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import get_template
from xhtml2pdf import pisa

from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo

from .models import (Achievement, Course, Education, Experience, Has, Project,
                     Publication, StudentPlacement)


@login_required
def placement(request):
    context = {}

    return render(request, "placementModule/placement.html", context)


@login_required
def profile(request, username):
    user = get_object_or_404(User, Q(username=username))
    profile = get_object_or_404(ExtraInfo, Q(user=user))
    student = get_object_or_404(Student, Q(id=profile.id))
    studentplacement = get_object_or_404(StudentPlacement, Q(unique_id=student))
    skills = Has.objects.filter(Q(unique_id=student))
    education = Education.objects.filter(Q(unique_id=student))
    course = Course.objects.filter(Q(unique_id=student))
    experience = Experience.objects.filter(Q(unique_id=student))
    project = Project.objects.filter(Q(unique_id=student))
    achievement = Achievement.objects.filter(Q(unique_id=student))
    publication = Publication.objects.filter(Q(unique_id=student))
    context = {'user': user, 'profile': profile, 'student': studentplacement, 'skills': skills,
               'educations': education, 'courses': course, 'experiences': experience,
               'projects': project, 'achievements': achievement, 'publications': publication}
    return render(request, "placementModule/placement.html", context)


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))


def cv(request, username):
    # Retrieve data or whatever you need
    user = get_object_or_404(User, Q(username=username))
    profile = get_object_or_404(ExtraInfo, Q(user=user))
    student = get_object_or_404(Student, Q(id=profile.id))
    studentplacement = get_object_or_404(StudentPlacement, Q(unique_id=student))
    skills = Has.objects.filter(Q(unique_id=student))
    education = Education.objects.filter(Q(unique_id=student))
    course = Course.objects.filter(Q(unique_id=student))
    experience = Experience.objects.filter(Q(unique_id=student))
    project = Project.objects.filter(Q(unique_id=student))
    achievement = Achievement.objects.filter(Q(unique_id=student))
    publication = Publication.objects.filter(Q(unique_id=student))
    return render_to_pdf('placementModule/placement.html', {'pagesize': 'A4', 'user': user,
                                                            'profile': profile,
                                                            'student': studentplacement,
                                                            'skills': skills,
                                                            'educations': education,
                                                            'courses': course,
                                                            'experiences': experience,
                                                            'projects': project,
                                                            'achievements': achievement,
                                                            'publications': publication})
