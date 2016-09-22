from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.functional import cached_property

from polling.models import State
from voteswap.match import get_friend_matches


class ProfileContext(object):
    def __init__(self, profile):
        self.profile = profile
        self.pair_proposal_friend_ids = set(
            self.profile.proposals_made.values_list(
                'to_profile__id', flat=True))

    def has_proposed_to_friend(self, friend):
        return friend.id in self.pair_proposal_friend_ids

    @cached_property
    def good_potential_matches(self):
        return [FriendMatchContext(fm, self)
                for fm in get_friend_matches(self.profile)]


class FriendMatchContext(object):
    def __init__(self, friend_match, profile_context):
        self.friend_match = friend_match
        self.profile_context = profile_context

    @property
    def name(self):
        profile = self.friend_match.profile
        try:
            return profile.user.get_full_name()
        except:
            pass
        return profile.email

    @property
    def has_been_proposed_to(self):
        return self.profile_context.has_proposed_to_friend(
            self.friend_match.profile)

    @property
    def proposal_string(self):
        profile = self.friend_match.profile
        state = State.objects.get(name=profile.state)
        if state.is_swing:
            # If I'm a good match, then I must be voting for a third party
            # and I must have a second choice candidate
            return (
                "Will vote for {second_candidate} in {state} in exchange for "
                "your vote for {preferred_candidate} in {your_state}").format(
                    second_candidate=profile.second_candidate,
                    state=profile.state,
                    preferred_candidate=profile.preferred_candidate,
                    your_state=self.profile_context.profile.state)
        else:
            # If I'm a good match in a safe state, then I must be voting for
            # a major party, and my friend must be voting for a third party
            # in a swing state
            up_friend = self.profile_context.profile
            return (
                "Will vote for {up_friend_preferred} in {my_state} in "
                "exchange for your vote for {up_friend_second} in "
                "{your_state}").format(
                    up_friend_preferred=up_friend.preferred_candidate,
                    my_state=profile.state,
                    up_friend_second=up_friend.second_candidate,
                    your_state=up_friend.state)


@login_required
def profile(request):
    user = request.user
    context = RequestContext(
        request,
        {
            'profile': user.profile,
            'profile_context': ProfileContext(user.profile),
        }
    )
    return render_to_response('users/profile.html',
                              context_instance=context)
