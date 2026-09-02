from django.db import migrations


def clear_stored_pdfs(apps, schema_editor):
    """Drop the cached copies so issued certificates pick up the current wording.

    A stored PDF is served back verbatim, so certificates issued before the
    salutation was capitalised would keep the old wording for ever. Clearing
    the cache makes the next download re-render them. Safe here because the
    feature is days old and no student's year or semester has moved since.
    """
    Certificate = apps.get_model('academic_procedures', 'BonafideCertificate')
    Certificate.objects.exclude(pdf_content=None).update(pdf_content=None)


class Migration(migrations.Migration):

    dependencies = [
        ('academic_procedures', '0054_merge_20260828_1758'),
    ]

    operations = [
        migrations.RunPython(clear_stored_pdfs, migrations.RunPython.noop),
    ]
