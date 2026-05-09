# # import datetime
# from celery.task.schedules import crontab
# from celery.schedules import crontab
# from celery import Celery
# from django_celery_beat.models import CrontabSchedule, PeriodicTask
# # from celery.decorators import task
# # from celery.utils.log import get_task_logger
# # from datetime import datetime
# from celery.task.schedules import crontab
# from celery.decorators import periodic_task
#
#
# app = Celery('tasks', broker='pyamqp://guest@localhost//')
# # disable coordinated universal time. Runs on local time
# app.conf.enable_utc = False
#
#
# @periodic_task(run_every=(crontab(minute='*/1')), name="some_task", ignore_result=True)
# def some_task():
#     print("5")
