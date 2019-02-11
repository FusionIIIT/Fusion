import subprocess
from datetime import datetime

from django.conf import settings


def semester(roll):
    month = datetime.now().month
    sem = 0
    if month >= 8 and month <= 12:
        sem = 1
    semester = (datetime.now().year-int(roll))*2+sem
    return semester


def create_thumbnail(course, row, name, ext, attach_str, thumb_time, thumb_size):
    filepath = settings.MEDIA_ROOT + '/online_cms/' + course.course_id + '/vid/' + name + ext
    filename = settings.MEDIA_ROOT + '/online_cms/' + course.course_id + '/vid/'
    filename = filename + name.replace(' ', '-') + '-' + attach_str + '.png'
    process = 'ffmpeg -y -i ' + filepath + ' -vframes ' + str(1) + ' -an -s '
    process = process + thumb_size + ' -ss ' + str(thumb_time) + ' ' + filename
    subprocess.call(process, shell=True)
