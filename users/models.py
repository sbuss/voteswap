from __future__ import unicode_literals

import base64
from django.conf import settings
from django.db import models
from django.db import transaction
from django.db.models import Q
import us
import uuid

from polling.models import CANDIDATES_ADVOCATED

STATES = [(state.name, state.name) for state in us.STATES]


class PairProposalManager(models.Manager):
    def pending(self):
        return self.get_queryset().filter(
            date_confirmed__isnull=True,
            date_rejected__isnull=True)

    def confirmed(self):
        return self.get_queryset().filter(date_confirmed__isnull=False)

    def rejected(self):
        return self.get_queryset().filter(date_rejected__isnull=False)


class PairProposal(models.Model):
    from_profile = models.ForeignKey(
        'Profile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='proposals_made')
    to_profile = models.ForeignKey(
        'Profile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='proposals_received')
    ref_id = models.UUIDField(primary_key=False, default=uuid.uuid4)
    date_proposed = models.DateTimeField(auto_now_add=True)
    date_confirmed = models.DateTimeField(null=True)
    date_rejected = models.DateTimeField(null=True)
    reason_rejected = models.TextField(null=True, blank=True)
    objects = PairProposalManager()

    def __repr__(self):
        return "<PairProposal: from:{from_p} to:{to_p} at:{when}>".format(
            from_p=repr(self.from_profile),
            to_p=repr(self.to_profile),
            when=self.date_proposed.isoformat())


class ProfileManager(models.Manager):
    def get_queryset(self):
        return (super(ProfileManager, self).get_queryset()
                .select_related('user')
                .prefetch_related('_paired_with__user'))

    def unpaired(self):
        return self.get_queryset().filter(_paired_with=None)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True)
    # TODO: populate fb_name with facebook name
    fb_name = models.CharField(max_length=255, null=True)
    fb_id = models.CharField(max_length=255, null=True)
    state = models.CharField(max_length=255, choices=STATES, null=True)
    preferred_candidate = models.CharField(
        max_length=255, choices=CANDIDATES_ADVOCATED, null=True)
    reason = models.TextField(null=True, blank=True)  # Why a user is swapping
    # Pairing with a User might be more technically correct, but then that
    # requires us to JOIN against the users table when trying to get the
    # user's information we actually care about
    _paired_with = models.ManyToManyField(
        'self', symmetrical=True)
    friends = models.ManyToManyField('self', symmetrical=True)

    objects = ProfileManager()

    def clean(self):
        self.reason = base64.b64encode(self.reason.encode('utf-8'))

    def _all_friends(self, unpaired=False):
        # TODO Raw SQL query is faster
        direct_friend_ids = self.friends.all().values_list('id', flat=True)
        all_friend_ids = self.friends.through.objects.filter(
            Q(from_profile_id=self.id) |
            Q(from_profile_id__in=direct_friend_ids)).values_list(
                'to_profile_id', flat=True)
        if unpaired:
            return (Profile.objects.unpaired()
                    .filter(id__in=all_friend_ids)
                    .exclude(id=self.id))
        else:
            return (Profile.objects
                    .filter(id__in=all_friend_ids)
                    .exclude(id=self.id))

    @property
    def reason_decoded(self):
        if self.reason:
            return base64.b64decode(self.reason).decode('utf-8')
        return ''

    @property
    def all_friends(self):
        return self._all_friends()

    @property
    def all_unpaired_friends(self):
        return self._all_friends(unpaired=True)

    @transaction.atomic
    def set_pair(self, other):
        if self._paired_with.all():
            self._paired_with.clear()
        self._paired_with.add(other)

    def get_pair(self):
        pair = self._paired_with.all()
        if pair:
            return pair[0]
        return None

    paired_with = property(get_pair, set_pair)

    def _is_paired(self):
        return self.paired_with is not None
    _is_paired.boolean = True
    is_paired = property(_is_paired)

    def __repr__(self):
        return "<Profile: user:{user}, state:{state}, cand:{candidate}, pair:{pair}>".format(  # NOQA
                user=self.user,
                state=self.state,
                candidate=self.preferred_candidate,
                pair=repr(getattr(self.paired_with, 'user', None)))
