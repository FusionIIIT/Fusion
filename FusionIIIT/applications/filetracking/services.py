from .models import File, Tracking
from . import selectors

def validate_file_size(upload_file):
    if upload_file and upload_file.size / 1000 > 10240:
        return False
    return True

def create_file_service(uploader, subject, description, designation, upload_file, extraJSON=None):
    return File.objects.create(
        uploader=uploader,
        subject=subject,
        description=description,
        designation=designation,
        upload_file=upload_file,
        file_extra_JSON=extraJSON
    )

def create_tracking_service(file, current_id, current_design, receive_design, receiver_id, remarks, upload_file):
    return Tracking.objects.create(
        file_id=file,
        current_id=current_id,
        current_design=current_design,
        receive_design=receive_design,
        receiver_id=receiver_id,
        remarks=remarks,
        upload_file=upload_file,
    )