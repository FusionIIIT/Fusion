from django.contrib.auth import User

def create_file(uploader:ExtraInfo, uploader_designation:Designation, receiver:User, 
                receiver_designation: Designation, src_module:str, 
                src_object_id:str, file_extra_JSON:dict) -> int : 
''' this function is used to create a file object corresponding to any object of a module that needs to be tracked '''

def view_file(file_id:int) -> dict: 
''' This function returns all the details of a given file'''

def delete_file(file_id:int) -> bool: 
''' This function is used to delete a file from being tracked, all the tracking history is deleted as well and returns if the deletion was successful'''

def view_inbox(user:str, designation:str, src_module:str) -> dict: 
''' This function is used to get all the files in the inbox of a particular user and designation'''

def view_outbox(user:str, designation:str, src_module:str) -> dict: 
''' This function is used to get all the files in the outbox of a particular user and designation'''

def view_history(file_id:int) -> dict: 
''' This function is used to get the history of a particular file with the given file_id '''

def forward_file(file_id: int, receiver:str, receiver_designation:str, file_extra_JSON: dict) -> int: 
''' This function forwards the file and inserts a new tracking history into the file tracking table'''

def get_designations(user: str) -> list: 
''' This function is used to return a list of all the designation of the particular user'''

def get_user_object_from_username(username:str) -> User: 
    
def get_designation_object_from_designation_name(designation:str) -> Designation: 

