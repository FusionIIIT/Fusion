from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('filetracking', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FTAccessPolicy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=100, unique=True)),
                ('value', models.JSONField(default=dict)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['key'],
            },
        ),
        migrations.CreateModel(
            name='FTAdminAuditLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('CREATE_USER', 'Create User'), ('UPDATE_USER', 'Update User'), ('DELETE_USER', 'Delete User'), ('ASSIGN_ROLE', 'Assign Role'), ('REMOVE_ROLE', 'Remove Role'), ('UPDATE_POLICY', 'Update Policy')], max_length=30)),
                ('target_identifier', models.CharField(blank=True, max_length=120)),
                ('details', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ft_admin_actions', to=settings.AUTH_USER_MODEL)),
                ('target_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ft_admin_targets', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
