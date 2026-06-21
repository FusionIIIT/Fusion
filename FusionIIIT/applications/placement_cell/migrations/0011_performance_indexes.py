from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("placement_cell", "0010_placement_appeal"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="notifystudent",
            index=models.Index(fields=["placement_type"], name="placement_c_placeme_1c6ff8_idx"),
        ),
        migrations.AddIndex(
            model_name="notifystudent",
            index=models.Index(fields=["company_name"], name="placement_c_company_0204a2_idx"),
        ),
        migrations.AddIndex(
            model_name="placementstatus",
            index=models.Index(fields=["unique_id", "invitation"], name="placement_c_unique__068844_idx"),
        ),
        migrations.AddIndex(
            model_name="placementstatus",
            index=models.Index(fields=["unique_id", "timestamp"], name="placement_c_unique__5767b0_idx"),
        ),
        migrations.AddIndex(
            model_name="studentrecord",
            index=models.Index(fields=["unique_id", "record_id"], name="placement_c_unique__964ebc_idx"),
        ),
        migrations.AddIndex(
            model_name="placementschedule",
            index=models.Index(fields=["placement_date"], name="placement_c_placeme_190366_idx"),
        ),
        migrations.AddIndex(
            model_name="placementschedule",
            index=models.Index(fields=["schedule_at"], name="placement_c_schedul_f76a20_idx"),
        ),
        migrations.AddIndex(
            model_name="placementschedule",
            index=models.Index(fields=["notify_id", "placement_date"], name="placement_c_notify__957faa_idx"),
        ),
        migrations.AddIndex(
            model_name="placementapplication",
            index=models.Index(fields=["student", "created_at"], name="placement_c_student_5ef23d_idx"),
        ),
        migrations.AddIndex(
            model_name="placementapplication",
            index=models.Index(fields=["schedule", "created_at"], name="placement_c_schedul_6db3a0_idx"),
        ),
        migrations.AddIndex(
            model_name="placementapplication",
            index=models.Index(fields=["student", "status"], name="placement_c_student_10ef00_idx"),
        ),
        migrations.AddIndex(
            model_name="placementapplication",
            index=models.Index(fields=["schedule", "status"], name="placement_c_schedul_93bec9_idx"),
        ),
        migrations.AddIndex(
            model_name="placementround",
            index=models.Index(fields=["schedule", "round_no"], name="placement_c_schedul_6c9b4d_idx"),
        ),
        migrations.AddIndex(
            model_name="placementround",
            index=models.Index(fields=["schedule", "start_datetime"], name="placement_c_schedul_3be9db_idx"),
        ),
        migrations.AddIndex(
            model_name="placementapplicationtimeline",
            index=models.Index(fields=["application", "created_at"], name="placement_c_applica_6646ff_idx"),
        ),
        migrations.AddIndex(
            model_name="placementinterviewschedule",
            index=models.Index(fields=["application", "scheduled_at"], name="placement_c_applica_45d617_idx"),
        ),
        migrations.AddIndex(
            model_name="placementinterviewschedule",
            index=models.Index(fields=["application", "round_no"], name="placement_c_applica_209fbb_idx"),
        ),
        migrations.AddIndex(
            model_name="placementprofiledocument",
            index=models.Index(fields=["student", "uploaded_at"], name="placement_c_student_27f93a_idx"),
        ),
    ]
