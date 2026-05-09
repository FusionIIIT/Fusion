from django.core.management.base import BaseCommand
from applications.health_center.models import Doctor


class Command(BaseCommand):
    help = 'Add 10 dummy doctors to the database for testing'

    def handle(self, *args, **options):
        dummy_doctors = [
            {
                'doctor_name': 'Rajesh Kumar',
                'doctor_phone': '9876543210',
                'email': 'rajesh.kumar@hospital.com',
                'specialization': 'General Medicine',
                'registration_number': 'MCI/2015/12345',
                'is_active': True,
            },
            {
                'doctor_name': 'Priya Sharma',
                'doctor_phone': '9876543211',
                'email': 'priya.sharma@hospital.com',
                'specialization': 'Pediatrics',
                'registration_number': 'MCI/2016/12346',
                'is_active': True,
            },
            {
                'doctor_name': 'Amit Patel',
                'doctor_phone': '9876543212',
                'email': 'amit.patel@hospital.com',
                'specialization': 'Surgery',
                'registration_number': 'MCI/2014/12347',
                'is_active': True,
            },
            {
                'doctor_name': 'Anjali Singh',
                'doctor_phone': '9876543213',
                'email': 'anjali.singh@hospital.com',
                'specialization': 'Gynecology',
                'registration_number': 'MCI/2017/12348',
                'is_active': True,
            },
            {
                'doctor_name': 'Vikram Reddy',
                'doctor_phone': '9876543214',
                'email': 'vikram.reddy@hospital.com',
                'specialization': 'Cardiology',
                'registration_number': 'MCI/2015/12349',
                'is_active': True,
            },
            {
                'doctor_name': 'Neha Gupta',
                'doctor_phone': '9876543215',
                'email': 'neha.gupta@hospital.com',
                'specialization': 'Dermatology',
                'registration_number': 'MCI/2016/12350',
                'is_active': True,
            },
            {
                'doctor_name': 'Sanjay Mishra',
                'doctor_phone': '9876543216',
                'email': 'sanjay.mishra@hospital.com',
                'specialization': 'Orthopedics',
                'registration_number': 'MCI/2015/12351',
                'is_active': True,
            },
            {
                'doctor_name': 'Deepa Verma',
                'doctor_phone': '9876543217',
                'email': 'deepa.verma@hospital.com',
                'specialization': 'Psychiatry',
                'registration_number': 'MCI/2017/12352',
                'is_active': True,
            },
            {
                'doctor_name': 'Rohan Joshi',
                'doctor_phone': '9876543218',
                'email': 'rohan.joshi@hospital.com',
                'specialization': 'Ophthalmology',
                'registration_number': 'MCI/2016/12353',
                'is_active': True,
            },
            {
                'doctor_name': 'Meera Nair',
                'doctor_phone': '9876543219',
                'email': 'meera.nair@hospital.com',
                'specialization': 'ENT',
                'registration_number': 'MCI/2018/12354',
                'is_active': True,
            },
        ]

        created_count = 0
        skipped_count = 0

        for doctor_data in dummy_doctors:
            doctor, created = Doctor.objects.get_or_create(
                doctor_name=doctor_data['doctor_name'],
                defaults=doctor_data,
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created: Dr. {doctor.doctor_name} - {doctor.specialization}'
                    )
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⊘ Already exists: Dr. {doctor.doctor_name}'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(
            self.style.SUCCESS(
                f'Summary: Created {created_count} doctors, Skipped {skipped_count} (already exist)'
            )
        )
        self.stdout.write(self.style.SUCCESS('='*60))
