from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django.test import TestCase

from polling.models import CANDIDATE_CLINTON
from polling.models import CANDIDATE_STEIN
from polling.tests.factories import StateFactory
from users.tests.factories import UserFactory
from users.views import profile

HTTP_OK = 200
HTTP_REDIRECT = 302


class TestProfileView(TestCase):
    def setUp(self):
        super(TestProfileView, self).setUp()
        self.safe_state = StateFactory.create(
            safe_rank=1, safe_for=CANDIDATE_CLINTON)
        self.request = RequestFactory()
        self.user = UserFactory.create(
            profile__preferred_candidate=CANDIDATE_CLINTON,
            profile__state=self.safe_state.name)

    def test_nav(self):
        """Login-aware context menu has the right links"""
        request = self.request.get(reverse('users:profile'))
        request.user = self.user
        response = profile(request)
        self.assertContains(response, "View matches")
        self.assertContains(response, reverse("users:profile"))
        self.assertContains(response, "Update profile")
        self.assertContains(response, reverse("users:update_profile"))
        self.assertContains(response, "Log out")
        self.assertContains(response, reverse("logout"))

    def test_profile_missing_info(self):
        """If data is missing, redirect to update_profile"""
        self.user.profile.state = ''
        self.user.profile.save()
        request = self.request.get(reverse('users:profile'))
        request.user = self.user
        response = profile(request)
        self.assertEqual(response.status_code, HTTP_REDIRECT)
        self.assertTrue(response.has_header('Location'))
        self.assertEqual(response.get('Location'),
                         reverse('users:update_profile'))

    def test_paired_call_to_action(self):
        friend_state = StateFactory(safe_rank=1)
        friend = UserFactory.create(profile__state=friend_state.name)
        self.user.profile.friends.add(friend.profile)
        self.user.profile.paired_with = friend.profile
        request = self.request.get(reverse('users:profile'))
        request.user = self.user
        response = profile(request)
        self.assertContains(response, 'You pledged to swap your vote')

    def test_no_friends_call_to_action(self):
        request = self.request.get(reverse('users:profile'))
        request.user = self.user
        response = profile(request)
        self.assertContains(response,
                            'Expected to see friends to swap votes with?')
        self.assertContains(response, 'There aren\'t any friends')
        # Also when we add a friend, it shouldn't change
        friend = UserFactory.create(profile__state=self.user.profile.state)
        self.user.profile.friends.add(friend.profile)
        response = profile(request)
        self.assertContains(response,
                            'Expected to see friends to swap votes with?')
        self.assertContains(response, 'There aren\'t any friends')

    def test_some_matches_call_to_action(self):
        friend_state = StateFactory(tipping_point_rank=1)
        friend = UserFactory.create(profile__state=friend_state.name)
        friend.profile.preferred_candidate = CANDIDATE_STEIN
        friend.profile.save()
        self.user.profile.friends.add(friend.profile)
        request = self.request.get(reverse('users:profile'))
        request.user = self.user
        response = profile(request)
        self.assertContains(response, 'Expected to see more matches?')
        self.assertContains(response, 'There aren\'t any more friends')
