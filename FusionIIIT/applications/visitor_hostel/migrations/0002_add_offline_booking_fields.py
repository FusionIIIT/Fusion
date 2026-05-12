# Generated for UC-VH-006: Manage Offline Bookings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visitor_hostel', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bookingdetail',
            name='is_offline',
            field=models.BooleanField(default=False, help_text='True if booking was made offline (telephonic/walk-in)'),
        ),
        migrations.AddField(
            model_name='bookingdetail',
            name='booking_source',
            field=models.CharField(choices=[('online', 'Online'), ('telephonic', 'Telephonic'), ('walkin', 'Walk-in')], default='online', help_text='Source of booking', max_length=10),
        ),
        migrations.AddField(
            model_name='bookingdetail',
            name='intender_name',
            field=models.CharField(blank=True, help_text='Name of person making offline booking', max_length=100),
        ),
        migrations.AddField(
            model_name='bookingdetail',
            name='intender_phone',
            field=models.CharField(blank=True, help_text='Phone of person making offline booking', max_length=15),
        ),
        migrations.AddField(
            model_name='bookingdetail',
            name='intender_email',
            field=models.CharField(blank=True, help_text='Email of person making offline booking', max_length=100),
        ),
        migrations.AddField(
            model_name='bookingdetail',
            name='intender_relation',
            field=models.CharField(blank=True, help_text='Relation to visitor', max_length=50),
        ),
    ]