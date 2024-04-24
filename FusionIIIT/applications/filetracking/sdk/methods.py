from amqp import NotFound
from django.contrib.auth.models import User
from applications.filetracking.models import Tracking, File
from applications.globals.models import Designation, HoldsDesignation, ExtraInfo
from applications.filetracking.api.serializers import FileSerializer, FileHeaderSerializer, TrackingSerializer
from django.core.exceptions import ValidationError
from typing import Any


def create_file(
        uploader: str,
        uploader_designation: str,
        receiver: str,
        receiver_designation: str,
        subject: str = "", 
        description: str = "", 
        src_module: str = "filetracking",
        src_object_id: str = "",
        file_extra_JSON: dict = {},
        attached_file: Any = None) -> int:
    '''
    This function is used to create a file object corresponding to any object of a module that needs to be tracked
    '''

    '''
    Functioning:
    create base file with params
    create tracking with params
    if both complete then return id of file
    else raise error

    also, delete file object if tracking isnt created
    '''
    uploader_user_obj = get_user_object_from_username(uploader)
    uploader_extrainfo_obj = get_ExtraInfo_object_from_username(uploader)
    uploader_designation_obj = Designation.objects.get(
        name=uploader_designation)
    receiver_obj = get_user_object_from_username(receiver)
    receiver_designation_obj = Designation.objects.get(
        name=receiver_designation)

    new_file = File.objects.create(
        uploader=uploader_extrainfo_obj,
        subject=subject, 
        description=description,
        designation=uploader_designation_obj,
        src_module=src_module,
        src_object_id=src_object_id,
        file_extra_JSON=file_extra_JSON,
    )
    

    if attached_file is not None: 
        new_file.upload_file.save(attached_file.name, attached_file, save=True)

    uploader_holdsdesignation_obj = HoldsDesignation.objects.get(
        user=uploader_user_obj, designation=uploader_designation_obj)

    new_tracking = Tracking.objects.create(
        file_id=new_file,
        current_id=uploader_extrainfo_obj,
        current_design=uploader_holdsdesignation_obj,
        receiver_id=receiver_obj,
        receive_design=receiver_designation_obj,
        tracking_extra_JSON=file_extra_JSON,
        remarks=f"File with id:{str(new_file.id)} created by {uploader} and sent to {receiver}"
        # upload_file = None, dont add file for first tracking
    )
    if new_tracking is None:
        new_file.delete()
        raise ValidationError('Tracking model data is incorrect')
    else:
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

# inbox and outbox could be sorted based on most recent linked tracking entry

def view_inbox(username: str, designation: str, src_module: str) -> list:
    '''
    This function is used to get all the files in the inbox of a particular user and designation
    '''
    user_designation = Designation.objects.get(name=designation)
    recipient_object = get_user_object_from_username(username)
    received_files_tracking = Tracking.objects.select_related('file_id').filter(
        receiver_id=recipient_object,
        receive_design=user_designation,
        file_id__src_module=src_module,
        file_id__is_read=False).order_by('-receive_date');
    received_files = [tracking.file_id for tracking in received_files_tracking]

    # remove duplicate file ids (from sending back and forth)
    received_files_unique = uniqueList(received_files)

    received_files_serialized = list(FileHeaderSerializer(
        received_files_unique, many=True).data)
    
    for file in received_files_serialized: 
        file['sent_by_user'] = get_last_file_sender(file['id']).username
        file['sent_by_designation'] = get_last_file_sender_designation(file['id']).name
    return received_files_serialized


