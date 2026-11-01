import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage


def private_storage():
    # Kept outside MEDIA_ROOT: every download must pass course/ownership checks.
    root = getattr(settings, 'LMS_PRIVATE_ROOT', Path(settings.MEDIA_ROOT).parent / 'lms-private')
    return FileSystemStorage(location=str(root), base_url='/not-public-lms-files/')


def upload_key(instance, filename):
    return uuid.uuid4().hex
