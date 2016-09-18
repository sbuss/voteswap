from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django.test import TestCase

from polling.models import CANDIDATE_CLINTON
from polling.tests.factories import StateFactory
from users.tests.factories import UserFactory
from voteswap.views import confirm_signup

HTTP_OK = 200
HTTP_REDIRECT = 302
HTTP_SERVER_ERROR = 500


class TestConfirmSignup(TestCase):
    def setUp(self):
        self.user = UserFactory(profile=None)
        self.request = RequestFactory()
        self.state = StateFactory()
        self.session = {
            'landing_page_form': {
                'state': self.state.name,
                'preferred_candidate': CANDIDATE_CLINTON,
                'reason': u'just because',
            }
        }

    def test_no_session_data(self):
        """For some reason, session data is missin, redirect."""
        request = self.request.get(reverse(confirm_signup))
        request.user = self.user
        request.session = {}
        response = confirm_signup(request)
        self.assertEqual(response.status_code, HTTP_REDIRECT)
        self.assertTrue(response.has_header('Location'))
        self.assertEqual(response.get('Location'), reverse('signup'))

    def test_success(self):
        request = self.request.get(reverse(confirm_signup))
        request.user = self.user
        request.session = self.session
        response = confirm_signup(request)
        user = get_user_model().objects.get(id=self.user.id)
        self.assertTrue(user.profile)
        self.assertEqual(user.profile.state, self.state.name)
        self.assertEqual(response.status_code, HTTP_REDIRECT)
        self.assertTrue(response.has_header('Location'))
        self.assertEqual(response.get('Location'), reverse('users:profile'))

    def test_failure(self):
        request = self.request.get(reverse(confirm_signup))
        request.user = UserFactory()  # user gets a profile, so form save fails
        request.session = self.session
        response = confirm_signup(request)
        self.assertEqual(response.status_code, HTTP_SERVER_ERROR)