def view_outbox(username: str, designation: str, src_module: str) -> list:
    '''
    This function is used to get all the files in the outbox of a particular user and designation
    '''
    user_designation = get_designation_obj_from_name(designation=designation)
    user_object = get_user_object_from_username(username)
    user_HoldsDesignation_object = HoldsDesignation.objects.get(
        user=user_object, designation=user_designation)
    sender_ExtraInfo_object = get_ExtraInfo_object_from_username(username)
    sent_files_tracking = Tracking.objects.select_related('file_id').filter(
        current_id=sender_ExtraInfo_object,
        current_design=user_HoldsDesignation_object,
        file_id__src_module=src_module,
        file_id__is_read=False).order_by('-receive_date')
    sent_files = [tracking.file_id for tracking in sent_files_tracking]

    # remove duplicate file ids (from sending back and forth)
    sent_files_unique = uniqueList(sent_files)

    sent_files_serialized = FileHeaderSerializer(sent_files_unique, many=True)
    return sent_files_serialized.data



def view_archived(username: str, designation: str, src_module: str) -> dict:
    '''
    This function is used to get all the files in the archive of a particular user and designation
    Archived file mean those which the user has ever interacted with, and are now finished or archived
    '''
    user_designation = Designation.objects.get(name=designation)
    user_object = get_user_object_from_username(username)
    received_archived_tracking = Tracking.objects.select_related('file_id').filter(
        receiver_id=user_object,
        receive_design=user_designation,
        file_id__src_module=src_module,
        file_id__is_read=True)
    
    user_HoldsDesignation_object = HoldsDesignation.objects.get(
        user=user_object, designation=user_designation)
    sender_ExtraInfo_object = get_ExtraInfo_object_from_username(username)
    sent_archived_tracking = Tracking.objects.select_related('file_id').filter(
        current_id=sender_ExtraInfo_object,
        current_design=user_HoldsDesignation_object,
        file_id__src_module=src_module,
        file_id__is_read=True).order_by('-receive_date')
    
    archived_tracking = received_archived_tracking | sent_archived_tracking
    archived_files = [tracking.file_id for tracking in archived_tracking]

    # remove duplicate file ids (from sending back and forth)
    archived_files_unique = uniqueList(archived_files)

    archived_files_serialized = FileHeaderSerializer(archived_files_unique, many=True)
    return archived_files_serialized.data



def archive_file(file_id: int) -> bool:
    '''
    This function is used to archive a file and returns true if the archiving was successful
    '''
    try:
        File.objects.filter(id=file_id).update(is_read=True)
        return True
    except File.DoesNotExist:
        return False

def unarchive_file(file_id: int) -> bool: 
    '''
    This functions is used to unarchive a file and returns true if the unarchiving was successful
    '''
    try: 
        File.objects.filter(id=file_id).update(is_read=False)
        return True
    except File.DoesNotExist:
        return False



def create_draft(
        uploader: str,
        uploader_designation: str,
        src_module: str = "filetracking",
        src_object_id: str = "",
        file_extra_JSON: dict = {},
        attached_file: Any = None) -> int:
    '''
    This function is used to create a draft file object corresponding to any object of a module that needs to be tracked
    It is similar to create_file but is not sent to anyone
    Later this file can be sent to someone by forward_file by using draft file_id
    '''
    uploader_extrainfo_obj = get_ExtraInfo_object_from_username(uploader)
    uploader_designation_obj = Designation.objects.get(
        name=uploader_designation)

    new_file = File.objects.create(
        uploader=uploader_extrainfo_obj,
        designation=uploader_designation_obj,
        src_module=src_module,
        src_object_id=src_object_id,
        file_extra_JSON=file_extra_JSON,
        upload_file=attached_file
    )
    return new_file.id


def view_drafts(username: str, designation: str, src_module: str) -> dict:
    '''
    This function is used to get all the files in the drafts (has not been sent) of a particular user and designation
    '''
    user_designation = Designation.objects.get(name=designation)
    user_ExtraInfo_object = get_ExtraInfo_object_from_username(username)
    draft_files = File.objects.filter(
        tracking__isnull=True, uploader=user_ExtraInfo_object, designation=user_designation, src_module=src_module).order_by('-upload_date')
    draft_files_serialized = FileHeaderSerializer(draft_files, many=True)
    return draft_files_serialized.data



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
        'remarks': remarks,
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
    Tracking_history = Tracking.objects.filter(
        file_id=file_id).order_by('-receive_date')
    Tracking_history_serialized = TrackingSerializer(
        Tracking_history, many=True)
    return Tracking_history_serialized.data


