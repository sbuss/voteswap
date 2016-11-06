from django.http.request import QueryDict
from django.test import TestCase

from users.forms import ConfirmPairProposalForm
from users.forms import PairProposalForm
from users.forms import RejectPairProposalForm
from users.models import PairProposal
from users.models import Profile
from users.tests.factories import ProfileFactory


class TestPairProposalForm(TestCase):
    def test_no_friends_invalid(self):
        profile = ProfileFactory.create()
        form = PairProposalForm(profile)
        self.assertFalse(form.is_valid())

    def test_querydict(self):
        ProfileFactory.create()
        profile = ProfileFactory.create()
        friends = [ProfileFactory.create() for x in range(2)]
        profile.friends.add(*friends)

        form = PairProposalForm(
            profile, data=QueryDict(
                'from_profile=%s&to_profile=%s' % (profile.id, friends[0].id)))
        self.assertEqual(
            form.fields['from_profile'].queryset.get(), profile)
        self.assertEqual(
            set(form.fields['to_profile'].queryset.all()),
            set(friends))

    def test_friends_queryset(self):
        ProfileFactory.create()
        profile = ProfileFactory.create()
        friends = [ProfileFactory.create() for x in range(2)]
        profile.friends.add(*friends)

        form = PairProposalForm(profile, data={'to_profile': friends[0].id})
        self.assertEqual(
            form.fields['from_profile'].queryset.get(), profile)
        self.assertEqual(
            set(form.fields['to_profile'].queryset),
            set(Profile.objects.filter(
                id__in=[friend.id for friend in friends])))
        self.assertTrue(form.is_valid())

    def test_no_paired_friends(self):
        profile = ProfileFactory.create()
        friend = ProfileFactory.create()
        profile.friends.add(friend)
        paired_friend = ProfileFactory.create()
        paired_friend.paired_with = ProfileFactory.create()
        profile.friends.add(paired_friend)
        form = PairProposalForm(profile, data={'to_profile': friend.id})
        self.assertEqual(
            form.fields['from_profile'].queryset.get(), profile)
        self.assertEqual(
            set(form.fields['to_profile'].queryset),
            set(Profile.objects.filter(id=friend.id)))
        self.assertTrue(form.is_valid())

    def test_valid(self):
        profile = ProfileFactory.create()
        friend = ProfileFactory.create()
        profile.friends.add(friend)
        form = PairProposalForm(profile, data={'to_profile': friend.id})
        self.assertEqual(len(PairProposal.objects.all()), 0)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(len(PairProposal.objects.all()), 1)
        proposal = PairProposal.objects.get()
        self.assertEqual(proposal.from_profile, profile)
        self.assertEqual(proposal.to_profile, friend)

    def test_friends_of_friends(self):
        profile = ProfileFactory.create()
        # Start with no friends
        self.assertQuerysetEqual(
            profile.friends.all(),
            profile.all_unpaired_friends)
        friend = ProfileFactory.create()
        profile.friends.add(friend)
        # Add a friend and make sure it's there
        self.assertEqual(
            friend,
            profile.all_unpaired_friends.get())
        foaf = ProfileFactory.create()
        # After creating another profile, it isn't yet a friend
        self.assertEqual(
            friend,
            profile.all_unpaired_friends.get())
        friend.friends.add(foaf)
        # But after adding it as a friend of my friend, I can see it
        self.assertEqual(
            set([friend, foaf]),
            set(profile.all_unpaired_friends))
        # But won't see friends-of-friends-of-friends
        foaf.friends.add(ProfileFactory.create())
        self.assertEqual(
            set([friend, foaf]),
            set(profile.all_unpaired_friends))

    def test_random(self):
        profile = ProfileFactory.create(allow_random=True)
        friend = ProfileFactory.create()
        profile.friends.add(friend)
        # Add a friend and make sure it's there
        self.assertEqual(
            friend,
            profile.all_unpaired_friends.get())
        rando = ProfileFactory.create(allow_random=True)
        # The rando also accepts random friends, so it should show up as an
        # unpaired friend
        self.assertEqual(
            set([friend, rando]),
            set(profile.all_unpaired_friends))
        form = PairProposalForm(profile, data={'to_profile': rando.id})
        self.assertEqual(len(PairProposal.objects.all()), 0)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(len(PairProposal.objects.all()), 1)
        proposal = PairProposal.objects.get()
        self.assertEqual(proposal.from_profile, profile)
        self.assertEqual(proposal.to_profile, rando)


