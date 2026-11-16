from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from accounts.models import User
from .models import Category, Event, DiscountCode

def make_user(username='u1', role=User.Role.ATTENDEE):
    user = User.objects.filter(username=username).first()

    if user:
        return user

    return User.objects.create_user(username, f'{username}@x.com', 'pass12345', role=role)

def make_event(organizer=None, capacity=2, price=Decimal('100.00'), status=Event.Status.PUBLISHED, starts_in_days=7,):
    organizer = organizer or make_user('org', User.Role.ORGANIZER)
    category, _ = Category.objects.get_or_create(name='Workshop')
    start = timezone.now() + timedelta(days=starts_in_days)


    return Event.objects.create(
        organizer=organizer,
        category=category,
        title='Django Workshop',
        description='Hands-on session',
        location='Room 101',
        start_at=start,
        end_at=start + timedelta(hours=2),
        capacity=capacity,
        price=price,
        status=status,
    )


def make_code(**kwargs):
    defaults = dict(
        event=make_event(),
        code='save20',
        percent=20,
        max_uses=2,
        valid_until=timezone.now() + timedelta(days=1),
    )
    defaults.update(kwargs)
    return DiscountCode.objects.create(**defaults)