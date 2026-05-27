from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.utils import timezone

from events.models import Category, Event, Registration


class Command(BaseCommand):
    help = "Seed database with sample event data"

    def handle(self, *args, **kwargs):
        try:
            user_model = get_user_model()

            organizer = user_model.objects.create_user(
                username="eventpro",
                email="organizer@test.com",
                password="TestPass123",
                role="organizer",
            )
            attendee = user_model.objects.create_user(
                username="johndoe",
                email="attendee@test.com",
                password="TestPass123",
                role="attendee",
            )

            category_data = [
                ("Technology", "#2563EB", "💻"),
                ("Business", "#F59E0B", "💼"),
                ("Arts & Culture", "#EC4899", "🎨"),
                ("Health & Wellness", "#10B981", "🧘"),
                ("Sports", "#EF4444", "⚽"),
            ]
            categories = {}
            for name, color_hex, icon_emoji in category_data:
                category = Category.objects.create(
                    name=name,
                    description=f"{name} events and experiences",
                    color_hex=color_hex,
                    icon_emoji=icon_emoji,
                )
                categories[name] = category

            now = timezone.now()
            events_payload = [
                {
                    "title": "AfriTech Summit 2025",
                    "description": "A continental summit on AI, cloud, and fintech innovation.",
                    "category": categories["Technology"],
                    "start_datetime": now + timedelta(days=30),
                    "end_datetime": now + timedelta(days=30, hours=8),
                    "venue_name": "KICC Main Hall",
                    "venue_address": "Harambee Avenue, Nairobi",
                    "city": "Nairobi",
                    "country": "Kenya",
                    "is_virtual": False,
                    "meeting_link": "",
                    "max_capacity": 500,
                    "ticket_price": Decimal("2500.00"),
                    "status": Event.STATUS_PUBLISHED,
                },
                {
                    "title": "Nairobi Startup Pitch Night",
                    "description": "Founders pitch to angel investors and VCs.",
                    "category": categories["Business"],
                    "start_datetime": now + timedelta(days=45),
                    "end_datetime": now + timedelta(days=45, hours=4),
                    "venue_name": "iHub Auditorium",
                    "venue_address": "Senteu Plaza, Nairobi",
                    "city": "Nairobi",
                    "country": "Kenya",
                    "is_virtual": False,
                    "meeting_link": "",
                    "max_capacity": 200,
                    "ticket_price": Decimal("500.00"),
                    "status": Event.STATUS_PUBLISHED,
                },
                {
                    "title": "Coastal Creatives Expo",
                    "description": "Showcase of visual arts, film, and design talent.",
                    "category": categories["Arts & Culture"],
                    "start_datetime": now + timedelta(days=60),
                    "end_datetime": now + timedelta(days=60, hours=6),
                    "venue_name": "Swahili Pot Hub",
                    "venue_address": "Moyne Drive, Mombasa",
                    "city": "Mombasa",
                    "country": "Kenya",
                    "is_virtual": False,
                    "meeting_link": "",
                    "max_capacity": 100,
                    "ticket_price": Decimal("1500.00"),
                    "status": Event.STATUS_PUBLISHED,
                },
                {
                    "title": "Virtual Wellness Bootcamp",
                    "description": "Online sessions on mental health, fitness, and nutrition.",
                    "category": categories["Health & Wellness"],
                    "start_datetime": now + timedelta(days=75),
                    "end_datetime": now + timedelta(days=75, hours=3),
                    "venue_name": "",
                    "venue_address": "",
                    "city": "Kisumu",
                    "country": "Kenya",
                    "is_virtual": True,
                    "meeting_link": "https://meet.example.com/wellness-bootcamp",
                    "max_capacity": 500,
                    "ticket_price": Decimal("0.00"),
                    "status": Event.STATUS_PUBLISHED,
                },
                {
                    "title": "Kisumu Marathon Prep Clinic",
                    "description": "Training clinic for marathon runners and coaches.",
                    "category": categories["Sports"],
                    "start_datetime": now + timedelta(days=90),
                    "end_datetime": now + timedelta(days=90, hours=2),
                    "venue_name": "Jomo Kenyatta Grounds",
                    "venue_address": "Kenyatta Sports Ground, Kisumu",
                    "city": "Kisumu",
                    "country": "Kenya",
                    "is_virtual": False,
                    "meeting_link": "",
                    "max_capacity": 50,
                    "ticket_price": Decimal("500.00"),
                    "status": Event.STATUS_DRAFT,
                },
                {
                    "title": "Mombasa Beach Fitness Festival",
                    "description": "Outdoor community wellness and sports activities.",
                    "category": categories["Health & Wellness"],
                    "start_datetime": now - timedelta(days=20),
                    "end_datetime": now - timedelta(days=20, hours=-5),
                    "venue_name": "Pirates Beach",
                    "venue_address": "Nyali Beach Road, Mombasa",
                    "city": "Mombasa",
                    "country": "Kenya",
                    "is_virtual": False,
                    "meeting_link": "",
                    "max_capacity": 100,
                    "ticket_price": Decimal("0.00"),
                    "status": Event.STATUS_CANCELLED,
                },
            ]

            created_events = []
            for payload in events_payload:
                event = Event.objects.create(organizer=organizer, **payload)
                created_events.append(event)

            Registration.objects.create(
                user=attendee,
                event=created_events[0],
                status=Registration.STATUS_CONFIRMED,
                notes="Excited for the keynote!",
            )
            Registration.objects.create(
                user=attendee,
                event=created_events[1],
                status=Registration.STATUS_CONFIRMED,
                notes="Will bring startup deck.",
            )
            second_attendee = user_model.objects.create_user(
                username="waitlisted_guest",
                email="waitlisted@test.com",
                password="TestPass123",
                role="attendee",
            )
            Registration.objects.create(
                user=second_attendee,
                event=created_events[0],
                status=Registration.STATUS_WAITLISTED,
                notes="Please notify me if a seat opens.",
            )

            self.stdout.write(self.style.SUCCESS("Seeded successfully!"))
            self.stdout.write("")
            self.stdout.write("Login Credentials")
            self.stdout.write("-" * 60)
            self.stdout.write(f"{'Role':<14}{'Username':<20}{'Email':<28}{'Password'}")
            self.stdout.write("-" * 60)
            self.stdout.write(
                f"{'Organizer':<14}{'eventpro':<20}{'organizer@test.com':<28}{'TestPass123'}"
            )
            self.stdout.write(
                f"{'Attendee':<14}{'johndoe':<20}{'attendee@test.com':<28}{'TestPass123'}"
            )
            self.stdout.write(
                f"{'Waitlisted':<14}{'waitlisted_guest':<20}{'waitlisted@test.com':<28}{'TestPass123'}"
            )
            self.stdout.write("-" * 60)
        except IntegrityError:
            self.stdout.write(self.style.WARNING("Data already exists, skipping"))
