from django.test import TestCase
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from .factory import make_event, make_user, make_code
from .models import DiscountCode, Event


class EventTests(TestCase):
    def test_end_must_be_after_start(self):
        event = make_event()
        event.end_at = event.start_at - timedelta(hours=1)
        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_database_rejects_bad_dates(self):
        event = make_event()
        event.end_at = event.start_at - timedelta(hours=1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                event.save()

    def test_zero_capacity_rejected_by_database(self):
        event = make_event()
        event.capacity = 0
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                event.save()

    def test_attendee_cannot_organize_events(self):
        event = make_event()
        event.organizer = make_user('attndeee')
        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_slugs_are_unique(self):
        e1 = make_event()
        e2 = make_event(organizer=e1.organizer)
        self.assertNotEqual(e1.slug, e2.slug)

    def test_publish_only_from_draft(self):
        event = make_event(status=Event.Status.DRAFT)
        event.publish()
        self.assertEqual(event.status, Event.Status.PUBLISHED)
        with self.assertRaises(ValidationError):
            event.publish()

    def test_cancel(self):
        event = make_event()
        event.cancel()
        self.assertEqual(event.status, Event.Status.CANCELLED)
        with self.assertRaises(ValidationError):
            event.cancel()

    def test_event_open_for_registration(self):
        # if it is open
        self.assertTrue(make_event().is_open_for_registration())
        # if it is draafted
        draft = make_event(status=Event.Status.DRAFT)
        self.assertFalse(draft.is_open_for_registration())
        #if it is ended
        started = make_event(starts_in_days=-1)
        self.assertFalse(started.is_open_for_registration())


class DiscountCodeTests(TestCase):
    def test_code_is_normalized(self):
        self.assertEqual(make_code().code, 'SAVE20')

    def test_redeem_until_exhausted(self):
        code = make_code(max_uses=1)
        self.assertTrue(code.redeem())
        self.assertFalse(code.redeem())
        code.refresh_from_db()
        self.assertEqual(code.used_count, 1)
        self.assertFalse(code.is_valid())

    def test_expired_code(self):
        code = make_code(valid_until=timezone.now() - timedelta(minutes=1))
        self.assertFalse(code.is_valid())
        self.assertFalse(code.redeem())

    def test_unique_per_event(self):
        code = make_code(code='REPEAT2')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                DiscountCode.objects.create(
                    event=code.event,
                    code='REPEAT2',
                    percent=5,
                    max_uses=1,
                    valid_until=code.valid_until,
                )