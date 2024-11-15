from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('item_id', models.AutoField(primary_key=True)),
                ('item_name', models.CharField(max_length=100)),
                ('quantity', models.PositiveIntegerField(default=0)),
                ('type', models.CharField(max_length=20, choices=[('Consumable', 'Consumable'), ('Non-Consumable', 'Non-Consumable')])),
                ('unit', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DepartmentInfo',
            fields=[
                ('subdepartment_id', models.AutoField(primary_key=True)),
                ('subdepartment_name', models.CharField(max_length=100)),
                ('department_name', models.CharField(max_length=100)),
                ('admin', models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Relationship',
            fields=[
                ('item_id', models.ForeignKey(on_delete=models.CASCADE, to='app_name.Item')),
                ('subdepartment_id', models.ForeignKey(on_delete=models.CASCADE, to='app_name.DepartmentInfo')),
                ('quantity', models.PositiveIntegerField(default=0)),
            ],
            options={
                'unique_together': {('item_id', 'subdepartment_id')},
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('event_id', models.AutoField(primary_key=True)),
                ('event_type', models.CharField(max_length=20, choices=[('Addition', 'Addition'), ('Removal', 'Removal'), ('Transfer', 'Transfer')])),
                ('quantity', models.PositiveIntegerField(default=0)),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('item_id', models.ForeignKey(on_delete=models.CASCADE, to='app_name.Item')),
                ('in_subdepartment_id', models.ForeignKey(on_delete=models.CASCADE, related_name='in_subdepartment', to='app_name.DepartmentInfo')),
                ('from_subdepartment_id', models.ForeignKey(on_delete=models.CASCADE, related_name='from_subdepartment', to='app_name.DepartmentInfo')),
                ('responsible_user', models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
