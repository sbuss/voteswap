from django.test import TestCase

from users.forms import PairProposalForm
from users.models import Profile
from users.tests.factories import ProfileFactory


class TestPairProposalForm(TestCase):
    def test_no_friends_invalid(self):
        profile = ProfileFactory.create(active=True)
        form = PairProposalForm(profile)
        self.assertFalse(form.is_valid())

    def test_friends_queryset(self):
        ProfileFactory.create(active=True)
        profile = ProfileFactory.create(active=True)
        friends = [ProfileFactory.create(active=True) for x in range(2)]
        profile.friends.add(*friends)

        form = PairProposalForm(profile, data={'to_profile': friends[0].id})
        self.assertEqual(
            form.fields['from_profile'].queryset.get(), profile)
        self.assertEqual(
            set(form.fields['to_profile'].queryset),
            set(Profile.objects.filter(
                id__in=[friend.id for friend in friends])))
        self.assertTrue(form.is_valid())
