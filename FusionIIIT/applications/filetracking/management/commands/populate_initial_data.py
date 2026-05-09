from django.core.management.base import BaseCommand
from applications.filetracking.models import FileType, FileWorkflow
from applications.globals.models import Designation, DepartmentInfo


class Command(BaseCommand):
    help = 'Populate initial data for comprehensive FTS system'

    def _resolve_designation(self, *exact_names, contains_tokens=None):
        """Resolve designation by flexible matching against existing DB values."""
        for name in exact_names:
            if not name:
                continue
            match = Designation.objects.filter(name__iexact=name).first()
            if match:
                return match

        for name in exact_names:
            if not name:
                continue
            match = Designation.objects.filter(name__icontains=name).order_by('name').first()
            if match:
                return match

        for token in contains_tokens or []:
            match = Designation.objects.filter(name__icontains=token).order_by('name').first()
            if match:
                return match

        return None

    def handle(self, *args, **options):
        self.stdout.write('Populating initial file types...')

        # Keep test-only E2E file types hidden from regular users.
        disabled_count = FileType.objects.filter(name__startswith='E2E_', is_active=True).update(is_active=False)
        if disabled_count:
            self.stdout.write(f'Deactivated {disabled_count} E2E test file type(s)')

        # Create file types
        file_types_data = [
            {
                'name': 'Academic Document',
                'category': 'ACADEMIC',
                'description': 'Documents related to academic procedures',
                'requires_attachments': True,
            },
            {
                'name': 'Administrative Request',
                'category': 'ADMINISTRATIVE',
                'description': 'General administrative requests',
                'requires_attachments': False,
            },
            {
                'name': 'Financial Request',
                'category': 'FINANCIAL',
                'description': 'Financial and budget related requests',
                'requires_attachments': True,
            },
            {
                'name': 'HR Request',
                'category': 'HR',
                'description': 'Human resources related requests',
                'requires_attachments': False,
            },
            {
                'name': 'Infrastructure Request',
                'category': 'ESTABLISHMENT',
                'description': 'Infrastructure and maintenance requests',
                'requires_attachments': True,
            },
            {
                'name': 'Student Complaint',
                'category': 'STUDENT',
                'description': 'Student related complaints and requests',
                'requires_attachments': False,
            },
            {
                'name': 'Research Proposal',
                'category': 'RESEARCH',
                'description': 'Research related documents and proposals',
                'requires_attachments': True,
            },
            {
                'name': 'Event Request',
                'category': 'OTHER',
                'description': 'Event organization and permission requests',
                'requires_attachments': True,
            },
        ]

        for ft_data in file_types_data:
            file_type, created = FileType.objects.update_or_create(
                name=ft_data['name'],
                defaults=ft_data,
            )
            if created:
                self.stdout.write(f'Created file type: {file_type.name}')
            else:
                self.stdout.write(f'File type updated: {file_type.name}')

        # Create workflow configurations for file types
        self.stdout.write('Setting up workflow configurations...')

        # Get designations
        designations = {
            'student': self._resolve_designation('student', contains_tokens=['student']),
            'staff': self._resolve_designation('staff', 'office_staff', contains_tokens=['staff', 'assistant']),
            'faculty': self._resolve_designation(
                'faculty',
                'Assistant Professor',
                'Associate Professor',
                'Professor',
                contains_tokens=['professor', 'faculty'],
            ),
            'hod': self._resolve_designation('hod', contains_tokens=['hod']),
            'dean': self._resolve_designation('dean', 'Dean Academic', contains_tokens=['dean']),
            'director': self._resolve_designation('director', 'Director', contains_tokens=['director']),
        }

        admin_department, _ = DepartmentInfo.objects.get_or_create(name='Administration')

        # Academic Document workflow: student -> faculty -> hod -> dean
        academic_doc = FileType.objects.filter(name='Academic Document').first()
        if academic_doc:
            stage_one_designations = []
            for candidate in [
                self._resolve_designation('Assistant Professor', contains_tokens=['assistant professor']),
                self._resolve_designation('Associate Professor', contains_tokens=['associate professor']),
                self._resolve_designation('Professor', contains_tokens=['professor']),
                designations.get('staff'),
            ]:
                if candidate and candidate.id not in {d.id for d in stage_one_designations}:
                    stage_one_designations.append(candidate)

            for designation in stage_one_designations:
                FileWorkflow.objects.update_or_create(
                    file_type=academic_doc,
                    step_order=1,
                    designation=designation,
                    department=None,
                    defaults={
                        'action_required': 'REVIEW',
                        'max_days': 3,
                        'is_mandatory': True,
                    },
                )

            for order, designation_name, action in [
                (2, 'hod', 'APPROVE'),
                (3, 'dean', 'FINAL_APPROVE'),
            ]:
                designation = designations.get(designation_name)
                if designation:
                    FileWorkflow.objects.update_or_create(
                        file_type=academic_doc,
                        step_order=order,
                        designation=designation,
                        department=None,
                        defaults={
                            'action_required': action,
                            'max_days': 3,
                            'is_mandatory': True,
                        },
                    )

        # Administrative Request workflow: staff -> hod -> director
        admin_req = FileType.objects.filter(name='Administrative Request').first()
        if admin_req:
            for order, designation_name, action in [
                (1, 'hod', 'APPROVE'),
                (2, 'director', 'FINAL_APPROVE'),
            ]:
                designation = designations.get(designation_name)
                if designation:
                    FileWorkflow.objects.update_or_create(
                        file_type=admin_req,
                        step_order=order,
                        designation=designation,
                        department=None,
                        defaults={
                            'action_required': action,
                            'max_days': 3,
                            'is_mandatory': True,
                        },
                    )

        # Financial Request workflow: staff -> hod -> finance -> director
        finance_req = FileType.objects.filter(name='Financial Request').first()
        if finance_req:
            for order, designation_name, action in [
                (1, 'hod', 'REVIEW'),
                (2, 'staff', 'APPROVE'),
                (3, 'director', 'FINAL_APPROVE'),
            ]:
                designation = designations.get(designation_name)
                if designation:
                    FileWorkflow.objects.update_or_create(
                        file_type=finance_req,
                        step_order=order,
                        designation=designation,
                        department=None,
                        defaults={
                            'action_required': action,
                            'max_days': 3,
                            'is_mandatory': True,
                        },
                    )

        # Student Complaint workflow: student -> staff (administration)
        student_complaint = FileType.objects.filter(name='Student Complaint').first()
        if student_complaint and designations.get('staff'):
            FileWorkflow.objects.update_or_create(
                file_type=student_complaint,
                step_order=1,
                designation=designations['staff'],
                department=admin_department,
                defaults={
                    'action_required': 'REVIEW',
                    'max_days': 3,
                    'is_mandatory': True,
                },
            )

        # Infrastructure Request workflow: staff (administration)
        infrastructure_req = FileType.objects.filter(name='Infrastructure Request').first()
        if infrastructure_req and designations.get('staff'):
            FileWorkflow.objects.update_or_create(
                file_type=infrastructure_req,
                step_order=1,
                designation=designations['staff'],
                department=admin_department,
                defaults={
                    'action_required': 'REVIEW',
                    'max_days': 3,
                    'is_mandatory': True,
                },
            )

        # HR Request workflow: staff (administration)
        hr_req = FileType.objects.filter(name='HR Request').first()
        if hr_req and designations.get('staff'):
            FileWorkflow.objects.update_or_create(
                file_type=hr_req,
                step_order=1,
                designation=designations['staff'],
                department=admin_department,
                defaults={
                    'action_required': 'REVIEW',
                    'max_days': 3,
                    'is_mandatory': True,
                },
            )

        # Research Proposal workflow: faculty (source department)
        research_prop = FileType.objects.filter(name='Research Proposal').first()
        if research_prop and designations.get('faculty'):
            FileWorkflow.objects.update_or_create(
                file_type=research_prop,
                step_order=1,
                designation=designations['faculty'],
                department=None,
                defaults={
                    'action_required': 'REVIEW',
                    'max_days': 3,
                    'is_mandatory': True,
                },
            )

        # Event Request workflow: staff (administration)
        event_req = FileType.objects.filter(name='Event Request').first()
        if event_req and designations.get('staff'):
            FileWorkflow.objects.update_or_create(
                file_type=event_req,
                step_order=1,
                designation=designations['staff'],
                department=admin_department,
                defaults={
                    'action_required': 'REVIEW',
                    'max_days': 3,
                    'is_mandatory': True,
                },
            )

        self.stdout.write(self.style.SUCCESS('Initial data populated successfully!'))