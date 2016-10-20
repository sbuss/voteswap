from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django.test import TestCase
from django.utils import timezone
from mock import patch
import time

from polling.models import CANDIDATE_CLINTON
from polling.tests.factories import StateFactory
from users.models import Profile
from users.models import SignUpLog
from users.tests.factories import ProfileFactory
from users.tests.factories import UserFactory
from voteswap.views import _attach_signup_info
from voteswap.views import confirm_signup
from voteswap.tests.test_load_facebook_friends import \
    _load_mock_request_response

HTTP_OK = 200
HTTP_REDIRECT = 302
HTTP_SERVER_ERROR = 500


@patch('voteswap.views.requests.get',
       side_effect=_load_mock_request_response())
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

    def test_no_session_data(self, mock_request):
        """For some reason, session data is missing, redirect."""
        request = self.request.get(reverse(confirm_signup))
        request.user = self.user
        request.session = {}
        response = confirm_signup(request)
        self.assertEqual(response.status_code, HTTP_REDIRECT)
        self.assertTrue(response.has_header('Location'))
        self.assertEqual(response.get('Location'), reverse('signup'))

    def test_success(self, mock_request):
        request = self.request.get(reverse(confirm_signup))
        request.user = self.user
        request.session = self.session
        response = confirm_signup(request)
        user = get_user_model().objects.get(id=self.user.id)
        self.assertTrue(user.profile)
        self.assertEqual(user.profile.state, self.state.name)
        self.assertEqual(response.status_code, HTTP_REDIRECT)
        self.assertTrue(response.has_header('Location'))
        self.assertEqual(response.get('Location'),
                         reverse('users:new_profile'))
        self.assertContains(response, 'CompleteRegistration')

    def test_existing_profile(self, mock_request):
        # This flow shouldn't happen, but in case it does, just merge the
        # profiles
        self.assertEqual(len(Profile.objects.all()), 0)
        request = self.request.get(reverse(confirm_signup))
        request.user = UserFactory()
        ProfileFactory.create(
            fb_id=request.user.social_auth.get().uid)
        self.assertEqual(len(Profile.objects.all()), 2)
        request.session = self.session
        response = confirm_signup(request)
        # And a new profile will be created from the response, but the existing
        # profile got deleted, so the total number hasn't changed
        self.assertEqual(len(Profile.objects.all()), 2)
        self.assertEqual(response.status_code, HTTP_REDIRECT)
        self.assertTrue(response.has_header('Location'))
        self.assertEqual(response.get('Location'), reverse('users:profile'))

    def test_signupinfo(self, mock_request):
        request = self.request.get(reverse(confirm_signup))
        request.user = self.user
        request.session = self.session
        request.META = {
            'HTTP_REFERER': 'foo-referer',
            'REMOTE_ADDR': 'remote-addr',
        }
        _attach_signup_info(request)
        self.assertEqual(SignUpLog.objects.count(), 0)
        confirm_signup(request)
        self.assertEqual(SignUpLog.objects.count(), 1)
        sul = SignUpLog.objects.get()
        self.assertEqual(sul.referer, 'foo-referer')
        self.assertEqual(sul.ip, 'remote-addr')
        self.assertEqual(sul.user, request.user)

    def test_signupinfo_post(self, mock_request):
        request = self.request.post(reverse(confirm_signup))
        request.user = self.user
        request.session = self.session
        request.META = {
            'HTTP_REFERER': 'foo-referer',
            'REMOTE_ADDR': 'remote-addr',
        }
        request.session['signupinfo'] = [
            int(time.mktime(timezone.datetime.now().timetuple())),
            'foo-referer',
            'remote-addr'
        ]
        # _attach_signup_info(request)
        self.assertEqual(SignUpLog.objects.count(), 0)
        confirm_signup(request)
        self.assertEqual(SignUpLog.objects.count(), 1)
        sul = SignUpLog.objects.get()
        self.assertEqual(sul.referer, 'foo-referer')
        self.assertEqual(sul.ip, 'remote-addr')
        self.assertEqual(sul.user, request.user)
