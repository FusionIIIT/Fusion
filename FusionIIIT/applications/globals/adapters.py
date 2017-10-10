from allauth.account.utils import perform_login
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.contrib.auth.models import User
# from django.http import HttpResponse
# from django.contrib.auth import authenticate
from django.shortcuts import redirect, render_to_response


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        user = sociallogin.user
        email = user.email
        if not email.split('@')[1] == 'iiitdmj.ac.in':
            messages.error(request, 'Use iiitdmj mail to sign in to this account !')
            raise ImmediateHttpResponse(render_to_response('account/exception.html'))

        else:
            if user.id:
                return
            try:
                # if user exists, connect the account to the existing account and login
                u = User.objects.get(email=email)
                sociallogin.state['process'] = 'connect'
                # authenticate(username=u.username, password=u.password)
                perform_login(request, u, 'none')
                return redirect('/')
            except User.DoesNotExist:
                exception_string = "Seems Like you don't \
                                    have an account here! Contact CC admin for your account."
                messages.error(request, exception_string)
                raise ImmediateHttpResponse(render_to_response('account/exception_no_account.html'))
