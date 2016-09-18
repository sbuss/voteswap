from django.contrib.auth import get_user_model
from django.test import TestCase

from users.models import Profile
from users.tests.factories import ProfileFactory
from users.tests.factories import UserFactory
from polling.models import CANDIDATE_CLINTON
from polling.models import CANDIDATE_JOHNSON
from polling.tests.factories import StateFactory
from voteswap.forms import LandingPageForm


class TestLandingPageForm(TestCase):
    def setUp(self):
        super(TestLandingPageForm, self).setUp()
        self.state = StateFactory.create(name='California')

    def _data(self, **kwargs):
        data = {'preferred_candidate': CANDIDATE_CLINTON,
                'second_candidate': '',
                'state': 'California',
                'reason': ''}
        data.update(**kwargs)
        return data

    def test_preferred_candidate_major_party(self):
        form = LandingPageForm(
            data=self._data(preferred_candidate=CANDIDATE_CLINTON))
        self.assertTrue(form.is_valid())

    def test_major_party_swing(self):
        self.state.tipping_point_rank = 1
        self.state.save()
        form = LandingPageForm(
            data=self._data(preferred_candidate=CANDIDATE_CLINTON))
        self.assertTrue(form.is_valid())

    def test_third_party_swing(self):
        """Ensure that second_candidate is required if state is swing."""
        self.state.tipping_point_rank = 1
        self.state.save()
        form = LandingPageForm(
            data=self._data(
                preferred_candidate=CANDIDATE_JOHNSON,
            ))
        self.assertFalse(form.is_valid())

        form = LandingPageForm(
            data=self._data(
                preferred_candidate=CANDIDATE_JOHNSON,
                second_candidate=CANDIDATE_CLINTON,
            ))
        self.assertTrue(form.is_valid())

    def test_save_no_profile(self):
        """Ensure saving the form creates a profile for a user."""
        user = UserFactory.create(profile=None)
        reason = 'because'
        data = self._data(
            preferred_candidate=CANDIDATE_JOHNSON,
            second_candidate=CANDIDATE_CLINTON,
            reason=reason)
        form = LandingPageForm(data=data)
        self.assertTrue(form.is_valid())
        form.save(user)
        user = get_user_model().objects.get(id=user.id)
        self.assertEqual(user.profile.state, data['state'])
        self.assertEqual(user.profile.preferred_candidate,
                         data['preferred_candidate'])
        self.assertEqual(user.profile.second_candidate,
                         data['second_candidate'])
        self.assertEqual(user.profile.reason,
                         data['reason'])
        self.assertTrue(user.profile.active)
        self.assertNotEqual(user.profile.fb_id, '')
        self.assertEqual(user.profile.fb_id, user.social_auth.get().uid)

    def test_save_profile(self):
        """A profile may exist for a FB user, without a db User."""
        user = UserFactory.create(profile=None)
        profile = ProfileFactory.create(fb_id=user.social_auth.get().uid)
        self.assertFalse(profile.active)
        data = self._data()
        form = LandingPageForm(data=data)
        self.assertTrue(form.is_valid())
        form.save(user)
        user = get_user_model().objects.get(id=user.id)
        profile = Profile.objects.get(id=profile.id)
        self.assertEqual(user.profile, profile)
        self.assertTrue(user.profile.active)
        self.assertEqual(user.profile.fb_id, user.social_auth.get().uid)
