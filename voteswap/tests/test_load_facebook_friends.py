from django.test import RequestFactory
from django.test import TestCase
import json
from mock import MagicMock
from mock import patch

from voteswap.views import _add_facebook_friends_for_user
from users.models import Profile
from users.tests.factories import UserFactory


def _load_mock_request_response(
        fname='voteswap/tests/_fake_friends_list.json'):
    with open(fname, 'r') as f:
        data = json.load(f)

    def _mock_requests_call(url):
        # MagicMock that returns the json for .json()
        retval = MagicMock()
        retval.json = MagicMock(return_value=data)
        return retval
    return _mock_requests_call


class TestConfirmSignup(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.request = RequestFactory()

    def test_load_friends(self):
        self.assertEqual(len(Profile.objects.all()), 1)
        with patch('voteswap.views.requests.get',
                   side_effect=_load_mock_request_response()):
            _add_facebook_friends_for_user(self.user)
        self.assertEqual(len(Profile.objects.all()), 2)

    def test_next_link(self):
        def _next_then_nothing():
            """Get the request with 'next' set, then another without it."""
            count = [0]

            def choose_request(url):
                if count[0] == 0:
                    count[0] = 1
                    return _load_mock_request_response(
                        'voteswap/tests/_fake_friends_list_with_next.json')(
                            url)
                else:
                    return _load_mock_request_response(
                        'voteswap/tests/_fake_friends_list.json')(url)
            return choose_request

        with patch('voteswap.views.requests.get',
                   side_effect=_next_then_nothing()) as mock_get:
            _add_facebook_friends_for_user(self.user)
        self.assertTrue(mock_get.called)
