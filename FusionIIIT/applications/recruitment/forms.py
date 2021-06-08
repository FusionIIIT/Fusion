from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class RegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = [ "email", "username", "first_name", "last_name", "password1", "password2" ]

