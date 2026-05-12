# Generated for UC-VH-011: Manage Inventory & Threshold Alerts

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('visitor_hostel', '0002_add_offline_booking_fields'),
    ]

    operations = [
        # Add threshold management fields to Inventory
        migrations.AddField(
            model_name='inventory',
            name='threshold_quantity',
            field=models.IntegerField(default=5, help_text='Minimum quantity before alert (BR-VH-007)'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='is_critical',
            field=models.BooleanField(default=False, help_text='Auto-set when quantity < threshold'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='last_threshold_alert',
            field=models.DateTimeField(blank=True, help_text='Last alert sent', null=True),
        ),
        migrations.AddField(
            model_name='inventory',
            name='unit',
            field=models.CharField(default='pieces', help_text='Unit of measurement', max_length=20),
        ),
        migrations.AddField(
            model_name='inventory',
            name='category',
            field=models.CharField(blank=True, help_text='Item category (cleaning, maintenance, etc.)', max_length=50),
        ),
        migrations.AddField(
            model_name='inventory',
            name='pending_replenishment',
            field=models.BooleanField(default=False, help_text='Has pending replenishment request'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='last_replenishment_date',
            field=models.DateField(blank=True, null=True),
        ),
        
        # Create ReplenishmentRequest model
        migrations.CreateModel(
            name='ReplenishmentRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('requested_quantity', models.IntegerField(help_text='Quantity requested for replenishment')),
                ('current_quantity', models.IntegerField(help_text='Current stock when request was made')),
                ('urgency', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium', max_length=20)),
                ('justification', models.TextField(help_text='Reason for replenishment request')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('ordered', 'Ordered'), ('received', 'Received')], default='pending', max_length=20)),
                ('approved_quantity', models.IntegerField(blank=True, help_text='Quantity approved by VhIncharge', null=True)),
                ('approval_remarks', models.TextField(blank=True, help_text='VhIncharge remarks')),
                ('estimated_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, help_text='When reviewed by VhIncharge', null=True)),
                ('vendor_info', models.TextField(blank=True, help_text='Vendor details for purchase')),
                ('actual_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('delivery_date', models.DateField(blank=True, null=True)),
                ('approved_by', models.ForeignKey(blank=True, help_text='VhIncharge who approved', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inventory_approvals', to=settings.AUTH_USER_MODEL)),
                ('inventory_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='replenishment_requests', to='visitor_hostel.inventory')),
                ('requested_by', models.ForeignKey(help_text='Caretaker who requested', on_delete=django.db.models.deletion.CASCADE, related_name='inventory_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]