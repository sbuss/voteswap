from django.test import RequestFactory
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.utils import timezone
from mock import MagicMock
from mock import patch
import time

from voteswap.views import _attach_signup_info
from voteswap.views import SignUpInfo


class TestSignupInfo(TestCase):
    def setUp(self):
        self.request = RequestFactory()

    def test_create_remote_addr(self):
        request = self.request.get(reverse('landing_page'))
        request.session = {}
        request.META = {
            'HTTP_REFERER': 'foo-referer',
            'REMOTE_ADDR': 'remote-addr',
        }
        now = timezone.datetime.now()
        with patch('voteswap.views.timezone') as mock_timezone:
            mock_timezone.datetime.now = MagicMock(return_value=now)
            _attach_signup_info(request)
        expected = SignUpInfo(
            int(time.mktime(now.timetuple())), 'foo-referer', 'remote-addr')
        self.assertEqual(request.session['signupinfo'], expected)

    def test_create_forwarded_for(self):
        request = self.request.get(reverse('landing_page'))
        request.session = {}
        request.META = {
            'HTTP_REFERER': 'foo-referer',
            'HTTP_X_FORWARDED_FOR': 'forwarded-for,',
        }
        now = timezone.datetime.now()
        with patch('voteswap.views.timezone') as mock_timezone:
            mock_timezone.datetime.now = MagicMock(return_value=now)
            _attach_signup_info(request)
        expected = SignUpInfo(
            int(time.mktime(now.timetuple())), 'foo-referer', 'forwarded-for')
        self.assertEqual(request.session['signupinfo'], expected)

    def test_recent_entry(self):
        now = timezone.datetime.now()
        request = self.request.get(reverse('landing_page'))
        request.session = {}
        existing = SignUpInfo(
            int(time.mktime(now.timetuple())), 'foo-referer', 'remote-addr')
        request.session['signupinfo'] = existing
        with patch('voteswap.views.timezone') as mock_timezone:
            mock_timezone.datetime.now = MagicMock(return_value=now)
            _attach_signup_info(request)
        self.assertEqual(request.session['signupinfo'], existing)

    def test_replace_entry(self):
        now = timezone.datetime.now()
        request = self.request.get(reverse('landing_page'))
        request.session = {}
        existing = SignUpInfo(
            int(time.mktime(now.timetuple())), 'foo-referer', 'remote-addr')
        request.session['signupinfo'] = existing
        request.META = {
            'HTTP_REFERER': 'foo-referer',
            'REMOTE_ADDR': 'remote-addr',
        }
        new_now = now + timezone.timedelta(days=1)
        with patch('voteswap.views.timezone') as mock_timezone:
            mock_timezone.datetime.now = MagicMock(return_value=new_now)
            _attach_signup_info(request)
        expected = SignUpInfo(
            int(time.mktime(new_now.timetuple())),
            'foo-referer', 'remote-addr')
        self.assertNotEqual(request.session['signupinfo'], existing)
        self.assertEqual(request.session['signupinfo'], expected)
