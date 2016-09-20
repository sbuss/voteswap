from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django.test import TestCase

from voteswap.match import get_friend_matches
from voteswap.tests.test_match import _TestSafeStateMatchBase
from voteswap.tests.test_match import _TestSwingStateMatchBase
from voteswap.tests.test_match import _TestSafeStateFriendsOfFriendsMatchBase
from voteswap.views import match as match_view

HTTP_OK = 200


class Common(object):
    class Base(TestCase):
        def setUp(self):
            super(Common.Base, self).setUp()
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


class TestSafeStateMatch(_TestSafeStateMatchBase, Common.Base):
    pass


class TestSwingStateMatch(_TestSwingStateMatchBase, Common.Base):
    pass


class TestSafeStateFriendsOfFriendsMatch(
        _TestSafeStateFriendsOfFriendsMatchBase, Common.Base):
    def test_through_friend_shown(self):
        request = self.request.get(reverse(match_view))
        request.user = self.user
        response = match_view(request)
        self.assertEqual(response.status_code, HTTP_OK)
        matches = get_friend_matches(self.user)
        for match in matches:
            self.assertContains(
                response, match.profile.fb_name)
            if not match.is_direct:
                self.assertContains(
                    response, "via %s" % match.through.fb_name)
