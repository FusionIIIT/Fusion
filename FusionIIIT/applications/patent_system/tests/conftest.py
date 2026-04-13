"""
conftest.py — Initial setup scaffold.
Customize this file with your module's specific logic.
"""
from django.test import TestCase

class BaseModuleTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass # Add your module setup here
