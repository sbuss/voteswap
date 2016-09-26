from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django.test import TestCase

from users.views import confirm_swap
from users.models import PairProposal
from users.models import Profile
from users.tests.factories import ProfileFactory
from users.tests.factories import UserFactory


class TestProposeSwapView(TestCase):
    def setUp(self):
        super(TestProposeSwapView, self).setUp()
        self.request = RequestFactory()
        self.from_profile = ProfileFactory.create()
        self.to_profile = UserFactory.create().profile
        self.other_profile = ProfileFactory.create()
        self.from_profile.friends.add(self.to_profile)
        self.from_profile.friends.add(self.other_profile)
        self.proposal = PairProposal.objects.create(
            from_profile=self.from_profile,
            to_profile=self.to_profile)

    def test_success(self):
        request = self.request.post(
            reverse('users:confirm_swap', args=[self.proposal.ref_id]),
            data={})
        request.user = self.to_profile.user
        response = confirm_swap(request, self.proposal.ref_id)
        self.assertEqual(response.content, '{"status": "ok", "errors": {}}')
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
        self.assertEqual(response.content, '{"status": "ok", "errors": {}}')
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
