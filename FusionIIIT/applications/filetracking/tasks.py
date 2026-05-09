import json
import os
from datetime import datetime

from celery import shared_task
from django.conf import settings

from applications.filetracking.models import File, FileMovement, FileVersion


@shared_task
def backup_filetracking_snapshot():
    """Periodic backup snapshot for FT audit/version data."""
    backup_dir = os.path.join(settings.BASE_DIR, 'backups', 'filetracking')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    output_path = os.path.join(backup_dir, f'ft_backup_{timestamp}.json')

    files = list(
        File.objects.values(
            'id', 'file_number', 'subject', 'status', 'created_at',
            'created_by_id', 'current_holder_id', 'current_designation_id',
            'current_department_id', 'source_department_id',
        )
    )
    movements = list(
        FileMovement.objects.values(
            'id', 'file_id', 'action', 'sender_id', 'receiver_id', 'remarks', 'timestamp'
        )
    )
    versions = list(
        FileVersion.objects.values(
            'id', 'file_id', 'version_number', 'action', 'changed_by_id', 'comment', 'created_at'
        )
    )

    payload = {
        'generated_at_utc': timestamp,
        'files': files,
        'movements': movements,
        'versions': versions,
        'counts': {
            'files': len(files),
            'movements': len(movements),
            'versions': len(versions),
        },
    }

    with open(output_path, 'w', encoding='utf-8') as backup_file:
        json.dump(payload, backup_file, default=str)

    return {
        'path': output_path,
        'files': len(files),
        'movements': len(movements),
        'versions': len(versions),
    }
