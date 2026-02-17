# FusionIIIT (Backend)

**FusionIIIT** is the automation of various functionalities, modules and tasks of/for **PDPM Indian Institute of Information Technology, Design and Manufacturing, Jabalpur** being developed in `python3.8` and using `Django` Webframework.

## Critical Prerequisites & Software Requirements

**You MUST strictly use the following versions:**

* Python `3.8.10`
* pip `21.1.1`
* PostgreSQL `14`
* Git

## System Configuration

* Ubuntu `20.04` **(Recommended)**
* *OR* WSL for Windows `10` \(Follow the guide below\) :[Windows Subsystem for Linux Installation Guide for Windows 10](https://docs.microsoft.com/en-us/windows/wsl/install-win10)
* *OR* Windows `7/8/8.1/10`

## Module-Wise Sync Targets

For production synchronization targets, refer to: [Fusion-README](https://github.com/FusionIIIT/Fusion-README)

## Contributing Guidelines

For contributing to this repository, you have to follow the guidelines given in [CONTRIBUTING.md](./CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) for smooth workflow of contributions and changes inside repository.

## Full-Stack Module-Wise Git Workflow Guide

This section outlines the repository setup, branch management, and contribution workflow for teams working on the Fusion ERP Backend.

### Phase 1: Team Lead Setup

1. **Fork the Main Repository:**

   * Go to [https://github.com/FusionIIIT/Fusion](https://github.com/FusionIIIT/Fusion) and click **Fork, Uncheck** the **Checkbox,** and click **Create fork.**
2. **Share:**

   * Distribute your forked repository URL to your team members

### Phase 2: Team Member Setup

1. **Fork the Team Lead's Repository:**

   * Navigate to your Team Lead's fork and fork it to your own GitHub account
2. **Clone Locally:**

   ```sh
   git clone https://github.com/<Your-Username>/Fusion.git
   ```
3. **Set Upstream:**

   ```sh
   cd Fusion
   git remote add upstream https://github.com/<TeamLead-Username>/Fusion.git
   ```

### Phase 3: Module-Wise Branch Switching

**Note:** v1 (MANUAL : Work on Existing Codebase) and v2 (AI : Work from Scracth according to documnets and Fusion README) - If you are assigned to the AI group, replace `v1` with `v2` in the commands below.

Fetch upstream data first:

```sh
cd Fusion
git fetch upstream
```

Then run your specific module command:

* **Examination:** `git checkout -b examination-v1 upstream/examination-v1`
* **LMS:** `git checkout -b lms-v1 upstream/lms-v1`
* **Award & Scholarship:** `git checkout -b scholarships-v1 upstream/scholarships-v1`
* **Department:** `git checkout -b department-v1 upstream/department-v1`
* **Other Academic Procedure:** `git checkout -b academic-procedures-v1 upstream/academic-procedures-v1`
* **Announcements:** `git checkout -b announcements-v1 upstream/announcements-v1`
* **Placement Cell + PBI:** `git checkout -b placement-pbi-v1 upstream/placement-pbi-v1`
* **Gymkhana:** `git checkout -b gymkhana-v1 upstream/gymkhana-v1`
* **Primary Health Center:** `git checkout -b health-center-v1 upstream/health-center-v1`
* **Hostel Management:** `git checkout -b hostel-management-v1 upstream/hostel-management-v1`
* **Mess Management:** `git checkout -b mess-management-v1 upstream/mess-management-v1`
* **Visitor Hostel:** `git checkout -b visitor-hostel-v1 upstream/visitor-hostel-v1`
* **Visitor Management System:** `git checkout -b visitor-management-v1 upstream/visitor-management-v1`
* **Dashboards:** `git checkout -b dashboards-v1 upstream/dashboards-v1`
* **File Tracking System:** `git checkout -b file-tracking-v1 upstream/file-tracking-v1`
* **RSPC:** `git checkout -b rspc-v1 upstream/rspc-v1`
* **P&S Management:** `git checkout -b ps-management-v1 upstream/ps-management-v1`
* **HR (EIS):** `git checkout -b hr-eis-v1 upstream/hr-eis-v1`
* **Patent Management System:** `git checkout -b patent-management-v1 upstream/patent-management-v1`
* **Institute Works Department:** `git checkout -b institute-works-v1 upstream/institute-works-v1`
* **Internal Audit and Accounts:** `git checkout -b audit-accounts-v1 upstream/audit-accounts-v1`
* **Complaint Management:** `git checkout -b complaint-management-v1 upstream/complaint-management-v1`

## How to get started

* on **Ubuntu**:

  ```sh
  // Install the required packages using the following command:

  sudo apt install python3-pip python3-dev python3-venv libpq-dev build-essential git
  sudo -H pip3 install --upgrade pip
  ```
* on **Windows**:

  * Get Python 3.8.10 from [here](https://www.python.org/downloads/release/python-3810/)
  * Git from [here](https://git-scm.com/download/win)
  * Install both using the downloaded `exe` files
    **Important:** Make sure to check the box that says **Add Python 3.x to PATH** to ensure that the interpreter will be placed in your execution path

### Setting up environment

* Create a virtual environment, run below command inside Fusion Directory or root.
  * on **Ubuntu**: `python3 -m venv env`
  * on **Windows PowerShell**: `python -m venv env OR py -3.8 -m venv env`
* Activate the *env*
  * on **Ubuntu**: `source env/bin/activate`
  * on **Windows PowerShell**: `.\env\Scripts\Activate.ps1`
    **Note** : On Windows, it may be required to enable the Activate.ps1 script by setting the execution policy for the user. You can do this by issuing the following command: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Installing Packages

Navigate to the Fusion directory and install requirements:

```sh
cd Fusion
pip install -r requirements.txt
```

### Running server

* Change directory to **FusionIIIT** `cd FusionIIIT`
* Run the server `python manage.py runserver`

## Phase 4: Syncing, Committing, and PRs

### Production Sync Targets

* **Backend Production Branch:** `prod/acad-react`

### Workflow

1. **Sync with Production:**

   * Frequently pull the latest changes from your specific module's production branch to avoid merge conflicts later
   * Team lead syncs first, then team members sync from the team lead's fork

   ```sh
   git pull upstream <your-assigned-branch>
   ```
2. **Make Changes:**

   * Make your code changes and commit them locally to your active module branch
3. **Migrating Database Changes:**

   * Make migrations: `python manage.py makemigrations`
   * Migrate the changes to the database: `python manage.py migrate`
4. **Committing:**

   ```sh
   git add .
   git commit -m "Your descriptive commit message"
   ```
5. **Pushing:**

   ```sh
   git push origin <your-assigned-branch>
   ```
6. **Create Pull Request:**

   * Go to `https://github.com/<your_user_name>/Fusion/tree/<your-assigned-branch>` and create a Pull Request
   * **Important:** Target the Team Lead's fork, NOT the main FusionIIIT repository

## Working with Code \(Alternative\)

* **(Recommended)** Use [Visual Studio Code](https://code.visualstudio.com/) as a text editor. Go through the [Tutorial](https://code.visualstudio.com/docs/python/python-tutorial) for getting started with **Visual Studio Code for Python**.**Note** : Use the following guide if using **WSL** for Development([https://code.visualstudio.com/docs/remote/wsl](https://code.visualstudio.com/docs/remote/wsl))
* Use the inbuilt **Source Control** feature for checking out, committing, pushing, pulling changes. You can also use [Github Desktop](https://desktop.github.com/) **_\(Windows/Mac only\)_**.
* Refer to below link for best practices regarding commit messages :
  ([https://gist.github.com/robertpainsi/b632364184e70900af4ab688decf6f53](https://gist.github.com/robertpainsi/b632364184e70900af4ab688decf6f53))

## Testing Procedure:

### Selenium-webdriver

Selenium is a browser automation library. Most often used for testing
web-applications, Selenium may be used for any task that requires automating
interaction with the browser.

### Installation

You can visit Selenium Official website and can download the language-specific client drivers(Java in our case)

[https://selenium-release.storage.googleapis.com/3.141/selenium-java-3.141.59.zip](https://selenium-release.storage.googleapis.com/3.141/selenium-java-3.141.59.zip)

You will need to download additional components to work with each of the major
browsers. The drivers for Chrome, Firefox, and Microsoft's IE and Edge web
browsers are all standalone executables that should be placed on your system
[PATH]. Apple's safaridriver is shipped with Safari 10 for OS X El Capitan and
macOS Sierra. You will need to enable Remote Automation in the Develop menu of
Safari 10 before testing.

| Browser           | Component                                                                              |
| ----------------- | -------------------------------------------------------------------------------------- |
| Chrome            | [ChromeDriver](https://chromedriver.storage.googleapis.com/index.html?path=83.0.4103.39/) |
| Internet Explorer | [IEDriverServer](http://selenium-release.storage.googleapis.com/index.html?path=2.39/)    |
| Firefox           | [GeckoDriver](https://chromedriver.storage.googleapis.com/index.html?path=83.0.4103.39/)  |

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
