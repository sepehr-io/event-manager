from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from registrations.models import Registration


class Review(models.Model):
    registration = models.OneToOneField(
        Registration, on_delete=models.CASCADE, related_name="review"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=Q(rating__gte=1) & Q(rating__lte=5),
                name='review_rating_between_1_and_5',
            )
        ]

    def __str__(self):
        return f'{self.registration} - {self.rating}/5'

    def clean(self):
        reg = self.registration
        if reg.status != Registration.Status.CONFIRMED:
            raise ValidationError('only confirmed registrations can be reviewed')
        if not reg.event.has_ended():
            raise ValidationError('you can review an event only after it ends')