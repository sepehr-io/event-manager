from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from .models import User


class UserModelTests(TestCase):

    def test_default_role_is_attendee(self):
        user = User.objects.create_user("Rostam", "rostam@x.com", "pass12345")
        self.assertEqual(user.role, User.Role.ATTENDEE)
        self.assertFalse(user.can_create_events())

    def test_email_is_lowercased(self):
        user = User.objects.create_user("rostam", "Rostam@X.com", "pass12345")
        self.assertEqual(user.email, "rostam@x.com")

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user("rostam", "rostam@x.com", "pass12345")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user("sohrab", "Rostam@X.com", "pass12345")

    def test_upgrade_to_organizer(self):
        user = User.objects.create_user("rostam", "rostam@x.com", "pass12345")
        user.upgrade_to_organizer()
        user.refresh_from_db()
        self.assertEqual(user.role, User.Role.ORGANIZER)
        self.assertTrue(user.can_create_events())

    def test_upgrade_twice_fails(self):
        user = User.objects.create_user("rostam", "rostam@x.com", "pass12345")
        user.upgrade_to_organizer()
        with self.assertRaises(ValidationError):
            user.upgrade_to_organizer()

    def test_superuser_becomes_admin_and_staff(self):
        admin = User.objects.create_superuser("boss", "boss@x.com", "pass12345")
        self.assertEqual(admin.role, User.Role.ADMIN)
        self.assertTrue(admin.is_staff)