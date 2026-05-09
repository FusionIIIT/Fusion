from django.core.management.base import BaseCommand
from applications.health_center.models import Stock, Expiry
from datetime import datetime, timedelta
import random


class Command(BaseCommand):
    help = 'Create 10 dummy batch entries for testing'

    def handle(self, *args, **options):
        """Create dummy batches"""
        stocks = Stock.objects.all()
        self.stdout.write(f"Found {stocks.count()} medicines in stock")

        if stocks.count() == 0:
            self.stdout.write(self.style.ERROR("❌ No medicines found! Please add medicines first."))
            return

        batches_created = []
        for i in range(10):
            stock = stocks[i % stocks.count()]
            batch_no = f"BATCH-HC-2024-{1000+i}"
            qty = random.randint(50, 200)
            
            # Create expired and active batches
            if i < 5:
                expiry_date = (datetime.now().date() - timedelta(days=30+i*10))
            else:
                expiry_date = (datetime.now().date() + timedelta(days=60+(i-5)*15))
            
            try:
                expiry = Expiry.objects.create(
                    stock=stock,
                    batch_no=batch_no,
                    qty=qty,
                    expiry_date=expiry_date,
                    is_returned=False,
                    returned_qty=0
                )
                batches_created.append(expiry)
                
                # Update stock total quantity
                stock.total_qty += qty
                stock.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Created: {stock.medicine.medicine_name} - {batch_no} - {qty}u - Exp: {expiry_date}"
                    )
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error creating batch: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Successfully created {len(batches_created)} batch entries!"))
        
        # Summary
        expired_count = Expiry.objects.filter(expiry_date__lt=datetime.now().date()).count()
        active_count = Expiry.objects.filter(expiry_date__gte=datetime.now().date()).count()
        
        self.stdout.write(f"\nBatch Summary:")
        self.stdout.write(f"  - Expired batches: {expired_count}")
        self.stdout.write(f"  - Active batches: {active_count}")
        self.stdout.write(f"  - Total batches: {Expiry.objects.count()}")
