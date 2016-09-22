from django.test import TestCase

from users.models import PairProposal
from users.tests.factories import ProfileFactory
from users.views import ProfileContext


class TestProfileContext(TestCase):
    def test_has_proposed_to_friend(self):
        profile = ProfileFactory.create(active=True)
        friend = ProfileFactory.create(active=True)
        profile.friends.add(friend)
        ctx = ProfileContext(profile)
        self.assertFalse(ctx.has_proposed_to_friend(friend))
        PairProposal.objects.create(
            from_profile=profile, to_profile=friend)
        ctx = ProfileContext(profile)
        self.assertTrue(ctx.has_proposed_to_friend(friend))
