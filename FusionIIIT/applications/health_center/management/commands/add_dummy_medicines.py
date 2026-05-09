from django.core.management.base import BaseCommand
from applications.health_center.models import Medicine


class Command(BaseCommand):
    help = 'Add 10 dummy medicines to the database for testing'

    def handle(self, *args, **options):
        dummy_medicines = [
            {
                'medicine_name': 'Aspirin',
                'brand_name': 'Bayer Aspirin',
                'generic_name': 'Acetylsalicylic Acid',
                'manufacturer_name': 'Bayer AG',
                'pack_size_label': '500mg',
                'unit': 'tablets',
                'reorder_threshold': 20,
            },
            {
                'medicine_name': 'Paracetamol',
                'brand_name': 'Calpol',
                'generic_name': 'Acetaminophen',
                'manufacturer_name': 'Ranbaxy Labs',
                'pack_size_label': '500mg',
                'unit': 'tablets',
                'reorder_threshold': 25,
            },
            {
                'medicine_name': 'Ibuprofen',
                'brand_name': 'Brufen',
                'generic_name': 'Ibuprofen',
                'manufacturer_name': 'Abbott',
                'pack_size_label': '400mg',
                'unit': 'tablets',
                'reorder_threshold': 20,
            },
            {
                'medicine_name': 'Amoxicillin',
                'brand_name': 'Augmentin',
                'generic_name': 'Amoxicillin Trihydrate',
                'manufacturer_name': 'GSK',
                'pack_size_label': '500mg',
                'unit': 'capsules',
                'reorder_threshold': 15,
            },
            {
                'medicine_name': 'Ciprofloxacin',
                'brand_name': 'Ciprobid',
                'generic_name': 'Ciprofloxacin Hydrochloride',
                'manufacturer_name': 'Cipla',
                'pack_size_label': '500mg',
                'unit': 'tablets',
                'reorder_threshold': 12,
            },
            {
                'medicine_name': 'Metformin',
                'brand_name': 'Glucophage',
                'generic_name': 'Metformin Hydrochloride',
                'manufacturer_name': 'Merck',
                'pack_size_label': '500mg',
                'unit': 'tablets',
                'reorder_threshold': 30,
            },
            {
                'medicine_name': 'Atorvastatin',
                'brand_name': 'Lipitor',
                'generic_name': 'Atorvastatin Calcium',
                'manufacturer_name': 'Pfizer',
                'pack_size_label': '20mg',
                'unit': 'tablets',
                'reorder_threshold': 15,
            },
            {
                'medicine_name': 'Omeprazole',
                'brand_name': 'Prilosec',
                'generic_name': 'Omeprazole',
                'manufacturer_name': 'AstraZeneca',
                'pack_size_label': '20mg',
                'unit': 'capsules',
                'reorder_threshold': 18,
            },
            {
                'medicine_name': 'Lisinopril',
                'brand_name': 'Prinivil',
                'generic_name': 'Lisinopril Dihydrate',
                'manufacturer_name': 'Merck',
                'pack_size_label': '10mg',
                'unit': 'tablets',
                'reorder_threshold': 14,
            },
            {
                'medicine_name': 'Clopidogrel',
                'brand_name': 'Plavix',
                'generic_name': 'Clopidogrel Bisulfate',
                'manufacturer_name': 'Sanofi',
                'pack_size_label': '75mg',
                'unit': 'tablets',
                'reorder_threshold': 10,
            },
        ]

        created_count = 0
        skipped_count = 0

        for medicine_data in dummy_medicines:
            medicine, created = Medicine.objects.get_or_create(
                medicine_name=medicine_data['medicine_name'],
                defaults=medicine_data,
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created: {medicine.medicine_name} ({medicine.brand_name})'
                    )
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⊘ Already exists: {medicine.medicine_name}'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(
            self.style.SUCCESS(
                f'Summary: Created {created_count} medicines, Skipped {skipped_count} (already exist)'
            )
        )
        self.stdout.write(self.style.SUCCESS('='*60))
