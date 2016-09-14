from __future__ import unicode_literals

from django.db import models
import us

# Create your models here.


PARTY_DEMOCRATIC = 'democratic'
PARTY_GREEN = 'green'
PARTY_LIBERTARIAN = 'libertarian'
PARTY_REPUBLICAN = 'republican'

PARTIES = (
    (PARTY_DEMOCRATIC, PARTY_DEMOCRATIC.title()),
    (PARTY_GREEN, PARTY_GREEN.title()),
    (PARTY_LIBERTARIAN, PARTY_LIBERTARIAN.title()),
    (PARTY_REPUBLICAN, PARTY_REPUBLICAN.title()),
)


CANDIDATE_CLINTON = 'Clinton'
CANDIDATE_JOHNSON = 'Johnson'
CANDIDATE_STEIN = 'Stein'
CANDIDATE_TRUMP = 'Trump'
CANDIDATE_NONE = ''
CANDIDATES = (
    (CANDIDATE_CLINTON, CANDIDATE_CLINTON.title()),
    (CANDIDATE_JOHNSON, CANDIDATE_JOHNSON.title()),
    (CANDIDATE_STEIN, CANDIDATE_STEIN.title()),
    (CANDIDATE_TRUMP, CANDIDATE_TRUMP.title()),
)
CANDIDATES_OR_NONE = CANDIDATES + ((CANDIDATE_NONE, "No One"),)

CANDIDATE_TO_PARTY = {
    CANDIDATE_CLINTON: PARTY_DEMOCRATIC,
    CANDIDATE_JOHNSON: PARTY_LIBERTARIAN,
    CANDIDATE_STEIN: PARTY_GREEN,
    CANDIDATE_TRUMP: PARTY_REPUBLICAN,
}

STATES = [(state.name, state.name) for state in us.STATES]
ABBVS = [(state.abbr, state.abbr) for state in us.STATES]


class State(models.Model):
    """All states (and districts) that can vote in federal elections."""
    name = models.CharField(max_length=255, choices=STATES)
    updated = models.DateField()
    abbv = models.CharField(max_length=255, choices=ABBVS)
    tipping_point_rank = models.IntegerField()
    safe_for = models.CharField(
        max_length=255, choices=CANDIDATES_OR_NONE, default=CANDIDATE_NONE)
    safe_rank = models.IntegerField(default=-1)
    leans = models.CharField(
        max_length=255, choices=CANDIDATES_OR_NONE, default=CANDIDATE_NONE)
    lean_rank = models.IntegerField(default=-1)

    class Meta:
        unique_together = ('name', 'updated')

    @property
    def likely_winner(self):
        if self.safe_for:
            return "Safe %s" % self.safe_for
        elif self.tipping_point_rank != -1:
            return "Leans %s" % self.leans
        else:
            return "Toss Up"

    def __unicode__(self):
        return u"{name}: {likely_winner} ({updated})".format(
            name=self.name,
            likely_winner=self.likely_winner,
            updated=self.updated)

    def __repr__(self):
        if self.tipping_point_rank == -1:
            return (
                "<State(updated:{updated}, name:{name}, likely_winner:{likely_winner})>"  # NOQA
                .format(updated=self.updated,
                        name=self.name,
                        tpr=self.tipping_point_rank,
                        likely_winner=self.likely_winner))
        else:
            return (
                "<State(updated:{updated}, name:{name}, tipping_point_rank:{tpr}, likely_winner:{likely_winner})>"  # NOQA
                .format(updated=self.updated,
                        name=self.name,
                        tpr=self.tipping_point_rank,
                        likely_winner=self.likely_winner))


"""VOTER_TYPE_REGISTERED = 'registered'
VOTER_TYPE_LIKELY = 'likely'
VOTER_TYPES = (
    (VOTER_TYPE_REGISTERED, VOTER_TYPE_REGISTERED.title()),
    (VOTER_TYPE_LIKELY, VOTER_TYPE_LIKELY.title()),
)


class Polls(models.Model):
    candidate = models.CharField(choices=CANDIDATES)
    state = models.ForeignKey(State, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    sample_size = models.IntegerField()
    likelihood = models.DecimalField()
    voter_type = models.CharField(choices=VOTER_TYPES)"""
