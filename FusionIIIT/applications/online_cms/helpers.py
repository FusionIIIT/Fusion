from datetime import datetime


def semester(roll):
    month = datetime.now().month
    sem = 0
    if month >= 8 and month <= 12:
        sem = 1
    semester = (datetime.now().year-int(roll))*2+sem
    return semester