class _TestConfirmOrRejectPairProposalForm(TestCase):
    def setUp(self):
        self.from_profile = ProfileFactory.create()
        self.to_profile = ProfileFactory.create()
        self.other_profile = ProfileFactory.create()
        self.from_profile.friends.add(self.to_profile)
        self.from_profile.friends.add(self.other_profile)
        self.proposal = PairProposal.objects.create(
            from_profile=self.from_profile,
            to_profile=self.to_profile)


class TestConfirmPairProposalForm(_TestConfirmOrRejectPairProposalForm):
    def _data(self):
        return {'from_profile': self.proposal.from_profile.id,
                'to_profile': self.proposal.to_profile.id}

    def test_confirm_success(self):
        form = ConfirmPairProposalForm(
            data=self._data(), instance=self.proposal)
        self.assertTrue(form.is_valid())
        form.save()
        from_profile = Profile.objects.get(id=self.from_profile.id)
        to_profile = Profile.objects.get(id=self.to_profile.id)
        self.assertEqual(from_profile.paired_with, to_profile)
        self.assertEqual(list(self.other_profile.all_unpaired_friends), [])
        self.assertFalse(PairProposal.objects.pending())
        self.assertFalse(PairProposal.objects.rejected())
        self.assertEqual(
            list(PairProposal.objects.confirmed()),
            [self.proposal])

    def test_confirm_fail(self):
        data = self._data().update({'to_profile': self.other_profile.id})
        form = ConfirmPairProposalForm(
            data=data, instance=self.proposal)
        self.assertFalse(form.is_valid())

    def test_random(self):
        profile = ProfileFactory.create(allow_random=True)
        rando = ProfileFactory.create(allow_random=True)
        form = PairProposalForm(profile, data={'to_profile': rando.id})
        self.assertTrue(form.is_valid())
        form.save()
        self.proposal = profile.proposals_made.get()
        form = ConfirmPairProposalForm(
            data=self._data(), instance=self.proposal)
        self.assertTrue(form.is_valid())
        form.save()


class TestRejectPairProposalForm(_TestConfirmOrRejectPairProposalForm):
    def _data(self):
        return {'from_profile': self.proposal.from_profile.id,
                'to_profile': self.proposal.to_profile.id,
                'reason_rejected': "I don't trust that guy"}

    def test_reject_success(self):
        form = RejectPairProposalForm(
            data=self._data(), instance=self.proposal)
        self.assertTrue(form.is_valid())
        form.save()
        from_profile = Profile.objects.get(id=self.from_profile.id)
        to_profile = Profile.objects.get(id=self.to_profile.id)
        self.assertFalse(from_profile.paired_with)
        self.assertFalse(to_profile.paired_with)
        self.assertEqual(
            set(self.other_profile.all_unpaired_friends),
            set([from_profile, to_profile]))
        self.assertFalse(PairProposal.objects.pending())
        self.assertFalse(PairProposal.objects.confirmed())
        self.assertEqual(
            list(PairProposal.objects.rejected()),
            [self.proposal])

    def test_random(self):
        profile = ProfileFactory.create(allow_random=True)
        rando = ProfileFactory.create(allow_random=True)
        form = PairProposalForm(profile, data={'to_profile': rando.id})
        self.assertTrue(form.is_valid())
        form.save()
        self.proposal = profile.proposals_made.get()
        form = RejectPairProposalForm(
            data=self._data(), instance=self.proposal)
        self.assertTrue(form.is_valid())
        form.save()
