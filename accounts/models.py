from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ATTENDEE = 'attendee', 'Attendee'
        ORGANIZER = 'organizer', 'Organizer'
        ADMIN = 'admin', 'Admin'

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.ATTENDEE
    )

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        if self.is_superuser:
            self.role = self.Role.ADMIN
        if self.role == self.Role.ADMIN:
            self.is_staff = True
        super().save(*args, **kwargs)

    def can_create_events(self):
        return self.role in (self.Role.ORGANIZER, self.Role.ADMIN)

    def upgrade_to_organizer(self):
        if self.role != self.Role.ATTENDEE:
            raise ValidationError('only attendees can become organizers')
        self.role = self.Role.ORGANIZER
        self.save(update_fields=['role'])