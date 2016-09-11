from __future__ import unicode_literals

from django.db import models

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


CANDIDATE_CLINTON = 'clinton'
CANDIDATE_JOHNSON = 'johnson'
CANDIDATE_STEIN = 'stein'
CANDIDATE_TRUMP = 'trump'
CANDIDATE_NONE = 'none'
CANDIDATES = (
    (CANDIDATE_CLINTON, CANDIDATE_CLINTON.title()),
    (CANDIDATE_JOHNSON, CANDIDATE_JOHNSON.title()),
    (CANDIDATE_STEIN, CANDIDATE_STEIN.title()),
    (CANDIDATE_TRUMP, CANDIDATE_TRUMP.title()),
    (CANDIDATE_NONE, "No One"),
)

CANDIDATE_TO_PARTY = {
    CANDIDATE_CLINTON: PARTY_DEMOCRATIC,
    CANDIDATE_JOHNSON: PARTY_LIBERTARIAN,
    CANDIDATE_STEIN: PARTY_GREEN,
    CANDIDATE_TRUMP: PARTY_REPUBLICAN,
}


class State(models.Model):
    """All states (and districts) that can vote in federal elections."""
    name = models.CharField()
    updated = models.DateField()
    abbv = models.CharField()
    tipping_point_rank = models.IntegerField()
    safe_for = models.CharField(choices=CANDIDATES, default=CANDIDATE_NONE)
    safe_rank = models.IntegerField(default=-1)
    leans = models.CharField(choices=CANDIDATES, default=CANDIDATE_NONE)
    lean_rank = models.IntegerField(default=-1)

    class Meta:
        unique_together = ('name', 'updated')
