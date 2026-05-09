from django.apps import AppConfig

class Hr2Config(AppConfig):
    name = 'applications.hr2'
    label = 'hr2'
    # For Django 3.1.5, no default_auto_field needed; it uses AutoField