import mimetypes

from django.core.management.base import BaseCommand

from applications.programme_curriculum.models_student_management import (
    StudentBatchUpload,
    PhdStudentBatchUpload,
)


class Command(BaseCommand):
    help = (
        "Read existing on-disk photo/signature files into the DB blob columns "
        "so they are captured by pg_dump. Run once after deploying the change. "
        "Idempotent: skips records that already have a blob, and files missing "
        "on disk (those must be re-uploaded)."
    )

    def handle(self, *args, **opts):
        imported = 0
        already = 0
        # roll_number -> list of image kinds whose file is gone (must re-upload)
        missing = {}
        for model in (StudentBatchUpload, PhdStudentBatchUpload):
            for rec in model.objects.all():
                changed = False
                for kind in ("photo", "signature"):
                    if getattr(rec, kind + "_blob", None):
                        already += 1
                        continue
                    stored = getattr(rec, kind, None)
                    if not stored:
                        continue
                    try:
                        stored.open("rb")
                        data = stored.read()
                        stored.close()
                    except Exception:
                        missing.setdefault(rec.roll_number or "id:%s" % rec.pk, []).append(kind)
                        continue
                    mime = mimetypes.guess_type(stored.name)[0] or "image/jpeg"
                    setattr(rec, kind + "_blob", data)
                    setattr(rec, kind + "_mime", mime)
                    imported += 1
                    changed = True
                if changed:
                    rec.save(update_fields=[
                        "photo_blob", "photo_mime", "signature_blob", "signature_mime",
                    ])
        self.stdout.write(
            "Imported %d image(s) into DB; %d already had blobs; %d record(s) with a "
            "missing file (must re-upload)." % (imported, already, len(missing))
        )
        if missing:
            self.stdout.write("Records needing re-upload (roll_number: fields):")
            for roll in sorted(missing):
                self.stdout.write("  %s: %s" % (roll, ", ".join(missing[roll])))
