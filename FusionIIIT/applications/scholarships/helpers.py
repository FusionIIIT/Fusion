import subprocess
from datetime import datetime

from django.conf import settings


def getBatch(roll):
    batch = "20"
    if(str(roll)[2].isdigit()):
        return str(roll)[0:4]
        
    else:
        batch+=str(roll)[0:2]
    return batch