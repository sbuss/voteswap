from django.db.models import Q
import logging

from polling.models import State
from polling.models import CANDIDATE_CLINTON
from polling.models import CANDIDATE_JOHNSON
from polling.models import CANDIDATE_STEIN
from polling.models import CANDIDATE_NONE
from polling.models import CANDIDATES_MAIN
from polling.models import CANDIDATES_THIRD_PARTY
from users.models import PairProposal
from users.models import Profile

logger = logging.getLogger(__name__)

COMPATIBLE_CANDIDATES = {
    CANDIDATE_JOHNSON: [CANDIDATE_CLINTON],
    CANDIDATE_STEIN: [CANDIDATE_CLINTON],
    CANDIDATE_CLINTON: [CANDIDATE_JOHNSON, CANDIDATE_STEIN],
}


class FriendMatch(object):
    def __init__(self, profile, through=None, is_random=False):
        self.profile = profile
        self.through = through
        self.is_random = is_random

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


def _random_matches(profile, found_friends, potential_states):
    matches = Profile.objects.exclude(
        id__in=[profile.id]+[ff.id for ff in found_friends]).filter(
            allow_random=True,
            state__in=potential_states,
            preferred_candidate__in=COMPATIBLE_CANDIDATES[profile.preferred_candidate])  # NOQA
    return [FriendMatch(prof, is_random=True) for prof in matches]


def _matches_for_swing_state_profile(
        profile, direct=True, foaf=True, exclude_pending=True):
    """Find the suitable matches for a swing state profile"""
    found_friends = set()
    logger.info(
        ("[swing] Getting matches for swing-state profile %s. "
         "direct: %s, foaf: %s, exclude_pending: %s"),
        profile, direct, foaf, exclude_pending)

    def _get_friends(for_profile):
        through = None if profile == for_profile else for_profile
        new_matches = set()
        for matched_profile in for_profile.friends.unpaired().exclude(
                id=profile.id).filter(
                    state__in=potential_states,
                    preferred_candidate__in=COMPATIBLE_CANDIDATES[profile.preferred_candidate]):  # NOQA
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
        logger.info("[swing] Adding direct friends")
        matches.extend(_order_matches_by_state_rank(
            _get_friends(profile), potential_states))
    if foaf:
        logger.info("[swing] Adding foafs")
        foaf_friends = set()
        for friend in profile.friends.all():
            foaf_friends = foaf_friends.union(_get_friends(friend))
        matches.extend(_order_matches_by_state_rank(
            foaf_friends, potential_states))
    if profile.allow_random:
        matches.extend(
            _order_matches_by_state_rank(
                _random_matches(profile, found_friends, potential_states),
                potential_states))
    matches = _exclude_matches(
        PairProposal.objects.rejected(), profile, matches)
    if exclude_pending:
        logger.info("[swing] Excluding pending matches")
        matches = _exclude_matches(
            PairProposal.objects.pending(), profile, matches)
    logger.info("[swing] Found %s matches for %s", len(matches), profile)
    return matches


def _matches_for_safe_state_profile(
        profile, direct=True, foaf=True, exclude_pending=True):
    """Find the suitable matches for a safe state profile"""
    found_friends = set()
    logger.info(
        ("[safe] Getting matches for safe-state profile %s. "
         "direct: %s, foaf: %s, exclude_pending: %s"),
        profile, direct, foaf, exclude_pending)

    def _get_friends(for_profile):
        through = None if profile == for_profile else for_profile
        new_matches = set()
        for matched_profile in for_profile.friends.unpaired().exclude(
                id=profile.id).filter(
                    state__in=potential_states,
                    preferred_candidate__in=COMPATIBLE_CANDIDATES[profile.preferred_candidate]):  # NOQA
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
        logger.info("[safe] Adding direct friends")
        matches.extend(_order_matches_by_state_rank(
            _get_friends(profile), potential_states))
    if foaf:
        logger.info("[safe] Adding foafs")
        foaf_friends = set()
        for friend in profile.friends.all():
            foaf_friends = foaf_friends.union(_get_friends(friend))
        matches.extend(_order_matches_by_state_rank(
            foaf_friends, potential_states))
    if profile.allow_random:
        matches.extend(
            _order_matches_by_state_rank(
                _random_matches(profile, found_friends, potential_states),
                potential_states))
    matches = _exclude_matches(
        PairProposal.objects.rejected(), profile, matches)
    if exclude_pending:
        logger.info("[safe] Excluding pending matches")
        matches = _exclude_matches(
            PairProposal.objects.pending(), profile, matches)
    logger.info("[safe] Found %s matches for %s", len(matches), profile)
    return matches


def get_friend_matches(profile, exclude_pending=True):
    """Find suitable matches for the given profile.

    Match critera:
      * safe state <-> swing states
      * candidate != my candidate
    """
    logger.info("Get friend matches for profile %s, exlude_pending: %s",
                profile, exclude_pending)
    state = State.objects.get(name=profile.state)
    if state.is_swing:
        logger.info("%s is a swing state", state.name)
        if profile.preferred_candidate in dict(CANDIDATES_MAIN):
            # The user shouldn't change their vote
            logger.info(
                ("%s shouldn't swap because they're a Clinton voter"
                 "in a swing state"),
                profile)
            return NoMatchNecessary()
        return _matches_for_swing_state_profile(
            profile, exclude_pending=exclude_pending)
    else:
        logger.info("%s is a safe state", state.name)
        # In a safe state
        if profile.preferred_candidate in dict(CANDIDATES_THIRD_PARTY):
            # The user shouldn't change their vote
            logger.info(
                ("%s shouldn't swap because they're a third-party voter"
                 "in a safe state"),
                profile)
            return NoMatchNecessary()
        return _matches_for_safe_state_profile(
            profile, exclude_pending=exclude_pending)
