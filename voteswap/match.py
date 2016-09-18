from polling.models import State
from polling.models import CANDIDATE_NONE
from polling.models import CANDIDATES_MAIN
from polling.models import CANDIDATES_THIRD_PARTY


class NoMatchNecessary(object):
    pass


def _order_friends_by_state_rank(friends, ordered_states):
    """Order the list of friends by state rank."""
    keyfunc = lambda profile: ordered_states.index(profile.state)
    return sorted(friends, key=keyfunc)


def _friends_for_swing_state_user(user):
    """Find the suitable friends for a swing state user"""
    def _get_friends(profile):
        return set(
            profile.friends.unpaired()
            .filter(state__in=potential_states,
                    preferred_candidate=user.profile.second_candidate))
    potential_states = list(
        State.objects
        .order_by('safe_rank')
        .values_list('name', flat=True)
    )
    friends = _get_friends(user.profile)
    for friend in user.profile.friends.all():
        friends = friends.union(_get_friends(friend))
    return _order_friends_by_state_rank(friends, potential_states)


def _friends_for_safe_state_user(user):
    """Find the suitable friends for a safe state user"""
    def _get_friends(profile):
        return set(
            profile.friends.unpaired()
            .filter(state__in=potential_states,
                    second_candidate=user.profile.preferred_candidate))

    potential_states = list(
        State.objects
        .filter(safe_for=CANDIDATE_NONE)
        .order_by('tipping_point_rank')
        .values_list('name', flat=True)
    )
    friends = _get_friends(user.profile)
    for friend in user.profile.friends.all():
        friends = friends.union(_get_friends(friend))
    return _order_friends_by_state_rank(friends, potential_states)


def get_friend_matches(user):
    """Find suitable matches for the given user.

    Match critera:
      * safe state <-> swing states
      * primary <-> secondary choice match
    """
    state = State.objects.get(name=user.profile.state)
    if state.is_swing:
        if user.profile.preferred_candidate in dict(CANDIDATES_MAIN):
            # The user shouldn't change their vote
            return NoMatchNecessary()
        return _friends_for_swing_state_user(user)
    else:
        # In a safe state
        if user.profile.preferred_candidate in dict(CANDIDATES_THIRD_PARTY):
            # The user shouldn't change their vote
            return NoMatchNecessary()
        return _friends_for_safe_state_user(user)
