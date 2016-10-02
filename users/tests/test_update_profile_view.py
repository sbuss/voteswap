from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django.test import TestCase

from polling.tests.factories import StateFactory
from users.models import Profile
from users.tests.factories import UserFactory
from users.views import update_profile

HTTP_OK = 200
HTTP_REDIRECT = 302


class TestProfileView(TestCase):
    def setUp(self):
        super(TestProfileView, self).setUp()
        self.request = RequestFactory()
        self.user = UserFactory.create(
            profile__reason="#NeverTrump")

    def test_go_back(self):
        request = self.request.get(reverse('users:update_profile'))
        request.user = self.user
        response = update_profile(request)
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertContains(response, "Cancel")

    def test_initial_data(self):
        request = self.request.get(reverse('users:update_profile'))
        request.user = self.user
        response = update_profile(request)
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertContains(response, self.user.profile.state)
        self.assertContains(response, self.user.profile.preferred_candidate)
        self.assertContains(response, self.user.profile.reason_decoded)
        self.assertContains(response, self.user.email)

    def test_update(self):
        new_state = StateFactory.create()
        new_reason = "I want to get off of Mr. Trump's wild ride"
        new_email = 'foobar@example.com'
        data = {'preferred_candidate': self.user.profile.preferred_candidate,
                'state': new_state.name,
                'reason': new_reason,
                'email': new_email}
        request = self.request.post(reverse('users:update_profile'), data=data)
        request.user = self.user
        response = update_profile(request)
        self.assertEqual(response.status_code, HTTP_REDIRECT)
        self.assertTrue(response.has_header('Location'))
        self.assertEqual(response.get('Location'), reverse('users:profile'))
        profile = Profile.objects.get(id=self.user.profile.id)
        self.assertEqual(profile.state, new_state.name)
        self.assertEqual(profile.reason_decoded, new_reason)
        user = User.objects.get(id=self.user.id)
        self.assertEqual(user.email, new_email)

    def test_email_required(self):
        new_state = StateFactory.create()
        new_reason = "Why do you need my email, anyway?"
        data = {'preferred_candidate': self.user.profile.preferred_candidate,
                'state': new_state.name,
                'reason': new_reason,
                'email': ''}
        request = self.request.post(reverse('users:update_profile'), data=data)
        request.user = self.user
        response = update_profile(request)
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertContains(response, "error")
        self.assertContains(response, "This field is required")
