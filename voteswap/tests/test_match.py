from django.test import TestCase
from django.utils import timezone

from polling.models import CANDIDATE_CLINTON
from polling.models import CANDIDATE_JOHNSON
from polling.models import CANDIDATE_STEIN
from polling.models import CANDIDATE_TRUMP
from polling.models import State
from polling.tests.factories import StateFactory
from users.models import PairProposal
from users.tests.factories import ProfileFactory
from users.tests.factories import UserFactory
from voteswap.match import _matches_for_safe_state_profile
from voteswap.match import _matches_for_swing_state_profile
from voteswap.match import get_friend_matches
from voteswap.match import NoMatchNecessary


def _profiles(matches):
    return [match.profile for match in matches]


class _TestSafeStateMatchBase(TestCase):
    def setUp(self):
        super(_TestSafeStateMatchBase, self).setUp()
        candidate = CANDIDATE_CLINTON
        self.state_safe = StateFactory.create(
            safe_for=candidate,
            safe_rank=1
        )
        self.user = UserFactory.create(
            profile__state=self.state_safe.name,
            profile__preferred_candidate=candidate)
        # Create friends in safe states
        for i in range(10):
            state = StateFactory.create(
                safe_for=self.user.profile.preferred_candidate,
                safe_rank=i+2)  # +2 because state_safe is rank 1
            friend = UserFactory.create(profile__state=state.name)
            self.user.profile.friends.add(friend.profile)
        # Create friends in swing states
        self.swing_state_1 = StateFactory.create(tipping_point_rank=1)
        swing_user_1 = UserFactory.create(
            profile__state=self.swing_state_1.name,
            profile__preferred_candidate=CANDIDATE_JOHNSON)
        self.user.profile.friends.add(swing_user_1.profile)
        self.swing_state_2 = StateFactory.create(tipping_point_rank=2)
        swing_user_2 = UserFactory.create(
            profile__state=self.swing_state_2.name,
            profile__preferred_candidate=CANDIDATE_STEIN)
        self.user.profile.friends.add(swing_user_2.profile)
        self.swing_state_3 = StateFactory.create(tipping_point_rank=3)
        swing_user_3 = UserFactory.create(
            profile__state=self.swing_state_3.name,
            profile__preferred_candidate=candidate)
        self.user.profile.friends.add(swing_user_3.profile)
        # The ordering of expected_matches matters, it's ordered by state rank
        self.expected_matches = [swing_user_1.profile, swing_user_2.profile]


class TestSafeStateMatch(_TestSafeStateMatchBase):
    def test_safe_state_major_candidate(self):
        # Now we should have three matches that show up
        matches = _matches_for_safe_state_profile(self.user.profile)
        self.assertEqual(len(matches), 2)
        self.assertEqual(_profiles(matches), self.expected_matches)
        self.assertEqual(_profiles(get_friend_matches(self.user.profile)),
                         self.expected_matches)
        # And I should be in my friend's potential matches
        self.assertIn(
            self.user.profile,
            _profiles(_matches_for_swing_state_profile(matches[0].profile)))

    def test_no_match_minor_in_safe_state(self):
        state_safe = StateFactory.create(
            safe_for=CANDIDATE_TRUMP,
            safe_rank=1,
        )
        user = UserFactory.create(
            profile__state=state_safe.name,
            profile__preferred_candidate=CANDIDATE_JOHNSON,
        )
        self.assertTrue(
            isinstance(get_friend_matches(user.profile), NoMatchNecessary))

    def test_paired_not_included(self):
        # pick two friends and pair them
        matches = _matches_for_safe_state_profile(self.user.profile)
        self.assertEqual(len(matches), 2)
        friend1 = matches[0].profile
        friend2 = self.user.profile.friends.exclude(id=friend1.id)[0]
        friend1.paired_with = friend2
        matches = _matches_for_safe_state_profile(self.user.profile)
        self.assertEqual(len(matches), 1)
        self.assertNotIn(friend1, _profiles(matches))

    def test_states(self):
        matches = _matches_for_safe_state_profile(self.user.profile)
        self.assertTrue(matches)
        swing_states = State.objects.filter(
            tipping_point_rank__gt=0, safe_rank=-1).values_list(
                'name', flat=True)
        self.assertTrue(
            all(match.profile.state in swing_states for match in matches))


