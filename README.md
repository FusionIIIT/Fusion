# FusionIIIT

**FusionIIIT** is the automation of various functionalities, modules and tasks of/for **PDPM Indian Institute of Information Technology, Design and Manufacturing, Jabalpur** being developed in `python3.8` and using `Django` Webframework.

## System Configuration

* Ubuntu `20.04` **(Recommended)**
* *OR* WSL for Windows `10` \(Follow the guide below\) :  
    [Windows Subsystem for Linux Installation Guide for Windows 10](https://docs.microsoft.com/en-us/windows/wsl/install-win10)
* *OR* Windows `7/8/8.1/10`

## Software Requirements

* Python `3.8`
* Git

## Contributing Guidelines

For contributing to this repository, you have to follow the guidelines given in [CONTRIBUTING.md](./CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) for smooth workflow of contributions and changes inside repository.

## How to get started

* on **Ubuntu**:

    ```sh
    // Install the required packages using the following command:
    
    sudo apt install python3-pip python3-dev python3-venv libpq-dev build-essential git
    sudo -H pip3 install --upgrade pip
    ```

* on **Windows**:

  * Get Python 3.8 from [here](https://www.python.org/ftp/python/3.8.3/python-3.8.3-amd64.exe) for AMD64/x64 or [here](https://www.python.org/ftp/python/3.8.3/python-3.8.3.exe) for x86
  * Git from [here](https://git-scm.com/download/win)
  * Install both using the downloaded `exe` files   
  **Important:** Make sure to check the box that says **Add Python 3.x to PATH** to ensure that the interpreter will be placed in your execution path

### Downloading the Code

* Go to (<https://github.com/FusionIIIT/Fusion>) and click on **Fork**
* You will be redirected to *your* fork, `https://github.com/<your_user_name>/Fusion`
* Open the terminal, change to the directory where you want to clone the **Fusion** repository
* Clone your repository using `git clone https://github.com/<your_user_name>/Fusion`
* Enter the cloned directory using `cd Fusion/`

### Setting up environment

* Create a virtual environment  
  * on **Ubuntu**: `python3 -m venv env`  
  * on **Windows PowerShell**: `python -m venv env`
* Activate the *env*    
  * on **Ubuntu**: `source env/bin/activate`
  * on **Windows PowerShell**: `.\env\Scripts\Activate.ps1`     
  **Note** : On Windows, it may be required to enable the Activate.ps1 script by setting the execution policy for the user. You can do this by issuing the following command: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
* Install the requirements: `pip install -r requirements.txt`

### Running server

* Change directory to **FusionIIIT** `cd FusionIIIT`
* Run the server `python manage.py runserver`

## Working with Code \(Method 1\)

### Setting upstream

* `git remote add upstream https://github.com/FusionIIIT/Fusion`
  * Adds the remote repository (the repository you forked from) so that changes can be pulled from/pushed to it

### Switching branch

* `git checkout -b <module-name>`
  * Creates a new branch `<module-name>` in your repository
* `git checkout <module-name>`
  * Switches to the branch you just created
  
### Migrating Changes (Database)

* Make migrations `$ python manage.py makemigrations`  
* Migrate the changes to the database `$ python manage.py migrate`

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
    
## Testing Procedure: 

### Selenium-webdriver 

Selenium is a browser automation library. Most often used for testing
web-applications, Selenium may be used for any task that requires automating
interaction with the browser.

### Installation

You can visit Selenium Official website and can download the language-specific client drivers(Java in our case)

<https://selenium-release.storage.googleapis.com/3.141/selenium-java-3.141.59.zip>

You will need to download additional components to work with each of the major
browsers. The drivers for Chrome, Firefox, and Microsoft's IE and Edge web
browsers are all standalone executables that should be placed on your system
[PATH]. Apple's safaridriver is shipped with Safari 10 for OS X El Capitan and
macOS Sierra. You will need to enable Remote Automation in the Develop menu of
Safari 10 before testing.


| Browser           | Component                          |
| ----------------- | ---------------------------------- |
| Chrome            | [ChromeDriver](https://chromedriver.storage.googleapis.com/index.html?path=83.0.4103.39/)     |
| Internet Explorer | [IEDriverServer](http://selenium-release.storage.googleapis.com/index.html?path=2.39/)      |
| Firefox           | [GeckoDriver](https://chromedriver.storage.googleapis.com/index.html?path=83.0.4103.39/)   |

### Add the Cucumber Eclipse Plugin for BDD testing
* Install the Cucumber Eclipse Plugin from Eclipse MarketPlace under help

### Getting Started
* Open the Test folder in Eclipse IDE(You are free to use any IDE)
  * Open the pom.xml and build the project
  * Change the driver path in System.setProperty in line 16 of Step_defination.java 
  
* Under the src/main/resources we have main.feature file to define Scenarios and Steps
* Give the step defination of the defined scenarios and steps in Step_Defination.java under src/main/java


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

## Notifications Support

The project now supports notifications across all modules. To implement notifications in your module refer to the instructions below.

* Create your notification class in [**`./FusionIIIT/notifications/views.py`**](https://github.com/FusionIIIT/Fusion/blob/master/FusionIIIT/notification/views.py) 
  ```
  def module_notif(sender, recipient, type):
    url='slug:slug'
    module='ModuleName'
    sender = sender
    recipient = recipient
    verb = ''

    // Type conditioned verb
    if type == 'A':
        verb = "A Verb"
    elif type == 'B':
        verb = "B Verb "
    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)
  ```
* Import your Notification class in your module into **`your_module/views.py`**
  ```
  from notification.views import module_notif
  ```
* To create a Notification, simply call the class and pass user objects for sender, receiver and a string type.
  ```
  module_notif(sender, receiver, type)
  ```
* The Notifications should then appear in the dashboard for the recipient

## Setting up Fusion using Docker
- Make sure you have docker & docker-compose setup properly.
- Run `docker-compose up`
- Once the server starts, run `sudo docker exec -i fusion_db_1 psql -U fusion_admin -d fusionlab < path_to_db_dump`