# HELPER FUNCTIONS

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

def get_last_file_sender(file_id: int) -> User: 
    '''
    This Function returns the last file sender,
    one who has last forwarded/sent the file
    '''
    latest_tracking = Tracking.objects.filter(
            file_id=file_id).order_by('-receive_date').first()
    latest_sender_extra_info = latest_tracking.current_id
    return latest_sender_extra_info.user

def get_last_file_sender_designation(file_id: int) -> Designation: 
    '''
    This Function returns the last file sender's Designation,
    one who has last forwarded/sent the file
    '''
    latest_tracking = Tracking.objects.filter(
            file_id=file_id).order_by('receive_date').first()
    latest_sender_holds_designation = latest_tracking.current_design
    return latest_sender_holds_designation.designation

def get_designations(username: str) -> list:
    '''
    This function is used to return a list of all the designation names of a particular user
    '''
    user = User.objects.get(username=username)
    designations_held = HoldsDesignation.objects.filter(user=user)
    designation_name = [hold_designation.designation.name for hold_designation in designations_held]
    return designation_name


def get_user_object_from_username(username: str) -> User:
    user = User.objects.get(username=username)
    return user

def get_ExtraInfo_object_from_username(username: str) -> ExtraInfo:
    user = User.objects.get(username=username)
    extrainfo = ExtraInfo.objects.get(user=user)
    return extrainfo

def uniqueList(l: list) -> list:
    '''
    This function is used to return a list with unique elements
    O(n) time and space
    '''
    seen = set()
    unique_list = []
    for item in l:
        if item not in seen:
            unique_list.append(item)
            seen.add(item)
    return unique_list

def add_uploader_department_to_files_list(files: list) -> list:
    '''
    This function is used to add the department of the uploader to the file
    '''
    for file in files:
        uploader_Extrainfo = file['uploader']
        if uploader_Extrainfo.department is None:
            # for files created by staff or users that dont have department
            file['uploader_department'] = 'FTS'
        else:
            file['uploader_department'] = (
                str(uploader_Extrainfo.department)).split(': ')[1]

    return files

def get_designation_obj_from_name(designation: str) -> Designation:
    des = Designation.objects.get(name = designation)
    return des 

def get_HoldsDesignation_obj(username: str, designation:str) -> HoldsDesignation:
    user_object = get_user_object_from_username(username=username)
    user_designation = get_designation_obj_from_name(designation=designation)
    obj = HoldsDesignation.objects.get(
        user=user_object, designation=user_designation)
    return obj

def get_last_recv_tracking_for_user(file_id: int, username: str, designation: str)-> Tracking:
    '''
    This returns the last tracking where username+designation recieved file_id
    '''

    recv_user_obj = get_user_object_from_username(username)
    recv_design_obj = get_designation_obj_from_name(designation)

    last_tracking = Tracking.objects.filter(file_id=file_id, 
                                            receiver_id=recv_user_obj, 
                                            receive_design=recv_design_obj).order_by('-receive_date')[0]
    return last_tracking

def get_last_forw_tracking_for_user(file_id: int, username: str, designation: str) -> Tracking:
    '''
    Returns the last tracking where the specified user forwarded the file.
    '''

    # Get user and designation objects
    sender_user_obj = get_ExtraInfo_object_from_username(username)
    sender_designation_obj = get_HoldsDesignation_obj(username=username, designation=designation)

    # Filter Tracking objects by file_id, sender_id, and sender_designation
    last_tracking = Tracking.objects.filter(file_id=file_id,
                                            current_id=sender_user_obj,
                                            current_design=sender_designation_obj).order_by('-forward_date').first()
    return last_tracking

def get_extra_info_object_from_id(id: int):
    return ExtraInfo.objects.get(id=id)
