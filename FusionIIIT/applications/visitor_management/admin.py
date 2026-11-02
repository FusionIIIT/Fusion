from django.contrib import admin

from . import models


@admin.register(models.Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "access_level", "is_hostel_area", "is_active")
    list_filter = ("access_level", "is_hostel_area", "is_active")
    search_fields = ("code", "name")


@admin.register(models.Gate)
class GateAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "zone", "is_active")


@admin.register(models.AccessPolicy)
class AccessPolicyAdmin(admin.ModelAdmin):
    list_display = ("version", "status", "max_visit_duration_minutes", "walk_in_pass_duration_minutes",
                    "approval_timeout_minutes", "published_at")
    list_filter = ("status",)

    def has_change_permission(self, request, obj=None):
        # VMS-BR-128: published versions are immutable; use the API to create a new version.
        return obj is None or obj.status == "DRAFT"


@admin.register(models.VmsRoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "scope_type", "zone", "gate", "valid_from", "valid_until", "is_active")
    list_filter = ("role", "scope_type", "is_active")
    search_fields = ("user__username",)


@admin.register(models.VisitRequest)
class VisitRequestAdmin(admin.ModelAdmin):
    list_display = ("reference", "visitor", "host", "status", "channel", "scheduled_start", "check_in_at", "check_out_at")
    list_filter = ("status", "channel")
    search_fields = ("reference", "visitor__full_name", "visitor__phone")
    readonly_fields = [f.name for f in models.VisitRequest._meta.fields]


@admin.register(models.RegistryEntry)
class RegistryEntryAdmin(admin.ModelAdmin):
    list_display = ("list_type", "full_name", "id_doc_number", "severity", "state", "expires_at", "is_active")
    list_filter = ("list_type", "state", "severity")
    search_fields = ("full_name", "id_doc_number", "phone", "email")


@admin.register(models.AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "actor_role", "action", "entity_type", "entity_id")
    list_filter = ("action", "actor_role")
    search_fields = ("message", "entity_id")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


for model in (models.Visitor, models.VisitPass, models.GateAttempt, models.VisitLog, models.SecurityAlert,
              models.EmergencyMuster, models.OfflineGateEvent, models.IntegrationConfig, models.VipPermission,
              models.PreAuthorization, models.VisitorEvent, models.BulkVisitorList, models.ExtensionRequest,
              models.VmsNotification, models.HostProfile, models.RegistryPublication):
    admin.site.register(model)
