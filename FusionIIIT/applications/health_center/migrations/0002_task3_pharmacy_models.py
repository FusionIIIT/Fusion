# Generated migration for Task 3: Pharmacy Models Refactoring
# Refactors InventoryStock into Stock & Expiry models
# Updates Prescription with status field
# Enhances PrescribedMedicine with qty_dispensed, notes, and expiry_used

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('health_center', '0001_initial'),
    ]

    operations = [
        # 1. Create Stock model (simplified from InventoryStock)
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_qty', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('medicine', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='stock', to='health_center.medicine')),
            ],
            options={
                'db_table': 'health_center_stock',
                'ordering': ['medicine'],
            },
        ),

        # 2. Create Expiry model (batch tracking for FIFO)
        migrations.CreateModel(
            name='Expiry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch_no', models.CharField(max_length=100)),
                ('qty', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('expiry_date', models.DateField()),
                ('is_returned', models.BooleanField(default=False)),
                ('returned_qty', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expiry_batches', to='health_center.stock')),
            ],
            options={
                'db_table': 'health_center_expiry',
                'ordering': ['expiry_date'],
                'unique_together': {('stock', 'batch_no')},
            },
        ),

        # 3. Add status field to Prescription
        migrations.AddField(
            model_name='prescription',
            name='status',
            field=models.CharField(
                choices=[('ISSUED', 'Issued'), ('DISPENSED', 'Dispensed'), ('CANCELLED', 'Cancelled'), ('COMPLETED', 'Completed')],
                default='ISSUED',
                max_length=20
            ),
        ),

        # 4. Rename prescription_date to issued_date in Prescription
        migrations.RenameField(
            model_name='prescription',
            old_name='prescription_date',
            new_name='issued_date',
        ),

        # 5. Update PrescribedMedicine model
        migrations.AddField(
            model_name='prescribedmedicine',
            name='qty_dispensed',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),

        migrations.AddField(
            model_name='prescribedmedicine',
            name='notes',
            field=models.TextField(blank=True),
        ),

        migrations.AddField(
            model_name='prescribedmedicine',
            name='is_dispensed',
            field=models.BooleanField(default=False),
        ),

        migrations.AddField(
            model_name='prescribedmedicine',
            name='dispensed_date',
            field=models.DateField(blank=True, null=True),
        ),

        # Rename quantity field to qty_prescribed for clarity
        migrations.RenameField(
            model_name='prescribedmedicine',
            old_name='quantity',
            new_name='qty_prescribed',
        ),

        # Update PrescribedMedicine.stock_used to expiry_used with new FK
        migrations.RemoveField(
            model_name='prescribedmedicine',
            name='stock_used',
        ),

        migrations.AddField(
            model_name='prescribedmedicine',
            name='expiry_used',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='prescribed_medicines',
                to='health_center.expiry'
            ),
        ),

        # 6. Keep old InventoryStock table reference for backward compatibility via proxy model
        migrations.CreateModel(
            name='InventoryStock',
            fields=[],
            options={
                'proxy': True,
                'db_table': 'health_center_stock',
            },
            bases=('health_center.stock',),
        ),
    ]
