from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.functional import cached_property
import json

from users.forms import PairProposalForm
from voteswap.match import get_friend_matches
from voteswap.forms import LandingPageForm


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
        return profile.fb_name

    @property
    def has_been_proposed_to(self):
        return self.profile_context.has_proposed_to_friend(
            self.friend_match.profile)

    @property
    def proposal_string(self):
        profile = self.friend_match.profile
        return (
            "Will vote for {your_candidate} in {my_state} in exchange for "
            "your vote for {my_candidate} in {your_state}").format(
                your_candidate=(
                    self.profile_context.profile.preferred_candidate),
                my_state=profile.state,
                my_candidate=profile.preferred_candidate,
                your_state=self.profile_context.profile.state)


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


def json_response(data):
    if isinstance(data, dict):
        data = json.dumps(data)
    return HttpResponse(data, content_type='application/json')


@login_required
def propose_swap(request):
    if request.method == "POST":
        form = PairProposalForm(
            from_profile=request.user.profile, data=request.POST)
        if form.is_valid():
            form.save()
            return json_response({'status': 'ok', 'errors': {}})
        else:
            return json_response({'status': 'error', 'errors': form.errors})
    else:
        return json_response(
            {'status': 'error',
             'errors': {'method': 'Must POST with to_profile set'}})


@login_required
def update_profile(request):
    if request.method == "POST":
        form = LandingPageForm(data=request.POST)
        if form.is_valid():
            form.save(request.user)
            return HttpResponseRedirect(reverse('users:profile'))
    else:
        initial = {
            'state': request.user.profile.state,
            'preferred_candidate': request.user.profile.preferred_candidate,
            'reason': request.user.profile.reason
        }
        form = LandingPageForm(initial=initial)
    context = RequestContext(request, {'form': form})
    return render_to_response(
        'users/update_profile.html', context_instance=context)
