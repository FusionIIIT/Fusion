# FusionIIIT

**FusionIIIT** is the automation of various functionalities, modules and tasks of/for **PDPM Indian Institute of Information Technology, Design and Manufacturing, Jabalpur** being developed in `python3.6` and using `Django` Webframework version `1.11`

## System Requirements

* **Ubuntu `18.04`** (or newer) *OR* **WSL** for **Windows 10** \(Follow the guide below\) :  
    [Windows Subsystem for Linux Installation Guide for Windows 10](https://docs.microsoft.com/en-us/windows/wsl/install-win10)
* **Windows `7/8/8.1/10`**

## Software Requirements

* Python `3.6`
* PostgreSQL `10.10`
* Git

## How to get started

* on **Ubuntu**:
  * Install the required packages using the following command :  
    `sudo apt install postgresql postgresql-contrib python3.6-dev python-virtualenv build-essential git`

* on **Windows**:
  * Get Python 3.6.8 from [here](https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe) for AMD64/x64 or [here](https://www.python.org/ftp/python/3.6.8/python-3.6.8.exe) for x86
  * Git from [here](https://git-scm.com/download/win)
  * Install both using the downloaded `exe` files.  
  
  **Important:** Make sure to check the box that says **Add Python 3.x to PATH** to ensure that the interpreter will be placed in your execution path.

### Downloading the Code

* Go to (<https://github.com/salarx/Fusion>) and click on **Fork**
* You will be redirected to *your* fork, `https://github.com/<your_user_name>/Fusion`
* Open the terminal, change to the directory where you want to clone the **Fusion** repository
* Clone your repository using `git clone https://github.com/<your_user_name>/Fusion`
* Enter the cloned directory using `cd Fusion/`

### Setting up environment

* Create a virtual environment  
  * on **Ubuntu**: `virtualenv env -p python3.6`  
  * on **Windows Powershell**: `virtualenv env`
* Activate the *env*
  * on **Ubuntu**: `source env/bin/activate`  
  * on **Windows Powershell**: `. .\env\scripts\activate`  
* Install the requirements: `pip install -r requirements.txt`
* Replace the files
  * on **Ubuntu**: `env/lib/python3.6/site-packages/notifications`
  * on **Windows**: `env/lib/site-packages/notifications`  
with the files in **notif_package_mod** folder inside the current directory

### Running server

* Change directory to **FusionIIIT** `cd FusionIIIT`
* Make *migrations* `python manage.py makemigrations`  
* Migrate the changes to the database `$ python manage.py migrate`  
* Run the server `python manage.py runserver`

## Working with Code \(Method 1\)

### Setting upstream

* `git remote add upstream https://github.com/salarx/Fusion`
  * Adds the remote repository (the repository you forked from) so that changes can be pulled from/pushed to it

### Switching branch

* `git checkout -b <module-name>`
  * Creates a new branch `<module-name>` in your repository
* `git checkout <module-name>`
  * Switches to the branch you just created

### Committing

* `git add .`
  * Adds the changes to the staging area
* `git commit`
  * Commits the staged changes

### Syncing

#### Pulling

* `git pull upstream master`
  * Pulls the changes from the *upstream* master branch

#### Pushing

* `git push -u origin <module-name>`
  * Pushes the changes to your repository **\(First time only\)**; using `git push` is sufficient later on
* Go to `https://github.com/<your_user_name>/Fusion/tree/<module-name>` and create pull request

## Working with Code \(Alternative\)

* **(Recommended)** Use [Visual Studio Code](https://code.visualstudio.com/) as a text editor. Go through the [Tutorial](https://code.visualstudio.com/docs/python/python-tutorial) for getting started with **Visual Studio Code for Python**.  
**Note** : Use the following guide if using **WSL** for Development  
    (<https://code.visualstudio.com/docs/remote/wsl>)
* Use the inbuilt **Source Control** feature for checking out, committing, pushing, pulling changes. You can also use [Github Desktop](https://desktop.github.com/) **_\(Windows/Mac only\)_**.  
* Refer to below link for best practices regarding commit messages :  
    (<https://gist.github.com/robertpainsi/b632364184e70900af4ab688decf6f53>)

## Different modules included

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
