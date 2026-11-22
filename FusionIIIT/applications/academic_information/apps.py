from django.apps import AppConfig


class AcademicInformationConfig(AppConfig):
    name = 'applications.academic_information'

    def ready(self):
        # Locked (alumni, withdrawn, ...) students' records cannot be changed.
        from applications.academic_information.student_lock import connect_student_lock
        connect_student_lock()
