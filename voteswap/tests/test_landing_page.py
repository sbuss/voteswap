from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django.test import TestCase

from polling.models import CANDIDATE_CLINTON
from polling.tests.factories import StateFactory
from users.tests.factories import UserFactory
from voteswap.forms import LandingPageForm
from voteswap.views import landing_page

HTTP_OK = 200
HTTP_REDIRECT = 302


class TestLandingPageView(TestCase):
    def setUp(self):
        self.user = UserFactory(profile=None)
        self.request = RequestFactory()
        # Need some states to load the landing page
        StateFactory.create(tipping_point_rank=1)
        StateFactory.create(safe_rank=1)

    def test_login_redirect(self):
        request = self.request.get(reverse(landing_page))
        request.user = self.user
        response = landing_page(request)
        self.assertEqual(response.status_code, HTTP_REDIRECT)
        self.assertTrue(response.has_header('Location'))
        self.assertEqual(response.get('Location'), reverse('users:profile'))

    def test_anonymous(self):
        request = self.request.get(reverse(landing_page))
        request.user = AnonymousUser()
        response = landing_page(request)
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertContains(response, 'Join with Facebook')
        self.assertContains(response, 'action="%s"' % reverse('landing_page'))

    def test_post(self):
        state = StateFactory()
        data = {'preferred_candidate': CANDIDATE_CLINTON,
                'state': state.name}
        request = self.request.post(reverse(landing_page), data=data)
        request.user = AnonymousUser()
        request.session = {}
        response = landing_page(request)
        self.assertTrue('landing_page_form' in request.session)
        form = LandingPageForm(data=data)
        self.assertTrue(form.is_valid())
        full_data = form.cleaned_data
        self.assertEqual(request.session['landing_page_form'], full_data)
        self.assertEqual(response.status_code, HTTP_REDIRECT)
        self.assertTrue(response.has_header('Location'))
        redirect_to = "{base}?next={next}".format(
            base=reverse('social:begin', args=['facebook']),
            next=reverse('confirm_signup'))
        self.assertEqual(response.get('Location'), redirect_to)
