from django.test import TestCase

from polling.models import CANDIDATE_CLINTON
from polling.models import CANDIDATE_JOHNSON
from polling.tests.factories import StateFactory
from users.models import PairProposal
from users.tests.factories import ProfileFactory
from users.tests.factories import UserFactory
from users.views import ProfileContext


class TestProfileContext(TestCase):
    def test_has_proposed_to_friend(self):
        profile = ProfileFactory.create()
        friend = ProfileFactory.create()
        profile.friends.add(friend)
        ctx = ProfileContext(profile)
        self.assertFalse(ctx.has_proposed_to_friend(friend))
        PairProposal.objects.create(
            from_profile=profile, to_profile=friend)
        ctx = ProfileContext(profile)
        self.assertTrue(ctx.has_proposed_to_friend(friend))

    def test_swing_match(self):
        swing_state = StateFactory.create(tipping_point_rank=1)
        safe_state = StateFactory.create(safe_rank=1)
        # The logged in user is in a swing state, their match in a safe state
        user = UserFactory.create(
            profile__state=swing_state.name,
            profile__preferred_candidate=CANDIDATE_JOHNSON)
        friend = UserFactory.create(
            profile__state=safe_state.name,
            profile__preferred_candidate=CANDIDATE_CLINTON)
        user.profile.friends.add(friend.profile)
        profile_ctx = ProfileContext(user.profile)
        [friend_context] = profile_ctx.good_potential_matches
        self.assertTrue(
            "Will vote for %s in %s" % (CANDIDATE_JOHNSON, safe_state.name)
            in friend_context.proposal_string)
        self.assertTrue(
            "your vote for %s in %s" % (CANDIDATE_CLINTON, swing_state.name)
            in friend_context.proposal_string)

    def test_safe_match(self):
        swing_state = StateFactory.create(tipping_point_rank=1)
        safe_state = StateFactory.create(safe_rank=1)
        # The logged in user is in a safe state, their match in a swing state
        friend = UserFactory.create(
            profile__state=swing_state.name,
            profile__preferred_candidate=CANDIDATE_JOHNSON)
        user = UserFactory.create(
            profile__state=safe_state.name,
            profile__preferred_candidate=CANDIDATE_CLINTON)
        user.profile.friends.add(friend.profile)
        profile_ctx = ProfileContext(user.profile)
        [friend_context] = profile_ctx.good_potential_matches
        self.assertTrue(
            "Will vote for %s in %s" % (CANDIDATE_CLINTON, swing_state.name)
            in friend_context.proposal_string)
        self.assertTrue(
            "your vote for %s in %s" % (CANDIDATE_JOHNSON, safe_state.name)
            in friend_context.proposal_string)
