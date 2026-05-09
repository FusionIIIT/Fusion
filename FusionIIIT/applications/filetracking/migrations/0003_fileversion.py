from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('filetracking', '0002_ft_admin_management'),
    ]

    operations = [
        migrations.CreateModel(
            name='FileVersion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version_number', models.PositiveIntegerField()),
                ('action', models.CharField(choices=[('SAVE', 'Save Amendment'), ('FORWARD', 'Amend and Forward')], default='SAVE', max_length=20)),
                ('comment', models.TextField(blank=True)),
                ('snapshot', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='globals.extrainfo')),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='filetracking.file')),
            ],
            options={
                'ordering': ['-version_number'],
                'unique_together': {('file', 'version_number')},
            },
        ),
    ]
