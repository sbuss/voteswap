from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django.test import TestCase
from mock import patch

from polling.tests.factories import StateFactory
from users.views import confirm_swap
from users.models import PairProposal
from users.models import Profile
from users.tests.factories import ProfileFactory
from users.tests.factories import UserFactory

HTTP_REDIRECT = 302


class TestConfirmSwapView(TestCase):
    def setUp(self):
        super(TestConfirmSwapView, self).setUp()
        self.request = RequestFactory()
        from_state = StateFactory.create(tipping_point_rank=1)
        self.from_profile = UserFactory.create(
            profile__state=from_state.name).profile
        to_state = StateFactory.create(safe_rank=1)
        self.to_profile = UserFactory.create(
            profile__state=to_state.name).profile
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
        request = self.request.post(
            reverse('users:confirm_swap', args=[self.proposal.ref_id]),
            data={})
        request.user = self.to_profile.user
        response = confirm_swap(request, self.proposal.ref_id)
        self.assertEqual(response.status_code, HTTP_REDIRECT)
        self.assertTrue(response.has_header('Location'))
        self.assertEqual(response.get('Location'),
                         reverse('users:profile'))
        from_profile = Profile.objects.get(id=self.from_profile.id)
        to_profile = Profile.objects.get(id=self.to_profile.id)
        self.assertEqual(from_profile.paired_with, to_profile)
        self.assertEqual(list(self.other_profile.all_unpaired_friends), [])

    def test_data_doesnt_matter(self):
        """POSTed data to this view gets ignored"""
        data = {'from_profile': -1, 'to_profile': 9999}
        request = self.request.post(
            reverse('users:confirm_swap', args=[self.proposal.ref_id]),
            data=data)
        request.user = self.to_profile.user
        response = confirm_swap(request, self.proposal.ref_id)
        self.assertEqual(response.status_code, HTTP_REDIRECT)
        self.assertTrue(response.has_header('Location'))
        self.assertEqual(response.get('Location'),
                         reverse('users:profile'))
        from_profile = Profile.objects.get(id=self.from_profile.id)
        to_profile = Profile.objects.get(id=self.to_profile.id)
        self.assertEqual(from_profile.paired_with, to_profile)
        self.assertEqual(list(self.other_profile.all_unpaired_friends), [])

    def test_invalid_proposal_id(self):
        """Giving a proposal for a different user gives an error"""
        new_profile = ProfileFactory.create()
        other_proposal = PairProposal.objects.create(
            from_profile=self.other_profile,
            to_profile=new_profile)
        request = self.request.post(
            reverse('users:confirm_swap', args=[other_proposal.ref_id]),
            data={})
        request.user = self.to_profile.user
        response = confirm_swap(request, other_proposal.ref_id)
        self.assertContains(response, 'Invalid swap proposal')
