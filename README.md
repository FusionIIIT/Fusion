# FusionIIIT

**FusionIIIT** is the automation of various functionalities, modules and tasks of/for PDPM Indian Institute of Information Technology, Design and Manufacturing, Jabalpur being developed in python3.6 and using django webframework version 1.11.4  

## Requirements

Python 3.6  
And additional requirements are in **requirements.txt** and will be installed through the below steps

## How to get started

* Download and install **python 3.6** and **git**
### Download
* Go to `https://github.com/FusionIIIT/Fusion` and click on `Fork`
* You will be redirected to *your* fork, `https://github.com/<yourname>/Fusion`
* Clone using `$ git clone https://github.com/<yourname>/Fusion`
### Run
* Install virtualenv  
    - on Ubuntu: `$ sudo apt install python-virtualenv`  
    - on Windows Powershell `$ pip install virtualenv`  
* Create a virtual environment  
    - on Ubuntu: `$ virtualenv env -p python3.6`  
    - on Windows: `$ virtualenv env`  
* Activate the env:
    - on Ubuntu: `$ source env/bin/activate`  
    - on Windows: `$ ./env/scripts/activate`  
* Install the requirements: `$ pip install -r requirements.txt`
* Change directory to FusionIIIT `$ cd FusionIIIT`
* Make migrations `$ python manage.py makemigrations`  
* Migrate the changes to the database `$ python manage.py migrate`  
* Run the server `$ python manage.py runserver`
### git setup
* `$ git remote add upstream https://github.com/FusionIIIT/Fusion`
* `$ git checkout -b <module-name>`

## How to contribute
* Start working on your module in the branch you created in the previous step
* Run and resolve any issues that you may get with:
  ```
  $ flake8 . --exclude manage.py,__pycache__,migrations --max-line-length=100
  $ isort
  ```  
  You may use autopep8 to automatically resolve them. https://pypi.org/project/autopep8/#usage
* After making changes  
    - `$ git add .`  
    - `$ git commit` then enter the commit message.
        Refer to below link for best practices regarding commit messages
        Follow: https://gist.github.com/robertpainsi/b632364184e70900af4ab688decf6f53  
### Syncing with Fork:
* `$ git fetch upstream`
* `$ git merge upstream/master`
* `$ git push origin <module-name>`
* Open the link given after the previous command or go to `https://github.com/FusionIIIT/Fusion` and create pull request


## Different modules include

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
* Leave Module  

