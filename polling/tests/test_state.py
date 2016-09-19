import datetime
from django.utils import timezone
from django.test import TestCase

from polling.models import State
from polling.models import STATES
from polling.tests.factories import StateFactory


class TestStateManager(TestCase):
    def test_latest(self):
        yesterday = timezone.now() - datetime.timedelta(days=1)
        StateFactory.create(name='California', updated=yesterday)
        state2 = StateFactory.create(name='California')
        self.assertEqual(len(State.objects.all()), 1)
        self.assertEqual(len(State.all_objects.all()), 2)
        self.assertEqual(list(State.objects.all()), [state2])

    def test_latest_multiple_states(self):
        yesterday = timezone.now() - datetime.timedelta(days=1)
        StateFactory.create(name='California', updated=yesterday)
        ca = StateFactory.create(name='California')
        StateFactory.create(name='Florida', updated=yesterday)
        fl = StateFactory.create(name='Florida')
        states = State.objects.all()
        self.assertEqual(len(states), 2)
        self.assertEqual(len(State.all_objects.all()), 4)
        self.assertEqual(set(State.objects.all()), set([ca, fl]))

    def test_latest_states(self):
        sorted_states = sorted([state[0] for state in STATES])
        for i in range(5):
            for i in range(127):
                StateFactory.create()
            self.assertEqual(
                sorted(list(State.objects.values_list('name', flat=True))),
                sorted_states)
