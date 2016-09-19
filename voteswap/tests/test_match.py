from django.test import TestCase

from polling.models import CANDIDATE_CLINTON
from polling.models import CANDIDATE_JOHNSON
from polling.models import CANDIDATE_TRUMP
from polling.tests.factories import StateFactory
from users.tests.factories import UserFactory
from voteswap.match import _friends_for_safe_state_user
from voteswap.match import _friends_for_swing_state_user
from voteswap.match import get_friend_matches
from voteswap.match import NoMatchNecessary


class TestSafeStateMatch(TestCase):
    def setUp(self):
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
            friend = UserFactory.create()
            StateFactory.create(
                name=friend.profile.state,
                safe_for=self.user.profile.preferred_candidate,
                safe_rank=i+2)  # +2 because state_safe is rank 1
            self.user.profile.friends.add(friend.profile)
        # Create friends in swing states
        swing_state_1 = StateFactory.create(tipping_point_rank=1)
        swing_user_1 = UserFactory.create(
            profile__state=swing_state_1.name,
            profile__preferred_candidate=CANDIDATE_JOHNSON,
            profile__second_candidate=candidate)
        self.user.profile.friends.add(swing_user_1.profile)
        swing_state_2 = StateFactory.create(tipping_point_rank=2)
        swing_user_2 = UserFactory.create(
            profile__state=swing_state_2.name,
            profile__preferred_candidate=CANDIDATE_JOHNSON,
            profile__second_candidate=candidate)
        self.user.profile.friends.add(swing_user_2.profile)
        swing_state_3 = StateFactory.create(tipping_point_rank=3)
        swing_user_3 = UserFactory.create(
            profile__state=swing_state_3.name,
            profile__preferred_candidate=candidate)
        self.user.profile.friends.add(swing_user_3.profile)
        # The ordering of expected_matches matters, it's ordered by state rank
        self.expected_matches = [swing_user_1.profile, swing_user_2.profile]

    def test_safe_state_major_candidate(self):
        # Now we should have two friends that show up
        friends = _friends_for_safe_state_user(self.user)
        self.assertEqual(len(friends), 2)
        self.assertEqual(friends, self.expected_matches)
        self.assertEqual(get_friend_matches(self.user), self.expected_matches)
        # And I should be in my friend's potential matches
        self.assertIn(self.user.profile,
                      _friends_for_swing_state_user(friends[0].user))

    def test_no_match_minor_in_safe_state(self):
        state_safe = StateFactory.create(
            safe_for=CANDIDATE_TRUMP,
            safe_rank=1,
        )
        user = UserFactory.create(
            profile__state=state_safe.name,
            profile__preferred_candidate=CANDIDATE_JOHNSON,
            profile__second_candidate=CANDIDATE_CLINTON,
        )
        self.assertTrue(
            isinstance(get_friend_matches(user), NoMatchNecessary))

    def test_paired_not_included(self):
        # pick two friends and pair them
        friends = _friends_for_safe_state_user(self.user)
        self.assertEqual(len(friends), 2)
        friend1 = friends[0]
        friend2 = self.user.profile.friends.exclude(id=friend1.id)[0]
        friend1.paired_with = friend2
        friends = _friends_for_safe_state_user(self.user)
        self.assertEqual(len(friends), 1)
        self.assertNotIn(friend1, friends)

    def test_all_active(self):
        friends = _friends_for_safe_state_user(self.user)
        self.assertTrue(all(friend.active for friend in friends))

    def test_no_inactive(self):
        """No inactive profiles should be returned."""
        friends = _friends_for_safe_state_user(self.user)
        self.assertEqual(len(friends), 2)
        friend1 = friends[0]
        friend1.active = False
        friend1.save()
        friends = _friends_for_safe_state_user(self.user)
        self.assertEqual(len(friends), 1)
        self.assertNotIn(friend1, friends)


