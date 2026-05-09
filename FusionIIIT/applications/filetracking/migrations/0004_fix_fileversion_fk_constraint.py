from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('filetracking', '0003_fileversion'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                'ALTER TABLE filetracking_fileversion '
                'DROP CONSTRAINT IF EXISTS filetracking_fileversion_file_id_7322c879_fk_File_id;'
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='fileversion',
            name='file',
            field=models.ForeignKey(
                db_constraint=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='versions',
                to='filetracking.file',
            ),
        ),
    ]
