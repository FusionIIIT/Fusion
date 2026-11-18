"""Fusion URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

import notifications.urls
import debug_toolbar
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from applications.globals.views import RateLimitedPasswordResetView


def serve_media(request, path, document_root=None):
    """Hand an uploaded file over as a download, never as a page.

    Uploads share this origin with the portal and with every module framed
    inside it, so anything served inline here runs as the application: an
    uploaded .html or .svg would execute in the app's own origin and could read
    the API token the client keeps. Forcing a download and refusing content-type
    sniffing takes that away whatever the file claims to be.
    """
    from django.views.static import serve

    response = serve(request, path, document_root=document_root)
    response['Content-Disposition'] = 'attachment'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Security-Policy'] = "default-src 'none'; sandbox"
    return response


urlpatterns = [
    url(r'^', include('applications.globals.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^academic-procedures/', include('applications.academic_procedures.urls')),
    url(r'^aims/', include('applications.academic_information.urls')),
    url(r'^notifications/', include('applications.notifications_extension.urls')),
    url(r'^programme_curriculum/',include('applications.programme_curriculum.urls')),
    url(r'^__debug__/', include(debug_toolbar.urls)),
    url(r'^accounts/', include('allauth.urls')),


    url(r'^eis/', include('applications.eis.urls')),
    url(r'^filetracking/', include('applications.filetracking.urls')),
    url(r'^spacs/', include('applications.scholarships.urls')),
    url(r'^examination/', include('applications.examination.urls')),

    path(
        'password-reset/',
        RateLimitedPasswordResetView.as_view(
            template_name='registration/password_reset_form.html',
        ),
        name='reset_password',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        ),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
        ),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ),
        name='password_reset_complete',
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT,
           view=serve_media)
