from django.db import models
import uuid
from decimal import ROUND_HALF_UP, Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone


class Registration(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = 'confirmed', 'Confirmed'
        WAITLISTED = 'waitlisted', 'Waitlisted'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='registrations',
    )
    event = models.ForeignKey(
        'events.Event', on_delete=models.PROTECT, related_name='registrations'
    )
    status = models.CharField(max_length=20, choices=Status.choices)
    discount_percent = models.PositiveSmallIntegerField(
        default=0, validators=[MaxValueValidator(100)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']
        indexes = [models.Index(fields=['event', 'status', 'created_at'])]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'event'], name='unique_registration_per_user_event'
            )
        ]

    def __str__(self):
        return f'{self.user} -> {self.event} [{self.status}]'

    def confirm(self):
        self.status = self.Status.CONFIRMED
        self.save(update_fields=['status'])

    def cancel(self):
        if self.status == self.Status.CANCELLED:
            raise ValidationError('registration already cancelled')
        if self.event.start_at <= timezone.now():
            raise ValidationError('Cant cancel after the event has started')
        self.status = self.Status.CANCELLED
        self.cancelled_at = timezone.now()
        self.save(update_fields=['status', 'cancelled_at'])

    @property
    def price_paid(self):
        factor = Decimal(100 - self.discount_percent) / Decimal(100)
        return (self.event.price * factor).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )


def generate_ticket_code():
    return uuid.uuid4().hex


class Ticket(models.Model):
    registration = models.OneToOneField(
        Registration, on_delete=models.CASCADE, related_name='ticket'
    )
    code = models.CharField(
        max_length=32, unique=True, default=generate_ticket_code, editable=False
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.code

    @property
    def is_checked_in(self):
        return self.checked_in_at is not None

    def check_in(self):
        if self.registration.status != Registration.Status.CONFIRMED:
            raise ValidationError('Ticket belongs to an inactive registration')
        if self.is_checked_in:
            raise ValidationError('Ticket has already been used')
        self.checked_in_at = timezone.now()
        self.save(update_fields=['checked_in_at'])