class TestSwingStateMatch(TestCase):
    def setUp(self):
        candidate = CANDIDATE_JOHNSON
        self.state_safe = StateFactory.create(
            tipping_point_rank=1,
        )
        self.user = UserFactory.create(
            profile__state=self.state_safe.name,
            profile__preferred_candidate=candidate,
            profile__second_candidate=CANDIDATE_CLINTON
        )
        # Make two friends for each candidate in a safe state for each
        # The ordering of expected matches is by state safe_rank
        self.expected_matches = []
        safe_rank = 1
        for (preferred_candidate, safe_for) in [
                (CANDIDATE_CLINTON, CANDIDATE_CLINTON),
                (CANDIDATE_TRUMP, CANDIDATE_CLINTON),
                (CANDIDATE_CLINTON, CANDIDATE_TRUMP),
                (CANDIDATE_TRUMP, CANDIDATE_TRUMP)]:
            for i in range(2):
                friend = UserFactory.create(
                    profile__preferred_candidate=preferred_candidate)
                StateFactory.create(
                    name=friend.profile.state,
                    safe_for=safe_for,
                    safe_rank=safe_rank)
                self.user.profile.friends.add(friend.profile)
                if preferred_candidate == self.user.profile.second_candidate:
                    self.expected_matches.append(friend.profile)
                safe_rank += 1
        # Create friends in swing states
        swing_state_1 = StateFactory.create(tipping_point_rank=2)
        swing_user_1 = UserFactory.create(
            profile__state=swing_state_1.name,
            profile__preferred_candidate=CANDIDATE_JOHNSON,
            profile__second_candidate=candidate)
        self.user.profile.friends.add(swing_user_1.profile)
        swing_state_2 = StateFactory.create(tipping_point_rank=3)
        swing_user_2 = UserFactory.create(
            profile__state=swing_state_2.name,
            profile__preferred_candidate=CANDIDATE_JOHNSON,
            profile__second_candidate=candidate)
        self.user.profile.friends.add(swing_user_2.profile)
        swing_state_3 = StateFactory.create(tipping_point_rank=4)
        swing_user_3 = UserFactory.create(
            profile__state=swing_state_3.name,
            profile__preferred_candidate=candidate)
        self.user.profile.friends.add(swing_user_3.profile)

    def test_swing_state_minor_candidate(self):
        # Now we should have eight friends in safe states, but only 4 of them
        # would vote for my second choice
        friends = _friends_for_swing_state_user(self.user)
        self.assertEqual(len(friends), 4)
        self.assertEqual(friends, self.expected_matches)
        self.assertEqual(get_friend_matches(self.user), self.expected_matches)
        # And I should be in my friend's potential matches
        self.assertIn(self.user.profile,
                      _friends_for_safe_state_user(friends[0].user))

    def test_no_match_major_in_swing_state(self):
        state_safe = StateFactory.create(
            tipping_point_rank=1,
        )
        user = UserFactory.create(
            profile__state=state_safe.name,
            profile__preferred_candidate=CANDIDATE_CLINTON,
        )
        self.assertTrue(
            isinstance(get_friend_matches(user), NoMatchNecessary))

    def test_paired_not_included(self):
        # pick two friends and pair them
        friends = _friends_for_swing_state_user(self.user)
        self.assertEqual(len(friends), 4)
        friend1 = friends[0]
        friend2 = self.user.profile.friends.exclude(
            id__in=[friend.id for friend in friends])[0]
        friend1.paired_with = friend2
        friends = _friends_for_swing_state_user(self.user)
        self.assertEqual(len(friends), 3)
        self.assertNotIn(friend1, friends)

    def test_all_active(self):
        friends = _friends_for_swing_state_user(self.user)
        self.assertTrue(all(friend.active for friend in friends))

    def test_no_inactive(self):
        """No inactive profiles should be returned."""
        friends = _friends_for_swing_state_user(self.user)
        self.assertEqual(len(friends), 4)
        friend1 = friends[0]
        friend1.active = False
        friend1.save()
        friends = _friends_for_swing_state_user(self.user)
        self.assertEqual(len(friends), 3)
        self.assertNotIn(friend1, friends)


class TestSafeStateFriendsOfFriendsMatch(TestCase):
    def setUp(self):
        candidate = CANDIDATE_CLINTON
        self.state_safe = StateFactory.create(
            safe_for=candidate,
            safe_rank=1
        )
        self.user = UserFactory.create(
            profile__state=self.state_safe.name,
            profile__preferred_candidate=candidate)
        tipping_point_rank = 1
        self.expected_matches = []
        # Create friends in safe states
        for i in range(2):
            friend = UserFactory.create()
            StateFactory.create(
                name=friend.profile.state,
                safe_for=self.user.profile.preferred_candidate,
                safe_rank=i+2)  # +2 because state_safe is rank 1
            self.user.profile.friends.add(friend.profile)
            # And create friends of these friends in swing states
            for i in range(2):
                foaf = UserFactory.create(
                    profile__preferred_candidate=CANDIDATE_JOHNSON,
                    profile__second_candidate=CANDIDATE_CLINTON)
                StateFactory.create(
                    name=foaf.profile.state,
                    tipping_point_rank=tipping_point_rank)
                tipping_point_rank += 1
                friend.profile.friends.add(foaf.profile)
                self.expected_matches.append(foaf.profile)
        # Create friends in swing states
        for i in range(2):
            friend = UserFactory.create(
                profile__preferred_candidate=CANDIDATE_JOHNSON,
                profile__second_candidate=CANDIDATE_CLINTON)
            StateFactory.create(
                name=friend.profile.state,
                tipping_point_rank=tipping_point_rank)
            tipping_point_rank += 1
            self.user.profile.friends.add(friend.profile)
            self.expected_matches.append(friend.profile)
        # At this point there are two direct friends and four indirect friends
        # to match

    def test_matches(self):
        friends = _friends_for_safe_state_user(self.user)
        self.assertEqual(len(friends), 6)
        self.assertEqual(friends, self.expected_matches)
        self.assertEqual(get_friend_matches(self.user), self.expected_matches)
