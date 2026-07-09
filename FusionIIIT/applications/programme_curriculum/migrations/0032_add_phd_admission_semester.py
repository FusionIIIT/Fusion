from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programme_curriculum', '0031_add_curriculum_options_to_batch'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentbatchupload',
            name='admission_semester',
            field=models.CharField(blank=True, choices=[('Odd', 'Odd Semester'), ('Even', 'Even Semester')], help_text='For PhD students: Semester in which admission occurred (becomes their Semester 1)', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='batch',
            name='name',
            field=models.CharField(choices=[('B.Tech', 'B.Tech'), ('M.Tech', 'M.Tech'), ('M.Tech AI & ML', 'M.Tech AI & ML'), ('M.Tech Data Science', 'M.Tech Data Science'), ('M.Tech Communication and Signal Processing', 'M.Tech Communication and Signal Processing'), ('M.Tech Nanoelectronics and VLSI Design', 'M.Tech Nanoelectronics and VLSI Design'), ('M.Tech Power & Control', 'M.Tech Power & Control'), ('M.Tech Design', 'M.Tech Design'), ('M.Tech CAD/CAM', 'M.Tech CAD/CAM'), ('M.Tech Manufacturing and Automation', 'M.Tech Manufacturing and Automation'), ('B.Des', 'B.Des'), ('M.Des', 'M.Des'), ('Phd', 'Phd')], max_length=50),
        ),
        migrations.AlterField(
            model_name='studentbatchupload',
            name='jee_app_no',
            field=models.CharField(blank=True, help_text='JEE App. No./CCMT Roll. No.', max_length=50, null=True, unique=True),
        ),
    ]
