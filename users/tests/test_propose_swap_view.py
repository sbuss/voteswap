from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django.test import TestCase
import json

from users.models import PairProposal
from users.tests.factories import UserFactory
from users.views import propose_swap

HTTP_OK = 200


class TestProposeSwapView(TestCase):
    def setUp(self):
        super(TestProposeSwapView, self).setUp()
        self.request = RequestFactory()

    def test_success(self):
        user = UserFactory.create()
        match = UserFactory.create()
        user.profile.friends.add(match.profile)
        request = self.request.post(
            reverse('users:propose_swap'),
            {'to_profile': match.profile.id})
        request.user = user
        self.assertFalse(PairProposal.objects.all())
        response = propose_swap(request)
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertEqual(response.content,
                         json.dumps({'status': 'ok', 'errors': []}))
        proposal = PairProposal.objects.get(from_profile=user.profile)
        self.assertTrue(proposal)
        self.assertEqual(proposal.to_profile, match.profile)
