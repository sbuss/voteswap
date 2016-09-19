from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django.test import TestCase

from voteswap.match import get_friend_matches
from voteswap.tests.test_match import _TestSafeStateMatchBase
from voteswap.tests.test_match import _TestSwingStateMatchBase
from voteswap.tests.test_match import _TestSafeStateFriendsOfFriendsMatchBase
from voteswap.views import match as match_view

HTTP_OK = 200


class CommonTestMixins(object):
    class Base(TestCase):
        def setUp(self):
            super(CommonTestMixins.Base, self).setUp()
            self.request = RequestFactory()

        def test_has_matches(self):
            request = self.request.get(reverse(match_view))
            request.user = self.user
            response = match_view(request)
            self.assertEqual(response.status_code, HTTP_OK)
            matches = get_friend_matches(self.user)
            for match in matches:
                self.assertContains(
                    response, match.profile.user.get_full_name())


class TestSafeStateMatch(_TestSafeStateMatchBase, CommonTestMixins.Base):
    pass


class TestSwingStateMatch(_TestSwingStateMatchBase, CommonTestMixins.Base):
    pass


class TestSafeStateFriendsOfFriendsMatch(
        _TestSafeStateFriendsOfFriendsMatchBase, CommonTestMixins.Base):
    pass
