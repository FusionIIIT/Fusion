from .models import File, Tracking
from django.contrib.auth.models import User

def get_file_by_id(file_id):
    return File.objects.filter(id=file_id).first()

def get_user_by_username(username):
    return User.objects.filter(username=username).first()

def get_all_files():
    return File.objects.all()

def get_tracking_by_file(file):
    return Tracking.objects.filter(file_id=file)

def get_designation_by_id(model, id):
    return model.objects.filter(id=id).first()