from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('examination', '0005_seatingarrangement'),
    ]

    operations = [
        # ExamRoom: add cols (number of columns in the room)
        migrations.AddField(
            model_name='examroom',
            name='cols',
            field=models.PositiveIntegerField(
                default=9,
                help_text='Number of columns in the room layout',
            ),
        ),
        # SeatingArrangement: add row_no and col_no
        migrations.AddField(
            model_name='seatingarrangement',
            name='row_no',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='seatingarrangement',
            name='col_no',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