class _TestSwingStateMatchBase(TestCase):
    def setUp(self):
        super(_TestSwingStateMatchBase, self).setUp()
        candidate = CANDIDATE_JOHNSON
        self.state_safe = StateFactory.create(
            tipping_point_rank=1,
        )
        self.user = UserFactory.create(
            profile__state=self.state_safe.name,
            profile__preferred_candidate=candidate,
        )
        # Make two friends for each candidate in a safe state for each
        # The ordering of expected matches is by state safe_rank
        self.expected_matches = []
        safe_rank = 1
        self.safe_states = []
        for (preferred_candidate, safe_for) in [
                (CANDIDATE_CLINTON, CANDIDATE_CLINTON),
                (CANDIDATE_TRUMP, CANDIDATE_CLINTON),
                (CANDIDATE_CLINTON, CANDIDATE_TRUMP),
                (CANDIDATE_TRUMP, CANDIDATE_TRUMP)]:
            for i in range(2):
                state = StateFactory.create(
                    safe_for=safe_for,
                    safe_rank=safe_rank)
                self.safe_states.append(state)
                friend = UserFactory.create(
                    profile__state=state.name,
                    profile__preferred_candidate=preferred_candidate)
                self.user.profile.friends.add(friend.profile)
                if preferred_candidate == CANDIDATE_CLINTON:
                    self.expected_matches.append(friend.profile)
                safe_rank += 1
        # Create friends in swing states
        swing_state_1 = StateFactory.create(tipping_point_rank=2)
        swing_user_1 = UserFactory.create(
            profile__state=swing_state_1.name,
            profile__preferred_candidate=CANDIDATE_JOHNSON)
        self.user.profile.friends.add(swing_user_1.profile)
        swing_state_2 = StateFactory.create(tipping_point_rank=3)
        swing_user_2 = UserFactory.create(
            profile__state=swing_state_2.name,
            profile__preferred_candidate=CANDIDATE_STEIN)
        self.user.profile.friends.add(swing_user_2.profile)
        swing_state_3 = StateFactory.create(tipping_point_rank=4)
        swing_user_3 = UserFactory.create(
            profile__state=swing_state_3.name,
            profile__preferred_candidate=candidate)
        self.user.profile.friends.add(swing_user_3.profile)


class TestSwingStateMatch(_TestSwingStateMatchBase):
    def test_swing_state_minor_candidate(self):
        # Now we should have eight friends in safe states, but only 4 of them
        # are suitable for swapping
        matches = _matches_for_swing_state_profile(self.user.profile)
        self.assertEqual(len(matches), 4)
        self.assertEqual(_profiles(matches), self.expected_matches)
        self.assertEqual(
            _profiles(get_friend_matches(self.user.profile)),
            self.expected_matches)
        # And I should be in my friend's potential matches
        self.assertIn(
            self.user.profile,
            _profiles(_matches_for_safe_state_profile(
                matches[0].profile)))

    def test_no_match_major_in_swing_state(self):
        state_safe = StateFactory.create(
            tipping_point_rank=1,
        )
        user = UserFactory.create(
            profile__state=state_safe.name,
            profile__preferred_candidate=CANDIDATE_CLINTON,
        )
        self.assertTrue(
            isinstance(get_friend_matches(user.profile), NoMatchNecessary))

    def test_paired_not_included(self):
        # pick two friends and pair them
        matches = _matches_for_swing_state_profile(self.user.profile)
        self.assertEqual(len(matches), 4)
        friend1 = matches[0].profile
        friend2 = self.user.profile.friends.exclude(
            id__in=[match.profile.id for match in matches])[0]
        friend1.paired_with = friend2
        matches = _matches_for_swing_state_profile(self.user.profile)
        self.assertEqual(len(matches), 3)
        self.assertNotIn(friend1, _profiles(matches))

    def test_states(self):
        matches = _matches_for_swing_state_profile(self.user.profile)
        safe_states = State.objects.filter(
            tipping_point_rank=-1, safe_rank__gt=0).values_list(
                'name', flat=True)
        self.assertTrue(
            all(match.profile.state in safe_states for match in matches))


