from django.conf import settings
from django.db import migrations, models
import django.utils.timezone
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('globals', '0012_acad_role_module_access'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='holdsdesignation',
            name='start_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='holdsdesignation',
            name='end_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='holdsdesignation',
            name='start_time',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now,
                                       null=True),
        ),
        migrations.CreateModel(
            name='SystemAdminAccess',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('assigned_by', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='granted_system_admin_access',
                    to=settings.AUTH_USER_MODEL)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='system_admin_access', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
