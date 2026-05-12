from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visitor_hostel', '0004_bill_extra_charges'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='offline_bill_id',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name='bill',
            name='offline_bill_photo',
            field=models.FileField(blank=True, null=True, upload_to='visitor_hostel/payments/offline_bills/'),
        ),
        migrations.AddField(
            model_name='bill',
            name='payment_mode',
            field=models.CharField(blank=True, choices=[('online', 'Online'), ('offline', 'Offline')], max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='bill',
            name='payment_screenshot',
            field=models.FileField(blank=True, null=True, upload_to='visitor_hostel/payments/screenshots/'),
        ),
        migrations.AddField(
            model_name='bill',
            name='transaction_id',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
    ]
