from applications.filetracking.models import File, FileMovement, FileType, DraftFile
from applications.globals.models import ExtraInfo


def get_user_profile(user):
    return ExtraInfo.objects.filter(user=user).first()


def get_files_created_by_user(user):
    return File.objects.filter(created_by__user=user).select_related(
        'file_type',
        'created_by',
        'source_department',
        'current_holder',
        'current_designation',
        'current_department',
    ).order_by('-created_at')


def get_file_with_related(file_id):
    return File.objects.select_related(
        'file_type',
        'created_by',
        'source_department',
        'current_holder',
        'current_designation',
        'current_department',
    ).filter(id=file_id).first()


def get_file_history_movements(file):
    return FileMovement.objects.filter(file=file).select_related(
        'sender',
        'receiver',
        'sender_designation',
        'receiver_designation',
        'sender_department',
        'receiver_department',
    ).order_by('timestamp')


def get_active_drafts_for_user(user):
    profile = get_user_profile(user)
    if not profile:
        return DraftFile.objects.none()
    return DraftFile.objects.filter(created_by=profile).order_by('-updated_at')


def get_active_file_types():
    return FileType.objects.filter(is_active=True).order_by('name')
