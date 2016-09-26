from django.db.models import Q

from polling.models import State
from polling.models import CANDIDATE_CLINTON
from polling.models import CANDIDATE_JOHNSON
from polling.models import CANDIDATE_NONE
from polling.models import CANDIDATES_MAIN
from polling.models import CANDIDATES_THIRD_PARTY
from users.models import PairProposal


class FriendMatch(object):
    def __init__(self, profile, through=None):
        self.profile = profile
        self.through = through

    @property
    def is_direct(self):
        return self.through is None


class NoMatchNecessary(object):
    pass


def _order_matches_by_state_rank(matches, ordered_states):
    """Order the list of matches by state rank."""
    keyfunc = lambda friend_match: ordered_states.index(
        friend_match.profile.state)
    return sorted(matches, key=keyfunc)


def _exclude_matches(proposal_qs, profile, matches):
    exclude_matches = set()
    for proposal in (
            proposal_qs
            .filter(Q(from_profile=profile) | Q(to_profile=profile))):
        exclude_matches.add(proposal.from_profile)
        exclude_matches.add(proposal.to_profile)
    if exclude_matches:
        return [match for match in matches
                if match.profile not in exclude_matches]
    return matches


def _matches_for_swing_state_profile(
        profile, direct=True, foaf=True, exclude_pending=True):
    """Find the suitable matches for a swing state profile"""
    found_friends = set()
    compatible_candidate = (
        CANDIDATE_CLINTON
        if profile.preferred_candidate == CANDIDATE_JOHNSON
        else CANDIDATE_JOHNSON)

    def _get_friends(for_profile):
        through = None if profile == for_profile else for_profile
        new_matches = set()
        for matched_profile in for_profile.friends.unpaired().exclude(
                id=profile.id).filter(
                    state__in=potential_states,
                    preferred_candidate=compatible_candidate):
            if matched_profile in found_friends:
                # Don't double add
                continue
            found_friends.add(matched_profile)
            new_matches.add(FriendMatch(matched_profile, through))
        return new_matches

    potential_states = list(
        State.objects
        .exclude(safe_rank=-1)
        .order_by('safe_rank')
        .values_list('name', flat=True)
    )
    matches = list()
    if direct:
        matches.extend(_order_matches_by_state_rank(
            _get_friends(profile), potential_states))
    if foaf:
        foaf_friends = set()
        for friend in profile.friends.all():
            foaf_friends = foaf_friends.union(_get_friends(friend))
        matches.extend(_order_matches_by_state_rank(
            foaf_friends, potential_states))
    matches = _exclude_matches(
        PairProposal.objects.rejected(), profile, matches)
    if exclude_pending:
        matches = _exclude_matches(
            PairProposal.objects.pending(), profile, matches)
    return matches


def _matches_for_safe_state_profile(
        profile, direct=True, foaf=True, exclude_pending=True):
    """Find the suitable matches for a safe state profile"""
    found_friends = set()
    compatible_candidate = (
        CANDIDATE_CLINTON
        if profile.preferred_candidate == CANDIDATE_JOHNSON
        else CANDIDATE_JOHNSON)

    def _get_friends(for_profile):
        through = None if profile == for_profile else for_profile
        new_matches = set()
        for matched_profile in for_profile.friends.unpaired().exclude(
                id=profile.id).filter(
                    state__in=potential_states,
                    preferred_candidate=compatible_candidate):
            if matched_profile in found_friends:
                continue
            found_friends.add(matched_profile)
            new_matches.add(FriendMatch(matched_profile, through))
        return new_matches

    potential_states = list(
        State.objects
        .filter(safe_for=CANDIDATE_NONE)
        .exclude(tipping_point_rank=-1)
        .order_by('tipping_point_rank')
        .values_list('name', flat=True)
    )
    matches = list()
    if direct:
        matches.extend(_order_matches_by_state_rank(
            _get_friends(profile), potential_states))
    if foaf:
        foaf_friends = set()
        for friend in profile.friends.all():
            foaf_friends = foaf_friends.union(_get_friends(friend))
        matches.extend(_order_matches_by_state_rank(
            foaf_friends, potential_states))
    matches = _exclude_matches(
        PairProposal.objects.rejected(), profile, matches)
    if exclude_pending:
        matches = _exclude_matches(
            PairProposal.objects.pending(), profile, matches)
    return matches


def get_friend_matches(profile, exclude_pending=True):
    """Find suitable matches for the given profile.

    Match critera:
      * safe state <-> swing states
      * candidate != my candidate
    """
    state = State.objects.get(name=profile.state)
    if state.is_swing:
        if profile.preferred_candidate in dict(CANDIDATES_MAIN):
            # The user shouldn't change their vote
            return NoMatchNecessary()
        return _matches_for_swing_state_profile(
            profile, exclude_pending=exclude_pending)
    else:
        # In a safe state
        if profile.preferred_candidate in dict(CANDIDATES_THIRD_PARTY):
            # The user shouldn't change their vote
            return NoMatchNecessary()
        return _matches_for_safe_state_profile(
            profile, exclude_pending=exclude_pending)
