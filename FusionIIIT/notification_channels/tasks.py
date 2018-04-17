from __future__ import absolute_import, unicode_literals
from channels import Group
import celery
import json


@celery.task()
def notify(notif):
    notif_type = "New Notification"
    notif_str = notif.__str__()
    if notif.notif_type:
        notif_type = notif.notif_type
    data = {
        "title": notif_type,
        "message": notif_str,
        "url": notif.reference_url,
    }
    Group(notif.recipient.username).send({
            "text": json.dumps(data),
        })