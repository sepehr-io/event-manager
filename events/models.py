from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, allow_unicode=True, blank=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Event(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        CANCELLED = 'cancelled', 'Cancelled'
        FINISHED = 'finished', 'Finished'

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='organized_events',
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='events'
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, allow_unicode=True, blank=True)
    description = models.TextField()
    location = models.CharField(max_length=255)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    capacity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    banner = models.ImageField(upload_to='events/banners/', blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_at']
        indexes = [models.Index(fields=['status', 'start_at'])]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_at__gt=F('start_at')),
                name='event_end_after_start',
            ),
            models.CheckConstraint(
                condition=Q(capacity__gte=1),
                name='event_capacity_at_least_one',
            ),
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name='event_price_not_negative',
            ),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            raise ValidationError({'end_at': 'end time must be after start time'})
        if self.pk:
            old = Event.objects.filter(pk=self.pk).values('price').first()
            if old and old['price'] != self.price and self.registrations.exists():
                raise ValidationError(
                    {'price': 'price cannot change after the first registration'}
                )
        if self.organizer_id and not self.organizer.can_create_events():
            raise ValidationError({'organizer': 'this user cannot organize events'})

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=True) or 'event'
            slug, n = base, 2
            while Event.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def confirmed_count(self):
        from registrations.models import Registration

        return self.registrations.filter(
            status=Registration.Status.CONFIRMED
        ).count()

    def seats_left(self):
        return max(self.capacity - self.confirmed_count(), 0)

    def is_full(self):
        return self.seats_left() == 0

    def is_open_for_registration(self):
        return self.status == self.Status.PUBLISHED and self.start_at > timezone.now()

    def has_ended(self):
        return self.end_at <= timezone.now()

    def publish(self):
        if self.status != self.Status.DRAFT:
            raise ValidationError('only draft events can be published')
        self.status = self.Status.PUBLISHED
        self.save(update_fields=['status'])

    def cancel(self):
        if self.status in (self.Status.CANCELLED, self.Status.FINISHED):
            raise ValidationError('this event cant no longer be cancelled')
        self.status = self.Status.CANCELLED
        self.save(update_fields=['status'])


class DiscountCode(models.Model):
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name='discount_codes'
    )
    code = models.CharField(max_length=50)
    percent = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    max_uses = models.PositiveIntegerField()
    used_count = models.PositiveIntegerField(default=0)
    valid_until = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'code'], name='unique_code_per_event'
            )
        ]

    def __str__(self):
        return f'{self.code} ({self.percent}%)'

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def is_valid(self):
        return self.used_count < self.max_uses and self.valid_until > timezone.now()

    def redeem(self):
        """atomically consume one use. Returns False if the code is mexed.
        call inside the same transaction as the registration
        """
        updated = DiscountCode.objects.filter(
            pk=self.pk,
            used_count__lt=F('max_uses'),
            valid_until__gt=timezone.now(),
        ).update(used_count=F('used_count') + 1)
        return updated == 1