from django.test import TestCase

from users.tests.factories import UserFactory
from polling.models import State
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
                'state': 'California'}
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
