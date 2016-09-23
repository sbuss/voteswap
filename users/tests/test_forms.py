from django.test import TestCase

from users.forms import PairProposalForm
from users.models import PairProposal
from users.models import Profile
from users.tests.factories import ProfileFactory


class TestPairProposalForm(TestCase):
    def test_no_friends_invalid(self):
        profile = ProfileFactory.create()
        form = PairProposalForm(profile)
        self.assertFalse(form.is_valid())

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
