from django.core.management.base import BaseCommand

from applications.visitor_hostel.models import RoomDetail


class Command(BaseCommand):
    help = "Seed visitor hostel rooms for the availability workflow"

    def handle(self, *args, **options):
        room_groups = [
            {
                "prefix": "A",
                "room_type": "SingleBed",
                "room_floor": "GroundFloor",
                "count": 6,
            },
            {
                "prefix": "B",
                "room_type": "SingleBed",
                "room_floor": "FirstFloor",
                "count": 6,
            },
            {
                "prefix": "C",
                "room_type": "DoubleBed",
                "room_floor": "SecondFloor",
                "count": 6,
            },
            {
                "prefix": "D",
                "room_type": "VIP",
                "room_floor": "ThirdFloor",
                "count": 4,
            },
        ]

        created = 0
        updated = 0

        for group in room_groups:
            for index in range(1, group["count"] + 1):
                room_number = f"{group['prefix']}{index:02d}"
                room, was_created = RoomDetail.objects.update_or_create(
                    room_number=room_number,
                    defaults={
                        "room_type": group["room_type"],
                        "room_floor": group["room_floor"],
                        "room_status": "Available",
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded visitor hostel rooms: {created} created, {updated} updated"
            )
        )