class _TestSafeStateFriendsOfFriendsMatchBase(TestCase):
    def setUp(self):
        super(_TestSafeStateFriendsOfFriendsMatchBase, self).setUp()
        candidate = CANDIDATE_CLINTON
        self.state_safe = StateFactory.create(
            safe_for=candidate,
            safe_rank=1
        )
        self.user = UserFactory.create(
            profile__state=self.state_safe.name,
            profile__preferred_candidate=candidate)
        tipping_point_rank = 1
        self.foaf_expected_matches = []
        # Create friends that haven't specified a vote choice just for links
        for i in range(2):
            friend_profile = ProfileFactory.create(state='')
            self.user.profile.friends.add(friend_profile)
            # And create friends of these friends in swing states
            for i in range(2):
                state = StateFactory.create(
                    tipping_point_rank=tipping_point_rank)
                foaf = UserFactory.create(
                    profile__state=state.name,
                    profile__preferred_candidate=CANDIDATE_STEIN)
                tipping_point_rank += 1
                friend_profile.friends.add(foaf.profile)
                self.foaf_expected_matches.append(foaf.profile)
        # And make another foaf that's friends with both of my friends
        state = StateFactory.create(
            tipping_point_rank=tipping_point_rank)
        self.foafoaf = UserFactory.create(
            profile__state=state.name,
            profile__preferred_candidate=CANDIDATE_JOHNSON)
        for friend in self.user.profile.friends.all():
            friend.friends.add(self.foafoaf.profile)
        self.foaf_expected_matches.append(self.foafoaf.profile)
        tipping_point_rank += 1
        self.direct_expected_matches = []
        # Create friends in swing states
        for i in range(2):
            state = StateFactory.create(
                tipping_point_rank=tipping_point_rank)
            friend = UserFactory.create(
                profile__state=state.name,
                profile__preferred_candidate=CANDIDATE_JOHNSON)
            tipping_point_rank += 1
            self.user.profile.friends.add(friend.profile)
            self.direct_expected_matches.append(friend.profile)
        # Direct friends are always preferred, so prepend them to expected
        self.expected_matches = (
            self.direct_expected_matches + self.foaf_expected_matches)
        # At this point there are two direct friends and five indirect friends
        # to match


class TestSafeStateFriendsOfFriendsMatch(
        _TestSafeStateFriendsOfFriendsMatchBase):
    def test_matches(self):
        matches = _matches_for_safe_state_profile(self.user.profile)
        self.assertEqual(len(matches), 7)
        self.assertEqual(_profiles(matches), self.expected_matches)
        self.assertEqual(
            _profiles(get_friend_matches(self.user.profile)),
            self.expected_matches)

    def test_direct(self):
        matches = _matches_for_safe_state_profile(
            self.user.profile, direct=True, foaf=False)
        self.assertEqual(len(matches), 2)
        self.assertEqual(_profiles(matches), self.direct_expected_matches)
        self.assertTrue(all(match.is_direct for match in matches))

    def test_foaf(self):
        matches = _matches_for_safe_state_profile(
            self.user.profile, direct=False, foaf=True)
        self.assertEqual(len(matches), 5)
        self.assertEqual(_profiles(matches), self.foaf_expected_matches)
        self.assertFalse(any(match.is_direct for match in matches))


