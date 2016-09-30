from django.contrib.auth import get_user_model
from django.test import TestCase

from users.models import Profile
from users.tests.factories import ProfileFactory
from users.tests.factories import UserFactory
from polling.models import CANDIDATE_CLINTON
from polling.models import CANDIDATE_JOHNSON
from polling.models import CANDIDATE_STEIN
from polling.tests.factories import StateFactory
from voteswap.forms import LandingPageForm


class TestLandingPageForm(TestCase):
    def setUp(self):
        super(TestLandingPageForm, self).setUp()
        self.state = StateFactory.create(name='California')

    def _data(self, **kwargs):
        data = {'preferred_candidate': CANDIDATE_CLINTON,
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

    def _test_valid(self, candidate):
        user = UserFactory.create(profile=None)
        data = self._data(preferred_candidate=candidate)
        form = LandingPageForm(data=data)
        self.assertTrue(form.is_valid())
        form.save(user)
        self.assertEqual(user.profile.preferred_candidate, candidate)

    def test_valid_clinton(self):
        self._test_valid(CANDIDATE_CLINTON)

    def test_valid_johnson(self):
        self._test_valid(CANDIDATE_JOHNSON)

    def test_valid_stein(self):
        self._test_valid(CANDIDATE_STEIN)

    def test_save_no_profile(self):
        """Ensure saving the form creates a profile for a user."""
        user = UserFactory.create(profile=None)
        reason = 'because'
        data = self._data(
            preferred_candidate=CANDIDATE_JOHNSON,
            reason=reason)
        form = LandingPageForm(data=data)
        self.assertTrue(form.is_valid())
        form.save(user)
        user = get_user_model().objects.get(id=user.id)
        self.assertEqual(user.profile.state, data['state'])
        self.assertEqual(user.profile.preferred_candidate,
                         data['preferred_candidate'])
        self.assertEqual(user.profile.reason,
                         data['reason'])
        self.assertNotEqual(user.profile.fb_id, '')
        self.assertEqual(user.profile.fb_id, user.social_auth.get().uid)

    def test_save_profile(self):
        """A profile may exist for a FB user, without a db User.

        This *should* never happen in practice, but it might happen if the
        user sign up flow screws up. Or it may happen if I change the sign up
        flow to log in with facebook first, before declaring votes.
        """
        user = UserFactory.create(profile=None)
        self.assertFalse(getattr(user, 'profile', False))
        profile = ProfileFactory.create(fb_id=user.social_auth.get().uid)
        self.assertFalse(getattr(profile, 'user', False))
        data = self._data()
        form = LandingPageForm(data=data)
        self.assertTrue(form.is_valid())
        form.save(user)
        user = get_user_model().objects.get(id=user.id)
        profile = Profile.objects.get(id=profile.id)
        self.assertEqual(user.profile, profile)
        self.assertEqual(user.profile.fb_id, user.social_auth.get().uid)

    def test_save_update_name_user_only(self):
        user = UserFactory.create(profile=None)
        data = self._data()
        form = LandingPageForm(data=data)
        self.assertTrue(form.is_valid())
        form.save(user)
        user = get_user_model().objects.get(id=user.id)
        self.assertEqual(user.get_full_name(), user.profile.fb_name)

    def test_save_update_name_user_and_profile(self):
        profile_fb_name = "foobar"
        user = UserFactory.create(profile__fb_name=profile_fb_name)
        data = self._data()
        form = LandingPageForm(data=data)
        self.assertTrue(form.is_valid())
        form.save(user)
        user = get_user_model().objects.get(id=user.id)
        self.assertNotEqual(user.get_full_name(), user.profile.fb_name)
        self.assertEqual(user.profile.fb_name, profile_fb_name)

    def test_save_update_name_user_and_profile_unlinked(self):
        fb_id = 1234
        user = UserFactory.create(profile=None, social_auth__uid=fb_id)
        profile = ProfileFactory.create(fb_id=fb_id)
        data = self._data()
        form = LandingPageForm(data=data)
        self.assertTrue(form.is_valid())
        form.save(user)
        user = get_user_model().objects.get(id=user.id)
        self.assertNotEqual(user.get_full_name(), user.profile.fb_name)
        self.assertEqual(user.profile, profile)

    def test_dont_delete_profile(self):
        """From a bug where the user's profile was deleted after updating."""
        user = UserFactory.create(profile__fb_id=1, social_auth__uid=1)
        profile = user.profile
        # Add a friend
        friend = UserFactory.create(profile__fb_id=2, social_auth__uid=2)
        profile.friends.add(friend.profile)
        data = self._data()
        form = LandingPageForm(data=data)
        self.assertTrue(form.is_valid())
        form.save(user)
        user = get_user_model().objects.get(id=user.id)
        self.assertEqual(user.profile.id, profile.id)
        self.assertEqual(profile.friends.get(), friend.profile)
