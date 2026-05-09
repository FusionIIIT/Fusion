# Generated manually for mess portal announcements support.

import datetime

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('central_mess', '0005_warden_decision_flow'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessAnnouncement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('priority', models.CharField(
                    choices=[('normal', 'Normal'), ('high', 'High'),
                             ('urgent', 'Urgent')],
                    default='normal',
                    max_length=20,
                )),
                ('publish_date', models.DateField(default=datetime.date.today)),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=models.SET_NULL,
                    related_name='mess_announcements_created',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ('-publish_date', '-created_at'),
            },
        ),
    ]
