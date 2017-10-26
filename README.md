# FusionIIIT

**FusionIIIT** is the automation of various functionalities, modules and tasks of/for PDPM Indian Institute of Information Technology, Design and Manufacturing, Jabalpur being developed in python3.5 and using django webframework version 1.11.4  

[![Build Status](https://api.travis-ci.org/3Peers/FusionIIIT.svg?branch=master)](https://travis-ci.org/3Peers/FusionIIIT)


## Requirements

Python 3.5  
Django==1.11.4+  
And additional requirements are in **requirements.txt**  

## How to run it?

  * Install virtualenv `$ sudo apt install python-virtualenv`  
  * Create a virtual environment `$ virtualenv env -p python3`  
  * Activate the env: `$ source env/bin/activate`  
  * Install the requirements: `$ pip install -r requirements.txt`  
  * Change directory to FusionIIIT `$ cd FusionIIIT`
  * Make migrations `$ python manage.py makemigrations`  
  * Migrate the changes to the database `$ python manage.py migrate`  
  * Run the server `$ python manage.py runserver`

## Diffrent modules include

  * Academic database management  
  * Academic workflows  
  * Finance and Accounting  
  * Placement Cell  
  * Mess management  
  * Gymkhana Activities  
  * Scholarship and Awards Portal  
  * Employee Management  
  * Course Management  
  * Complaint System  
  * File Tracking System  
  * Health Centre Mangement  
  * Visitor's Hostel Management  

## Contribution

  * Open an issue if you want to contribute for something that's not already in issues
  * Send a Pull Request anytime.
  * Before sending a pull request please make sure the changes you make are flake8 and isort compliant by using following commands  
  ```
  $ flake8 . --exclude manage.py,__pycache__,migrations --max-line-length=100
  $ isort
  ```
  * If there are errors resolve them, and then send a pull request.
