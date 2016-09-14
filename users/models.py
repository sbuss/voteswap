from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
import us

from polling.models import CANDIDATES

STATES = [(state.name, state.name) for state in us.STATES]


class ProfileManager(models.Manager):
    def get_queryset(self):
        return super(ProfileManager, self).get_queryset().select_related(
            'user', '_paired_with__user')


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    state = models.CharField(max_length=255, choices=STATES)
    preferred_candidate = models.CharField(max_length=255, choices=CANDIDATES)
    second_candidate = models.CharField(max_length=255, choices=CANDIDATES)
    # Pairing with a User might be more technically correct, but then that
    # requires us to JOIN against the users table when trying to get the
    # user's information we actually care about
    _paired_with = models.ForeignKey(
        'self', null=True, on_delete=models.SET_NULL)

    objects = ProfileManager()

    def get_pair(self):
        return self._paired_with

    @transaction.atomic
    def set_pair(self, value):
        self._paired_with = value
        value._paired_with = self
        value.save()
        self.save()

    def clean(self):
        if self.preferred_candidate == self.second_candidate:
            raise ValidationError("Your candidate choices cannot be the same.")

    paired_with = property(get_pair, set_pair)

    def __repr__(self):
        return "<Profile: user:{user}, state:{state}, pc:{pc}, sc:{sc}, pair:{pair}>".format(  # NOQA
                user=self.user,
                state=self.state,
                pc=self.preferred_candidate,
                sc=self.second_candidate,
                pair=self._paired_with.user if self._paired_with else 'None')
