from django.contrib.auth import User
from 

def create_file(uploader:User, uploader_designation:Designation, receiver:User, 
                receiver_designation: Designation, src_module:str, 
                src_object_id:str, file_extra_JSON:dict) -> int : 
''' this function is used to create a file object corresponding to any object of a module that needs to be tracked '''

def view_file(file_id:int) -> dict: 
''' This function returns all the details of a given file'''

def delete_file(file_id:int) -> None: 
''' This function is used to delete a file from being tracked, all the tracking history is deleted as well'''

def view_inbox(user:User, designation:Designation) -> dict: 
''' This function is used to get all the files in the inbox of a particular user and designation'''

def view_outbox(user:User, designation:Designation) -> dict: 
''' This function is used to get all the files in the outbox of a particular user and designation'''

def view_history(file_id:int) -> dict: 
''' This function is used to get the history of a particular file with the given file_id '''

def forward_file(file_id: int, receiver: User, receiver_designation: Designation) -> int: 
''' This function forwards the file and inserts a new tracking history into the file tracking table'''

def get_designation(user: User) -> list: 
''' This function is used to return a list of all the designation of the particular user'''
