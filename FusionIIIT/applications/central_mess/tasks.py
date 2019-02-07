import datetime
from celery.task.schedules import crontab
from celery import Celery
# from django_celery_beat.models import CrontabSchedule, PeriodicTask
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from datetime import datetime

app = Celery('tasks', broker='pyamqp://guest@localhost//')
# disable coordinated universal time. Runs on local time
app.conf.enable_utc = False

