from django.core import mail as testmail
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django.test import TestCase
import json

from polling.tests.factories import StateFactory
from users.models import PairProposal
from users.tests.factories import UserFactory
from users.views import propose_swap

HTTP_OK = 200


class TestProposeSwapView(TestCase):
    def setUp(self):
        super(TestProposeSwapView, self).setUp()
        self.request = RequestFactory()

    def test_success(self):
        user_state = StateFactory.create(tipping_point_rank=1)
        user = UserFactory.create(profile__state=user_state.name)
        match_state = StateFactory.create(safe_rank=1)
        match = UserFactory.create(profile__state=match_state.name)
        user.profile.friends.add(match.profile)
        request = self.request.post(
            reverse('users:propose_swap'),
            {'to_profile': match.profile.id})
        request.user = user
        self.assertFalse(PairProposal.objects.all())
        self.assertEqual(len(testmail.outbox), 0)
        response = propose_swap(request)
        self.assertEqual(len(testmail.outbox), 1)
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertEqual(response.content,
                         json.dumps({'status': 'ok', 'errors': {}}))
        proposal = PairProposal.objects.get(from_profile=user.profile)
        self.assertTrue(proposal)
        self.assertEqual(proposal.to_profile, match.profile)

    def test_get_fail(self):
        user = UserFactory.create()
        request = self.request.get(reverse('users:propose_swap'))
        request.user = user
        response = propose_swap(request)
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertEqual(
            response.content,
            json.dumps(
                {'status': 'error',
                 'errors': {'method': 'Must POST with to_profile set'}}))

    def test_invalid_error(self):
        user = UserFactory.create()
        match = UserFactory.create()
        # Don't add match as a friend, so it's invalid
        request = self.request.post(
            reverse('users:propose_swap'),
            {'to_profile': match.profile.id})
        request.user = user
        self.assertFalse(PairProposal.objects.all())
        response = propose_swap(request)
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertEqual(
            response.content,
            json.dumps(
                {'status': 'error',
                 'errors': {
                     "to_profile": ["Select a valid choice. That choice is not one of the available choices."]}  # NOQA
                }))
