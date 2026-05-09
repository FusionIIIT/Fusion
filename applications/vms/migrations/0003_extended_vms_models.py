"""
Migration for all new VMS models and field additions.

Covers: VisitorRequest, HostAuthority, RegistrationQuota, AccessZone,
VisitorLocation, BlacklistAuditLog, EscortAssignment, VIPActivityLog,
SystemConfig, ConfigChangeLog, VisitingHours, DataOperationLog,
and field additions to BlacklistEntry and SecurityIncident.
"""

import uuid
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vms", "0002_visitorpass_barcode_data_to_text"),
        ("globals", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # --- BlacklistEntry: add evidence + added_by fields ---
        migrations.AddField(
            model_name="blacklistentry",
            name="evidence",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="blacklistentry",
            name="added_by",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="vms_blacklist_added",
                to="globals.extrainfo",
            ),
        ),

        # --- SecurityIncident: add tracking_number, escalation_level, containment_actions ---
        migrations.AddField(
            model_name="securityincident",
            name="tracking_number",
            field=models.CharField(blank=True, max_length=32, unique=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="securityincident",
            name="escalation_level",
            field=models.IntegerField(
                choices=[(0, "None"), (1, "Supervisor"), (2, "Security Head"), (3, "Administration"), (4, "Police / Lockdown")],
                default=0,
            ),
        ),
        migrations.AddField(
            model_name="securityincident",
            name="containment_actions",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),

        # --- VisitorRequest ---
        migrations.CreateModel(
            name="VisitorRequest",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("request_id", models.CharField(db_index=True, max_length=32, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("visit", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="request", to="vms.visit")),
            ],
        ),

        # --- HostAuthority ---
        migrations.CreateModel(
            name="HostAuthority",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("authority_level", models.CharField(choices=[("basic", "Basic"), ("department", "Department"), ("admin", "Admin"), ("super_admin", "Super Admin")], default="basic", max_length=20)),
                ("department", models.CharField(blank=True, max_length=120)),
                ("can_approve_vip", models.BooleanField(default=False)),
                ("max_daily_approvals", models.PositiveIntegerField(default=10)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="vms_host_authority", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name_plural": "Host Authorities"},
        ),

        # --- RegistrationQuota ---
        migrations.CreateModel(
            name="RegistrationQuota",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("count", models.PositiveIntegerField(default=0)),
                ("host_user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="vms_quotas", to=settings.AUTH_USER_MODEL)),
            ],
            options={"unique_together": {("host_user", "date")}},
        ),

        # --- AccessZone ---
        migrations.CreateModel(
            name="AccessZone",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=60, unique=True)),
                ("description", models.CharField(blank=True, max_length=200)),
                ("requires_vip", models.BooleanField(default=False)),
                ("requires_escort", models.BooleanField(default=False)),
                ("is_restricted", models.BooleanField(default=False)),
                ("active", models.BooleanField(default=True)),
            ],
        ),

        # --- VisitorLocation ---
        migrations.CreateModel(
            name="VisitorLocation",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("checkpoint_name", models.CharField(max_length=120)),
                ("scanned_at", models.DateTimeField(auto_now_add=True)),
                ("visit", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="locations", to="vms.visit")),
                ("zone", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="vms.accesszone")),
                ("recorded_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vms_location_scans", to="globals.extrainfo")),
            ],
            options={"ordering": ["-scanned_at"]},
        ),

        # --- BlacklistAuditLog ---
        migrations.CreateModel(
            name="BlacklistAuditLog",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("add", "Added"), ("remove", "Removed"), ("update", "Updated")], max_length=10)),
                ("id_number", models.CharField(max_length=64)),
                ("reason", models.TextField(blank=True)),
                ("evidence", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("blacklist_entry", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_logs", to="vms.blacklistentry")),
                ("performed_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vms_blacklist_actions", to="globals.extrainfo")),
            ],
        ),

        # --- EscortAssignment ---
        migrations.CreateModel(
            name="EscortAssignment",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                ("released_at", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("visit", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="escorts", to="vms.visit")),
                ("escort", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vms_escort_duties", to="globals.extrainfo")),
            ],
        ),

        # --- VIPActivityLog ---
        migrations.CreateModel(
            name="VIPActivityLog",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=120)),
                ("details", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("visit", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="vip_logs", to="vms.visit")),
                ("recorded_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vms_vip_actions", to="globals.extrainfo")),
            ],
        ),

        # --- SystemConfig ---
        migrations.CreateModel(
            name="SystemConfig",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=120, unique=True)),
                ("value", models.TextField()),
                ("description", models.CharField(blank=True, max_length=256)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vms_config_changes", to="globals.extrainfo")),
            ],
        ),

        # --- ConfigChangeLog ---
        migrations.CreateModel(
            name="ConfigChangeLog",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("old_value", models.TextField()),
                ("new_value", models.TextField()),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                ("config", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="change_logs", to="vms.systemconfig")),
                ("changed_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vms_config_audit", to="globals.extrainfo")),
            ],
        ),

        # --- VisitingHours ---
        migrations.CreateModel(
            name="VisitingHours",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("day_of_week", models.IntegerField(choices=[(0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday")])),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                ("is_holiday", models.BooleanField(default=False)),
                ("holiday_name", models.CharField(blank=True, max_length=120)),
                ("active", models.BooleanField(default=True)),
            ],
            options={"verbose_name_plural": "Visiting Hours"},
        ),

        # --- DataOperationLog ---
        migrations.CreateModel(
            name="DataOperationLog",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("operation_type", models.CharField(choices=[("export", "Export"), ("import", "Import")], max_length=10)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("running", "Running"), ("completed", "Completed"), ("failed", "Failed"), ("rolled_back", "Rolled Back")], default="pending", max_length=16)),
                ("parameters", models.JSONField(default=dict)),
                ("result_summary", models.TextField(blank=True)),
                ("records_processed", models.PositiveIntegerField(default=0)),
                ("error_details", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("initiated_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vms_data_ops", to="globals.extrainfo")),
            ],
        ),
    ]
