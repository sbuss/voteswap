from datetime import datetime
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import F

from users.models import PairProposal
from users.models import Profile
from users.tests import BaseUsersTest
from users.tests.factories import ProfileFactory


class TestProfile(BaseUsersTest):
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

    def test_empty_preferred(self):
        self.assertFalse(Profile.objects.filter(preferred_candidate=""))

    def test_empty_second(self):
        self.assertFalse(Profile.objects.filter(second_candidate=""))

    def test_equal_candidates(self):
        self.assertFalse(Profile.objects.filter(
            preferred_candidate=F('second_candidate')))


class TestPairProposal(BaseUsersTest):
    def test_confirmed_qs(self):
        user0 = self.users[0]
        user1 = self.users[1]
        pair = PairProposal.objects.create(
            from_profile=user0.profile,
            to_profile=user1.profile)
        self.assertFalse(PairProposal.objects.confirmed())
        pair.date_confirmed = datetime.now()
        pair.save()
        self.assertEqual(list(PairProposal.objects.confirmed()), [pair])
        self.assertEqual(list(PairProposal.objects.rejected()), [])
        pair.date_confirmed = None
        pair.date_rejected = datetime.now()
        pair.save()
        self.assertEqual(list(PairProposal.objects.confirmed()), [])
        self.assertEqual(list(PairProposal.objects.rejected()), [pair])
