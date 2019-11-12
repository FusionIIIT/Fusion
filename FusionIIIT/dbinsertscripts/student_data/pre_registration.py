import xlrd
import sys
import os
import django
sys.path.append(r'/home/fusion/Fusion/FusionIIIT/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'Fusion.settings'
django.setup()


from django.contrib.auth.models import User
from applications.academic_information.models import Student,Course, Curriculum
from applications.globals.models import ExtraInfo