class TestExclude(TestCase):
    def setUp(self):
        candidate = CANDIDATE_CLINTON
        self.state_safe = StateFactory.create(
            safe_for=candidate,
            safe_rank=1
        )
        self.user = UserFactory.create(
            profile__state=self.state_safe.name,
            profile__preferred_candidate=candidate)
        self.state_swing = StateFactory.create(
            tipping_point_rank=1)
        self.friend = UserFactory.create(
            profile__state=self.state_swing.name,
            profile__preferred_candidate=CANDIDATE_STEIN)
        self.user.profile.friends.add(self.friend.profile)
        self.foaf = UserFactory.create(
            profile__state=self.state_swing.name,
            profile__preferred_candidate=CANDIDATE_JOHNSON)
        self.friend.profile.friends.add(self.foaf.profile)
        self.friend_proposal = PairProposal.objects.create(
            from_profile=self.user.profile,
            to_profile=self.friend.profile)
        self.foaf_proposal = PairProposal.objects.create(
            from_profile=self.foaf.profile,
            to_profile=self.user.profile)

    def test_matches(self):
        """Baseline test that both friends show up in matches"""
        self.assertEqual(
            set(_profiles(get_friend_matches(
                self.user.profile, exclude_pending=False))),
            set([self.friend.profile, self.foaf.profile]))
        self.assertEqual(
            set(_profiles(get_friend_matches(
                self.user.profile, exclude_pending=True))),
            set())

    def test_exclude_pending(self):
        self.assertEqual(
            set(_profiles(get_friend_matches(self.user.profile))),
            set())
        self.foaf_proposal.delete()
        self.assertEqual(
            set(_profiles(get_friend_matches(self.user.profile))),
            set([self.foaf.profile]))

    def test_exclude_rejected(self):
        self.assertEqual(
            set(_profiles(get_friend_matches(self.user.profile))),
            set())
        self.friend_proposal.date_rejected = timezone.now()
        self.friend_proposal.save()
        self.assertEqual(
            set(_profiles(get_friend_matches(self.user.profile))),
            set())


class TestAllowRandomSafeState(_TestSafeStateMatchBase):
    def setUp(self):
        super(TestAllowRandomSafeState, self).setUp()
        # Add some allow_random_users
        random_user_1 = UserFactory.create(
            profile__state=self.swing_state_1.name,
            profile__preferred_candidate=CANDIDATE_JOHNSON,
            profile__allow_random=True)
        random_user_2 = UserFactory.create(
            profile__state=self.swing_state_2.name,
            profile__preferred_candidate=CANDIDATE_JOHNSON,
            profile__allow_random=True)
        self.expected_no_random = self.expected_matches
        self.expected_with_random = self.expected_matches + [
            random_user_1.profile, random_user_2.profile]

    def test_no_random_matches_when_false(self):
        self.user.profile.allow_random = False
        self.user.profile.save()
        matches = _matches_for_safe_state_profile(self.user.profile)
        self.assertEqual(len(matches), 2)
        self.assertEqual(_profiles(matches), self.expected_no_random)

    def test_include_random_matches_when_true(self):
        self.user.profile.allow_random = True
        self.user.profile.save()
        matches = _matches_for_safe_state_profile(self.user.profile)
        self.assertEqual(len(matches), 4)
        self.assertEqual(_profiles(matches), self.expected_with_random)


class TestAllowRandomSwingState(_TestSwingStateMatchBase):
    def setUp(self):
        super(TestAllowRandomSwingState, self).setUp()
        # Add some allow_random_users
        random_user_1 = UserFactory.create(
            profile__state=self.safe_states[0].name,
            profile__preferred_candidate=CANDIDATE_CLINTON,
            profile__allow_random=True)
        random_user_2 = UserFactory.create(
            profile__state=self.safe_states[1].name,
            profile__preferred_candidate=CANDIDATE_CLINTON,
            profile__allow_random=True)
        self.expected_no_random = self.expected_matches
        self.expected_with_random = self.expected_matches + [
            random_user_1.profile, random_user_2.profile]

    def test_no_random_matches_when_false(self):
        self.user.profile.allow_random = False
        self.user.profile.save()
        matches = _matches_for_swing_state_profile(self.user.profile)
        self.assertEqual(len(matches), 4)
        self.assertEqual(_profiles(matches), self.expected_no_random)

    def test_include_random_matches_when_true(self):
        self.user.profile.allow_random = True
        self.user.profile.save()
        matches = _matches_for_swing_state_profile(self.user.profile)
        self.assertEqual(len(matches), 6)
        self.assertEqual(_profiles(matches), self.expected_with_random)
