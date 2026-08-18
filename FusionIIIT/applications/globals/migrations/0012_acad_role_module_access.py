from django.db import migrations

NEW_ROLES = ["Acad UG", "Acad PG", "Acad Ph.D."]


def clone_acadadmin_access(apps, schema_editor):
    ModuleAccess = apps.get_model("globals", "ModuleAccess")
    source = ModuleAccess.objects.filter(designation__iexact="acadadmin").first()
    if source is None:
        return
    fields = [
        f.name for f in ModuleAccess._meta.get_fields()
        if f.concrete and f.name not in ("id", "designation")
    ]
    values = {name: getattr(source, name) for name in fields}
    for role in NEW_ROLES:
        ModuleAccess.objects.get_or_create(designation=role, defaults=values)


def drop_access(apps, schema_editor):
    ModuleAccess = apps.get_model("globals", "ModuleAccess")
    ModuleAccess.objects.filter(designation__in=NEW_ROLES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("globals", "0011_announcement_target_programme"),
    ]

    operations = [
        migrations.RunPython(clone_acadadmin_access, drop_access),
    ]
