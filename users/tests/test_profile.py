# -*- coding: utf-8 -*-
import base64
from django.contrib.auth import get_user_model
from django.utils import timezone

from users.models import PairProposal
from users.models import Profile
from users.tests import BaseUsersTest
from users.tests.factories import ProfileFactory


class TestProfile(BaseUsersTest):
    def test_profile_reason_emoji(self):
        reason = u"💩"
        reasonb64 = base64.b64encode(reason.encode('utf-8'))
        profile = ProfileFactory.create()
        profile.reason = reason
        profile.clean()
        profile.save()
        self.assertEqual(profile.reason, reasonb64)
        self.assertEqual(profile.reason_decoded, reason)
        profile = Profile.objects.get(id=profile.id)
        profile.clean()
        profile.save()
        self.assertEqual(profile.reason, reasonb64)
        self.assertEqual(profile.reason_decoded, reason)

    def test_profile_reason_encoding(self):
        reason = 'foobar'
        reasonb64 = base64.b64encode(reason.encode('utf-8'))
        profile = ProfileFactory.create(reason=reason)
        self.assertEqual(profile.reason, reasonb64)
        self.assertEqual(profile.reason_decoded, reason)
        profile = Profile.objects.get(id=profile.id)
        profile.clean()
        profile.save()
        self.assertEqual(profile.reason, reasonb64)
        self.assertEqual(profile.reason_decoded, reason)
        profile = Profile.objects.get(id=profile.id)
        profile.clean()
        profile.save()
        self.assertEqual(profile.reason, reasonb64)
        self.assertEqual(profile.reason_decoded, reason)

    def test_paired_with_property(self):
        user0 = self.users[0]
        user1 = self.users[1]
        user2 = self.users[2]
        self.assertFalse(user0.profile.paired_with)
        self.assertFalse(user1.profile.paired_with)
        user0.profile.paired_with = user1.profile
        self.assertEqual(user0.profile.paired_with, user1.profile)
        self.assertEqual(user1.profile.paired_with, user0.profile)
        # Ensure it saved
        user0 = get_user_model().objects.get(id=user0.id)
        self.assertEqual(user0.profile.paired_with, user1.profile)
        user0.profile.paired_with = user2.profile
        self.assertEqual(user0.profile.paired_with, user2.profile)

    def test_empty_preferred(self):
        """No Profiles created in BaseUsersTest w/o preferred candidate."""
        self.assertFalse(Profile.objects.filter(preferred_candidate=""))


class TestPairProposal(BaseUsersTest):
    def test_confirmed_qs(self):
        user0 = self.users[0]
        user1 = self.users[1]
        pair = PairProposal.objects.create(
            from_profile=user0.profile,
            to_profile=user1.profile,
        )
        self.assertFalse(PairProposal.objects.confirmed())
        pair.date_confirmed = timezone.now()
        pair.save()
        self.assertEqual(list(PairProposal.objects.confirmed()), [pair])
        self.assertEqual(list(PairProposal.objects.rejected()), [])
        pair.date_confirmed = None
        pair.date_rejected = timezone.now()
        pair.save()
        self.assertEqual(list(PairProposal.objects.confirmed()), [])
        self.assertEqual(list(PairProposal.objects.rejected()), [pair])

    def test_direction(self):
        user0 = self.users[0]
        user1 = self.users[1]
        pair = PairProposal.objects.create(
            from_profile=user0.profile,
            to_profile=user1.profile,
        )
        self.assertEqual(pair, pair)
        self.assertFalse(user1.profile.proposals_made.all())
        self.assertEqual(
            list(user1.profile.proposals_received.all()),
            list(user0.profile.proposals_made
                 .filter(to_profile=user1.profile)))
        self.assertEqual(
            list(user0.profile.proposals_made.all()),
            list(user1.profile.proposals_received
                 .filter(from_profile=user0.profile)))
        self.assertFalse(user0.profile.proposals_received.all())

        self.assertFalse(user1.profile.proposals_received.confirmed())
        self.assertFalse(user1.profile.proposals_received.rejected())
        self.assertTrue(user1.profile.proposals_received.pending())
        pair.date_confirmed = timezone.now()
        pair.save()
        self.assertEqual(list(PairProposal.objects.confirmed()), [pair])
        self.assertTrue(user1.profile.proposals_received.confirmed())
        self.assertFalse(user1.profile.proposals_received.rejected())
        self.assertFalse(user1.profile.proposals_received.pending())
