from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django.test import TestCase
from mock import patch

from users.views import reject_swap
from users.models import PairProposal
from users.models import Profile
from users.tests.factories import ProfileFactory
from users.tests.factories import UserFactory

HTTP_REDIRECT = 302


class TestProposeSwapView(TestCase):
    def setUp(self):
        super(TestProposeSwapView, self).setUp()
        self.request = RequestFactory()
        self.from_profile = UserFactory.create().profile
        self.to_profile = UserFactory.create().profile
        self.other_profile = ProfileFactory.create()
        self.from_profile.friends.add(self.to_profile)
        self.from_profile.friends.add(self.other_profile)
        self.proposal = PairProposal.objects.create(
            from_profile=self.from_profile,
            to_profile=self.to_profile)
        self.email_patcher = patch('users.views.EmailMessage')
        self.mock_email_message_class = self.email_patcher.start()

    def tearDown(self):
        self.email_patcher.stop()

    def test_success(self):
        reason = 'foo'
        request = self.request.post(
            reverse('users:reject_swap', args=[self.proposal.ref_id]),
            data={'reason_rejected': reason})
        request.user = self.to_profile.user
        response = reject_swap(request, self.proposal.ref_id)
        self.assertEqual(response.status_code, HTTP_REDIRECT)
        self.assertTrue(response.has_header('Location'))
        self.assertEqual(response.get('Location'),
                         reverse('users:profile'))
        from_profile = Profile.objects.get(id=self.from_profile.id)
        to_profile = Profile.objects.get(id=self.to_profile.id)
        self.assertFalse(from_profile.paired_with)
        self.assertFalse(to_profile.paired_with)
        proposal = PairProposal.objects.get(id=self.proposal.id)
        self.assertEqual(proposal.reason_rejected, reason)

    def test_data_doesnt_matter(self):
        """POSTed data that isn't reason_rejected to this view gets ignored"""
        reason = 'because'
        data = {'from_profile': -1,
                'to_profile': 9999,
                'reason_rejected': reason}
        request = self.request.post(
            reverse('users:reject_swap', args=[self.proposal.ref_id]),
            data=data)
        request.user = self.to_profile.user
        response = reject_swap(request, self.proposal.ref_id)
        self.assertTrue(response.has_header('Location'))
        self.assertEqual(response.get('Location'),
                         reverse('users:profile'))
        from_profile = Profile.objects.get(id=self.from_profile.id)
        to_profile = Profile.objects.get(id=self.to_profile.id)
        self.assertFalse(from_profile.paired_with)
        self.assertFalse(to_profile.paired_with)
        proposal = PairProposal.objects.get(id=self.proposal.id)
        self.assertEqual(proposal.reason_rejected, reason)

    def test_invalid_proposal_id(self):
        """Giving a proposal for a different user gives an error"""
        new_profile = ProfileFactory.create()
        other_proposal = PairProposal.objects.create(
            from_profile=self.other_profile,
            to_profile=new_profile)
        request = self.request.post(
            reverse('users:reject_swap', args=[other_proposal.ref_id]),
            data={'reason_rejected': 'foo'})
        request.user = self.to_profile.user
        response = reject_swap(request, other_proposal.ref_id)
        self.assertContains(response, 'Invalid swap proposal')
