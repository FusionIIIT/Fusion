from hashlib import file_digest
from django.contrib.auth.models import User
from applications.filetracking.models import Tracking, File
from applications.globals.models import Designation, HoldsDesignation, ExtraInfo
from applications.filetracking.api.serializers import FileSerializer, FileHeaderSerializer, TrackingSerializer
from django.core.exceptions import ValidationError
from typing import Any


def create_file(
        uploader: ExtraInfo,
        uploader_designation: Designation,
        receiver: User,
        receiver_designation: Designation,
        src_module: str,
        src_object_id: str,
        file_extra_JSON: dict,
        upload_file) -> int:
    '''
    This function is used to create a file object corresponding to any object of a module that needs to be tracked
    '''
    new_file = File.objects.create(
        uploader=uploader,
        designation=uploader_designation,
        src_module=src_module,
        src_object_id=src_object_id,
        file_extra_JSON=file_extra_JSON,
        # upload_file=upload_file TESTING without file
    )
    # Tracking.objects.create(
    #     file_id=new_file.id,
    #     current_id=uploader,
    #     current_design=uploader_designation,
    #     receiver_id=receiver,
    #     receive_design=receiver_designation,
    #     tracking_extra_JSON=file_extra_JSON,
    #     # upload_file = upload_file TESTING without file
    # )
    return new_file.id


def view_file(file_id: int) -> dict:
    '''
    This function returns all the details of a given file
    '''
    try:
        requested_file = File.objects.get(id=file_id)
        serializer = FileSerializer(requested_file)
        file_details = serializer.data
        return file_details
    except File.DoesNotExist:
        raise NotFound("File Not Found with provided ID")


def delete_file(file_id: int) -> bool:
    '''
    This function is used to delete a file from being tracked, all the tracking history is deleted as well and returns true if the deletion was successful
    '''
    try:
        File.objects.filter(id=file_id).delete()
        return True
    except File.DoesNotExist:
        return False


def view_inbox(user: str, designation: str, src_module: str) -> dict:
    '''
    This function is used to get all the files in the inbox of a particular user and designation
    '''
    # TODO: currently this does not return a value of sent by
    user_designation = Designation.objects.get(name=designation)
    recipient_object = get_user_object_from_username(user)
    received_files_tracking = Tracking.objects.select_related('file_id').filter(
        receiver_id=recipient_object,
        receive_design=user_designation,
        file_id__src_module=src_module)
    received_files = [tracking.file_id for tracking in received_files_tracking]

    received_files_serialized = FileHeaderSerializer(received_files, many=True)
    return received_files_serialized.data


def view_outbox(username: str, designation: str, src_module: str) -> dict:
    '''
    This function is used to get all the files in the outbox of a particular user and designation
    '''
    user_designation = Designation.objects.get(name=designation)
    user_object = get_user_object_from_username(username)

    # holds designation is used instead of Designation due to legacy code
    # having it and breaking changes cannot be introduced
    user_HoldsDesignation_object = HoldsDesignation.objects.get(
        user=user_object, designation=user_designation)
    sender_ExtraInfo_object = get_ExtraInfo_object_from_username(username)
    sent_files_tracking = Tracking.objects.select_related('file_id').filter(
        current_id=sender_ExtraInfo_object,
        current_design=user_HoldsDesignation_object,
        file_id__src_module=src_module)
    sent_files = [tracking.file_id for tracking in sent_files_tracking]

    sent_files_serialized = FileHeaderSerializer(sent_files, many=True)
    return sent_files_serialized.data


def get_current_file_owner(file_id: int) -> User:
    '''
    This functions returns the current owner of the file.
    The current owner is the latest recipient of the file
    '''
    latest_tracking = Tracking.objects.filter(
        file_id=file_id).order_by('-receive_date').first()
    latest_recipient = latest_tracking.receiver_id
    return latest_recipient


def get_current_file_owner_designation(file_id: int) -> Designation:
    '''
    This function returns the designation of the current owner of the file.
    The current owner is the latest recipient of the file
    '''
    latest_tracking = Tracking.objects.filter(
        file_id=file_id).order_by('-receive_date').first()
    latest_recipient_designation = latest_tracking.receive_design
    return latest_recipient_designation


def forward_file(
        file_id: int,
        receiver: str,
        receiver_designation: str,
        file_extra_JSON: dict,
        remarks: str = "",
        file_attachment: Any = None) -> int:
    '''
    This function forwards the file and inserts a new tracking history into the file tracking table
    Note that only the current owner(with appropriate designation) of the file has the ability to forward files
    '''
    # HoldsDesignation and ExtraInfo object are used instead
    # of Designation and User object because of the legacy code being that way

    current_owner = get_current_file_owner(file_id)
    current_owner_designation = get_current_file_owner_designation(file_id)
    current_owner_extra_info = ExtraInfo.objects.get(user=current_owner)
    current_owner_holds_designation = HoldsDesignation.objects.get(
        user=current_owner, designation=current_owner_designation)
    receiver_obj = User.objects.get(username=receiver)
    receiver_designation_obj = Designation.objects.get(
        name=receiver_designation)
    tracking_data = {
        'file_id': file_id,
        'current_id': current_owner_extra_info.id,
        'current_design': current_owner_holds_designation.id,
        'receiver_id': receiver_obj.id,
        'receive_design': receiver_designation_obj.id,
        'tracking_extra_JSON': file_extra_JSON,
    }
    if file_attachment is not None:
        tracking_data['upload_file'] = file_attachment

    tracking_entry = TrackingSerializer(data=tracking_data)
    if tracking_entry.is_valid():
        tracking_entry.save()
        return tracking_entry.instance.id
    else:
        raise ValidationError('forward data is incomplete')


def view_history(file_id: int) -> dict:
    '''
    This function is used to get the history of a particular file with the given file_id
    '''
    pass


def get_designations(username: str) -> list:
    '''
    This function is used to return a list of all the designation names of a particular user
    '''
    user = User.objects.get(username=username)
    designations_held = HoldsDesignation.objects.filter(user=user)
    designation_name = [designation.name for designation in designations_held]


def get_user_object_from_username(username: str) -> User:
    user = User.objects.get(username=username)
    return user


def get_ExtraInfo_object_from_username(username: str) -> ExtraInfo:
    user = User.objects.get(username=username)
    extrainfo = ExtraInfo.objects.get(user=user)
    return extrainfo
