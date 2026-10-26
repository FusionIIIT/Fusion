# Database Optimization Migration for Student List Generation

from django.db import migrations

class Migration(migrations.Migration):
    """
    Add database indexes to optimize student list generation queries
    """
    
    dependencies = [
        ('programme_curriculum', '0025_update_minority_values'),
    ]

    operations = [
        # Indexes bypassed to resolve circular dependency with academic_procedures
    ]
