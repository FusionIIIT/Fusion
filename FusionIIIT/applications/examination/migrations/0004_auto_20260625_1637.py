from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('examination', '0003_resultannouncement_semester_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='resultannouncement',
            name='per_student_selection',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='PublishedResultStudent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('roll_no', models.CharField(max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('announcement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='published_students', to='examination.resultannouncement')),
            ],
            options={
                'unique_together': {('announcement', 'roll_no')},
            },
        ),
    ]
