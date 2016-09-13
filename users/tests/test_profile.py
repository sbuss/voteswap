from django.test import TestCase

from users.models import Profile
from users.tests.factories import UserFactory


class TestProfile(TestCase):
    def setUp(self):
        self.users = [UserFactory.create() for x in range(10)]

    def test_paired_with_property(self):
        user0 = self.users[0]
        user1 = self.users[1]
        self.assertFalse(user0.profile.paired_with)
        self.assertFalse(user1.profile.paired_with)
        user0.profile.paired_with = user1.profile
        self.assertEqual(user0.profile.paired_with, user1.profile)
        self.assertEqual(user1.profile.paired_with, user0.profile)
