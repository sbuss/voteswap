from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from django.db.models import Q
import us

from polling.models import CANDIDATES

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

    def active(self):
        return self.get_queryset().filter(active=True)

    def inactive(self):
        return self.get_queryset().filter(active=False)

    def unpaired(self):
        return self.active().filter(_paired_with=None)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True)
    # TODO: populate fb_name with facebook name
    fb_name = models.CharField(max_length=255, null=True)
    fb_id = models.CharField(max_length=255, null=True)
    active = models.BooleanField(default=False)
    state = models.CharField(max_length=255, choices=STATES, null=True)
    preferred_candidate = models.CharField(
        max_length=255, choices=CANDIDATES, null=True)
    second_candidate = models.CharField(
        max_length=255, choices=CANDIDATES, null=True, blank=True)
    reason = models.TextField(null=True, blank=True)  # Why a user is swapping
    # Pairing with a User might be more technically correct, but then that
    # requires us to JOIN against the users table when trying to get the
    # user's information we actually care about
    _paired_with = models.ManyToManyField(
        'self', symmetrical=True)
    friends = models.ManyToManyField('self', symmetrical=True)

    objects = ProfileManager()

    def _all_friends(self, unpaired=False):
        # TODO Raw SQL query is faster
        # TODO Do I even need this?
        direct_friend_ids = self.friends.all().values_list('id', flat=True)
        all_friend_ids = self.friends.through.objects.filter(
            Q(from_profile_id=self.id) |
            Q(from_profile_id__in=direct_friend_ids)).values_list(
                'id', flat=True)
        if unpaired:
            return (Profile.objects.unpaired()
                    .filter(id__in=all_friend_ids)
                    .exclude(id=self.id))
        else:
            return (Profile.objects
                    .filter(id__in=all_friend_ids)
                    .exclude(id=self.id))

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

    def clean(self):
        if self.active and not self.user:
            raise ValidationError(
                "Cannot create an active profile for a user who has not "
                "authorized Facebook login.")
        if self.preferred_candidate == self.second_candidate:
            raise ValidationError("Your candidate choices cannot be the same.")

    def __repr__(self):
        return "<Profile: user:{user}, state:{state}, pc:{pc}, sc:{sc}, pair:{pair}>".format(  # NOQA
                user=self.user,
                state=self.state,
                pc=self.preferred_candidate,
                sc=self.second_candidate,
                pair=repr(getattr(self.paired_with, 'user', None)))
