from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from users.tests.factories import UserFactory
from users.tests.factories import ProfileFactory


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
        # Ensure it saved
        user0 = get_user_model().objects.get(id=user0.id)
        self.assertEqual(user0.profile.paired_with, user1.profile)

    def test_profile_candidate_validation(self):
        profile = ProfileFactory.build()
        profile.preferred_candidate = profile.second_candidate
        self.assertRaises(ValidationError, profile.clean)
