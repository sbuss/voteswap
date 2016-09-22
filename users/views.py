from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.functional import cached_property

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
        return get_friend_matches(self.profile)


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
