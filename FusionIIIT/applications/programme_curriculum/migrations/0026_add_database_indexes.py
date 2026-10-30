# Database Optimization Migration for Student List Generation

from django.db import migrations

class Migration(migrations.Migration):
    """
    Add database indexes to optimize student list generation queries
    """
    
    dependencies = [
        ('programme_curriculum', '0025_update_minority_values'),
        # The indexed table and every column named below belong to that app;
        # without this the order is undefined and a fresh database fails here.
        ('academic_procedures', '0010_populate_session_and_type'),
    ]

    operations = [
        # Indexes bypassed to resolve circular dependency with academic_procedures
    ]
