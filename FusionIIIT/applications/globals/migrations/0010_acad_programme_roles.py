from django.db import migrations

ROLES = [
    ("Acad UG", "Academic Administrator (Undergraduate)"),
    ("Acad PG", "Academic Administrator (Postgraduate)"),
    ("Acad Ph.D.", "Academic Administrator (Doctoral)"),
]


def add_roles(apps, schema_editor):
    Designation = apps.get_model("globals", "Designation")
    for name, full_name in ROLES:
        Designation.objects.get_or_create(
            name=name,
            defaults={"full_name": full_name, "type": "administrative"},
        )


def remove_roles(apps, schema_editor):
    Designation = apps.get_model("globals", "Designation")
    HoldsDesignation = apps.get_model("globals", "HoldsDesignation")
    names = [name for name, _ in ROLES]
    HoldsDesignation.objects.filter(designation__name__in=names).delete()
    Designation.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("globals", "0009_announcement_created_by_set_null"),
    ]

    operations = [
        migrations.RunPython(add_roles, remove_roles),
    ]
