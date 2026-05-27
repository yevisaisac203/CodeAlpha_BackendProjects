from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    color_hex = models.CharField(max_length=7, blank=True)
    icon_emoji = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class EventTag(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Event(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CANCELLED = "cancelled"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_COMPLETED, "Completed"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=220, blank=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_events",
    )
    banner_image = models.ImageField(upload_to="events/banners/", null=True, blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    venue_name = models.CharField(max_length=200, blank=True)
    venue_address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="Kenya")
    is_virtual = models.BooleanField(default=False)
    meeting_link = models.URLField(blank=True)
    max_capacity = models.PositiveIntegerField(default=100)
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    tags = models.ManyToManyField(EventTag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_free(self):
        return self.ticket_price == 0

    @property
    def available_spots(self):
        confirmed_count = self.registrations.filter(
            status=Registration.STATUS_CONFIRMED
        ).count()
        return self.max_capacity - confirmed_count

    @property
    def is_full(self):
        return self.available_spots <= 0

    def save(self, *args, **kwargs):
        if self.pk is None:
            super().save(*args, **kwargs)
            if not self.slug:
                self.slug = slugify(f"{self.title}-{str(self.id)[:8]}")
                super().save(update_fields=["slug"])
            return

        if not self.slug:
            self.slug = slugify(f"{self.title}-{str(self.id)[:8]}")
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-start_datetime"]


class Registration(models.Model):
    STATUS_CONFIRMED = "confirmed"
    STATUS_WAITLISTED = "waitlisted"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_WAITLISTED, "Waitlisted"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    registered_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CONFIRMED)
    ticket_code = models.CharField(max_length=50, unique=True, editable=False)
    check_in_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.ticket_code:
            token = str(uuid4()).replace("-", "")[:8].upper()
            self.ticket_code = f"EVT-{self.event_id}-{token}"
        super().save(*args, **kwargs)

    class Meta:
        unique_together = [("user", "event")]
        ordering = ["-registered_at"]
