from django.test import TestCase

from polling.models import CANDIDATE_CLINTON
from polling.models import CANDIDATE_JOHNSON
from polling.models import CANDIDATE_TRUMP
from polling.tests.factories import StateFactory
from users.models import PairProposal
from users.tests.factories import ProfileFactory
from users.tests.factories import UserFactory
from users.views import ProfileContext


class TestProfileContext(TestCase):
    def setUp(self):
        self.swing_state = StateFactory.create(tipping_point_rank=1)
        self.safe_state = StateFactory.create(safe_rank=1)

    def test_has_proposed_to_friend(self):
        profile = ProfileFactory.create(state=self.swing_state.name)
        friend = ProfileFactory.create(state=self.safe_state.name)
        profile.friends.add(friend)
        ctx = ProfileContext(profile)
        self.assertFalse(ctx.has_proposed_to_friend(friend))
        PairProposal.objects.create(
            from_profile=profile, to_profile=friend)
        ctx = ProfileContext(profile)
        self.assertTrue(ctx.has_proposed_to_friend(friend))

    def test_swing_match(self):
        # The logged in user is in a swing state, their match in a safe state
        user = UserFactory.create(
            profile__state=self.swing_state.name,
            profile__preferred_candidate=CANDIDATE_JOHNSON)
        friend = UserFactory.create(
            profile__state=self.safe_state.name,
            profile__preferred_candidate=CANDIDATE_CLINTON)
        user.profile.friends.add(friend.profile)
        profile_ctx = ProfileContext(user.profile)
        [friend_context] = profile_ctx.good_potential_matches
        self.assertTrue(
            "Will vote for %s in %s" % (
                CANDIDATE_JOHNSON, self.safe_state.name)
            in friend_context.proposal_string)
        self.assertTrue(
            "your vote for %s in %s" % (
                CANDIDATE_CLINTON, self.swing_state.name)
            in friend_context.proposal_string)

    def test_safe_match(self):
        # The logged in user is in a safe state, their match in a swing state
        friend = UserFactory.create(
            profile__state=self.swing_state.name,
            profile__preferred_candidate=CANDIDATE_JOHNSON)
        user = UserFactory.create(
            profile__state=self.safe_state.name,
            profile__preferred_candidate=CANDIDATE_CLINTON)
        user.profile.friends.add(friend.profile)
        profile_ctx = ProfileContext(user.profile)
        [friend_context] = profile_ctx.good_potential_matches
        self.assertTrue(
            "Will vote for %s in %s" % (
                CANDIDATE_CLINTON, self.swing_state.name)
            in friend_context.proposal_string)
        self.assertTrue(
            "your vote for %s in %s" % (
                CANDIDATE_JOHNSON, self.safe_state.name)
            in friend_context.proposal_string)


class TestProfileContextStates(TestCase):
    def setUp(self):
        super(TestProfileContextStates, self).setUp()
        self.safe_clinton = StateFactory.create(
            safe_rank=1,
            safe_for=CANDIDATE_CLINTON)
        self.lean_clinton = StateFactory.create(
            lean_rank=1,
            leans=CANDIDATE_CLINTON)
        self.lean_trump = StateFactory.create(
            lean_rank=1,
            leans=CANDIDATE_TRUMP)
        self.safe_trump = StateFactory.create(
            safe_rank=1,
            safe_for=CANDIDATE_TRUMP)

    def test_clinton_in_safe_clinton(self):
        user = UserFactory(
            profile__preferred_candidate=CANDIDATE_CLINTON,
            profile__state=self.safe_clinton.name)
        ctx = ProfileContext(user.profile)
        self.assertTrue(ctx.needs_match)
        self.assertFalse(ctx.kingmaker)
        self.assertFalse(ctx.johnson)

    def test_clinton_in_leans_clinton(self):
        user = UserFactory(
            profile__preferred_candidate=CANDIDATE_CLINTON,
            profile__state=self.lean_clinton.name)
        ctx = ProfileContext(user.profile)
        self.assertFalse(ctx.needs_match)
        self.assertFalse(ctx.kingmaker)
        self.assertFalse(ctx.johnson)

    def test_clinton_in_leans_trump(self):
        user = UserFactory(
            profile__preferred_candidate=CANDIDATE_CLINTON,
            profile__state=self.lean_trump.name)
        ctx = ProfileContext(user.profile)
        self.assertFalse(ctx.needs_match)
        self.assertFalse(ctx.kingmaker)
        self.assertFalse(ctx.johnson)

    def test_clinton_in_safe_trump(self):
        user = UserFactory(
            profile__preferred_candidate=CANDIDATE_CLINTON,
            profile__state=self.safe_trump.name)
        ctx = ProfileContext(user.profile)
        self.assertTrue(ctx.needs_match)
        self.assertFalse(ctx.kingmaker)
        self.assertFalse(ctx.johnson)

    def test_johnson_in_safe_clinton(self):
        user = UserFactory(
            profile__preferred_candidate=CANDIDATE_JOHNSON,
            profile__state=self.safe_clinton.name)
        ctx = ProfileContext(user.profile)
        self.assertFalse(ctx.needs_match)
        self.assertFalse(ctx.kingmaker)
        self.assertTrue(ctx.johnson)

    def test_johnson_in_leans_clinton(self):
        user = UserFactory(
            profile__preferred_candidate=CANDIDATE_JOHNSON,
            profile__state=self.lean_clinton.name)
        ctx = ProfileContext(user.profile)
        self.assertTrue(ctx.needs_match)
        self.assertTrue(ctx.kingmaker)
        self.assertTrue(ctx.johnson)

    def test_johnson_in_leans_trump(self):
        user = UserFactory(
            profile__preferred_candidate=CANDIDATE_JOHNSON,
            profile__state=self.lean_trump.name)
        ctx = ProfileContext(user.profile)
        self.assertTrue(ctx.needs_match)
        self.assertTrue(ctx.kingmaker)
        self.assertTrue(ctx.johnson)

    def test_johnson_in_safe_trump(self):
        user = UserFactory(
            profile__preferred_candidate=CANDIDATE_JOHNSON,
            profile__state=self.safe_trump.name)
        ctx = ProfileContext(user.profile)
        self.assertFalse(ctx.needs_match)
        self.assertFalse(ctx.kingmaker)
        self.assertTrue(ctx.johnson)
