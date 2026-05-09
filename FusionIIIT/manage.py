#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    default_settings = "Fusion.settings.development"
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        default_settings = "Fusion.settings.test"
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", default_settings)

    from django.core.management import execute_from_command_line

execute_from_command_line(sys.argv)
