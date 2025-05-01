from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('academic_information', '0001_initial'),
    ]
    operations = [
        migrations.AddField(
            model_name='student',
            name='hall_id',
            field=models.CharField(max_length=20, null=True),
        ),
    ]