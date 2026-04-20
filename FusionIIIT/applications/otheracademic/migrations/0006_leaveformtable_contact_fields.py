from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('otheracademic', '0005_alter_pgtaassignment_multiple_subjects'),
    ]

    operations = [
        migrations.AddField(
            model_name='leaveformtable',
            name='stud_mobile_no',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='leaveformtable',
            name='parent_mobile_no',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='leaveformtable',
            name='leave_mobile_no',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='leaveformtable',
            name='curr_sem',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]