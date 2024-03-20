
import os
import sys
from django.core.management import execute_from_command_line
from django.contrib.auth.management.commands.createsuperuser import Command


def create_superuser():
    command = Command()
    command.handle(username='admin', email='')


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project.settings")
    create_superuser()
    execute_from_command_line(sys.argv)
