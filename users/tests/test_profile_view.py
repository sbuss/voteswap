from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django.test import TestCase

from polling.models import CANDIDATE_CLINTON
from polling.tests.factories import StateFactory
from users.tests.factories import UserFactory
from users.views import profile

HTTP_OK = 200


class TestProfileView(TestCase):
    def setUp(self):
        super(TestProfileView, self).setUp()
        self.safe_state = StateFactory.create(
            safe_rank=1, safe_for=CANDIDATE_CLINTON)
        self.request = RequestFactory()
        self.user = UserFactory.create(profile__state=self.safe_state.name)

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
        """Update profile link shown if the user's profile is missing info"""
        self.user.profile.state = ''
        self.user.profile.save()
        request = self.request.get(reverse('users:profile'))
        request.user = self.user
        response = profile(request)
        self.assertContains(
            response,
            "We're missing some information from you")

    def test_voter_in_state(self):
        request = self.request.get(reverse('users:profile'))
        request.user = self.user
        response = profile(request)
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertContains(
            response,
            "You're a {candidate} voter in {state}".format(
                candidate=self.user.profile.preferred_candidate,
                state=self.user.profile.state))
