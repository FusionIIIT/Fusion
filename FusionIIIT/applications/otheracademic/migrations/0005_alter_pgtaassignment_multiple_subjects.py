from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("otheracademic", "0004_assignment_history"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pgtaassignment",
            name="pg_student",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="globals.extrainfo"),
        ),
        migrations.AddConstraint(
            model_name="pgtaassignment",
            constraint=models.UniqueConstraint(
                fields=("pg_student", "subject"),
                name="uniq_pg_ta_assignment_student_subject",
            ),
        ),
    ]