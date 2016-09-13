from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.db import transaction
import us

from polling.models import CANDIDATES

STATES = [(state.name, state.name) for state in us.STATES]


class Profile(models.Model):
    user = models.OneToOneField(User)
    state = models.CharField(max_length=255, choices=STATES)
    preferred_candidate = models.CharField(max_length=255, choices=CANDIDATES)
    second_candidate = models.CharField(max_length=255, choices=CANDIDATES)
    # Pairing with a User might be more technically correct, but then that
    # requires us to JOIN against the users table when trying to get the
    # user's information we actually care about
    _paired_with = models.ForeignKey(
        'self', null=True, on_delete=models.SET_NULL)

    def get_pair(self):
        return self._paired_with

    @transaction.atomic
    def set_pair(self, value):
        self._paired_with = value
        value._paired_with = self
        value.save()
        self.save()

    paired_with = property(get_pair, set_pair)
