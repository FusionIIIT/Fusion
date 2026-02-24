from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('academic_information', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='specialization',
            field=models.CharField(choices=[('Power and Control', 'Power and Control'), ('Power & Control', 'Power & Control'), ('Microwave and Communication Engineering', 'Microwave and Communication Engineering'), ('Communication and Signal Processing', 'Communication and Signal Processing'), ('Micro-nano Electronics', 'Micro-nano Electronics'), ('Nanoelectronics and VLSI Design', 'Nanoelectronics and VLSI Design'), ('CAD/CAM', 'CAD/CAM'), ('Design', 'Design'), ('Manufacturing', 'Manufacturing'), ('Manufacturing and Automation', 'Manufacturing and Automation'), ('CSE', 'CSE'), ('AI & ML', 'AI & ML'), ('Data Science', 'Data Science'), ('Mechatronics', 'Mechatronics'), ('MDes', 'MDes'), ('None', 'None'), ('', 'No Specialization')], default='', max_length=40, null=True),
        ),
    ]
