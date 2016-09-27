from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.text import wrap as wrap_text
from google.appengine.api.mail import EmailMessage
import json
import re

from polling.models import CANDIDATE_CLINTON
from polling.models import CANDIDATE_JOHNSON
from polling.models import State
from users.forms import ConfirmPairProposalForm
from users.forms import PairProposalForm
from users.forms import RejectPairProposalForm
from users.models import PairProposal
from voteswap.match import get_friend_matches
from voteswap.forms import LandingPageForm


class ProfileContext(object):
    def __init__(self, profile):
        self.profile = profile
        try:
            self.state = State.objects.get(name=self.profile.state)
        except State.DoesNotExist:
            self.state = None
        self.pair_proposal_friend_ids = set(
            self.profile.proposals_made.values_list(
                'to_profile__id', flat=True))

    @property
    def profile_needs_updating(self):
        return not (self.profile.preferred_candidate and self.profile.state)

    @property
    def paired_candidate(self):
        if self.profile.preferred_candidate == CANDIDATE_CLINTON:
            return CANDIDATE_JOHNSON
        else:
            return CANDIDATE_CLINTON

    @property
    def johnson(self):
        return self.profile.preferred_candidate == CANDIDATE_JOHNSON

    @property
    def needs_match(self):
        if self.state.is_swing or self.state.leans:
            return self.profile.preferred_candidate == CANDIDATE_JOHNSON
        elif not self.state.is_swing:
            return self.profile.preferred_candidate == CANDIDATE_CLINTON
        return True

    @property
    def state_type(self):
        if self.state.is_swing:
            return "swing state"
        elif self.state.leans:
            return "%s-leaning state" % self.state.leans
        return "safe state for %s" % self.state.safe_for

    @property
    def paired_state_type(self):
        if self.state.is_swing:
            return "safe"
        return "swing"

    @property
    def kingmaker(self):
        return ((self.state.is_swing or self.state.leans) and
                self.profile.preferred_candidate == CANDIDATE_JOHNSON)

    def has_proposed_to_friend(self, friend):
        return friend.id in self.pair_proposal_friend_ids

    @cached_property
    def pending_matches(self):
        pending_matches = PairProposal.objects.pending().filter(
            Q(from_profile=self.profile) | Q(to_profile=self.profile))
        return [PendingMatchContext(pending_match, self)
                for pending_match in pending_matches]

    @cached_property
    def good_potential_matches(self):
        return [FriendMatchContext(fm, self)
                for fm in get_friend_matches(self.profile)]


class PendingMatchContext(object):
    def __init__(self, match, profile_context):
        self.profile_context = profile_context
        self.match = match

    @cached_property
    def form(self):
        if self.from_me:
            return None
        return ConfirmPairProposalForm(instance=self.match)

    @property
    def from_me(self):
        return self.match.from_profile == self.profile_context.profile

    @property
    def matched_profile(self):
        if self.from_me:
            return self.match.to_profile
        return self.match.from_profile


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
    profile_ctx = ProfileContext(user.profile)
    if profile_ctx.profile_needs_updating:
        return HttpResponseRedirect(reverse('users:update_profile'))

    context = RequestContext(
        request,
        {
            'profile': user.profile,
            'profile_context': profile_ctx,
        }
    )
    return render_to_response('users/profile.html',
                              context_instance=context)


def json_response(data):
    if isinstance(data, dict):
        data = json.dumps(data)
    return HttpResponse(data, content_type='application/json')


def _format_email(text):
    return re.sub("\n\n+", "\n\n", wrap_text(text, 80))


def _send_swap_proposal_email(user, match):
    message = EmailMessage(
        sender='noreply@voteswap.us',
        to=match.to_profile.user.email,
        subject="New VoteSwap with {user}".format(
            user=user.profile.fb_name))
    from_profile_context = ProfileContext(match.from_profile)
    to_profile_context = ProfileContext(match.to_profile)
    message.body = _format_email(
        render_to_string(
            'users/emails/propose_swap_email.txt',
            {'from_profile_ctx': from_profile_context,
             'to_profile_ctx': to_profile_context}))
    message.html = _format_email(
        render_to_string(
            'users/emails/propose_swap_email.html',
            {'from_profile_ctx': from_profile_context,
             'to_profile_ctx': to_profile_context}))
    message.send()


@login_required
def propose_swap(request):
    if request.method == "POST":
        form = PairProposalForm(
            from_profile=request.user.profile, data=request.POST)
        if form.is_valid():
            form.save()
            _send_swap_proposal_email(request.user, form.instance)
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
    profile_ctx = ProfileContext(request.user.profile)
    context = RequestContext(
        request,
        {
            'form': form,
            'profile': request.user.profile,
            'profile_context': profile_ctx,
        }
    )
    return render_to_response(
        'users/update_profile.html', context_instance=context)


def _send_reject_swap_email(user, match):
    message = EmailMessage(
        sender='noreply@voteswap.us',
        to=match.from_profile.user.email,
        subject="{user} rejected your vote swap".format(
            user=user.profile.fb_name))
    from_profile_context = ProfileContext(match.from_profile)
    to_profile_context = ProfileContext(match.to_profile)
    message.body = _format_email(
        render_to_string(
            'users/emails/reject_swap_email.txt',
            {'from_profile_ctx': from_profile_context,
             'to_profile_ctx': to_profile_context}))
    message.html = _format_email(
        render_to_string(
            'users/emails/reject_swap_email.html',
            {'from_profile_ctx': from_profile_context,
             'to_profile_ctx': to_profile_context}))
    logger.debug(message.body)
    logger.debug(message.html)
    message.send()


@login_required
@transaction.atomic
def reject_swap(request, ref_id):
    if request.method == "POST":
        try:
            proposal = (
                request.user.profile.proposals_received
                .select_for_update()
                .get(ref_id=ref_id))
        except PairProposal.DoesNotExist:
            return json_response(
                {'status': 'error',
                 'errors': {'proposal': 'Invalid swap proposal ID'}})
        data = {'from_profile': proposal.from_profile.id,
                'to_profile': proposal.to_profile.id,
                'reason_rejected': request.POST.get('reason_rejected', '')}
        form = RejectPairProposalForm(data=data, instance=proposal)
        if form.is_valid():
            form.save()
            _send_reject_swap_email(request.user, form.instance)
            return HttpResponseRedirect(reverse('users:profile'))
        else:
            return json_response({'status': 'error', 'errors': form.errors})
    else:
        return json_response(
            {'status': 'error',
             'errors': {'method': 'Must POST with to_profile set'}})


@login_required
@transaction.atomic
def confirm_swap(request, ref_id):
    if request.method == "POST":
        try:
            proposal = (
                request.user.profile.proposals_received
                .select_for_update()
                .get(ref_id=ref_id))
        except PairProposal.DoesNotExist:
            return json_response(
                {'status': 'error',
                 'errors': {'proposal': 'Invalid swap proposal ID'}})
        # I don't want someone posting new values, this is just to confirm
        # an existing PairRequest, so build the data dict manually
        data = {'from_profile': proposal.from_profile.id,
                'to_profile': proposal.to_profile.id}
        form = ConfirmPairProposalForm(data=data, instance=proposal)
        if form.is_valid():
            form.save()
            return json_response({'status': 'ok', 'errors': {}})
        else:
            return json_response({'status': 'error', 'errors': form.errors})
    else:
        return json_response(
            {'status': 'error',
             'errors': {'method': 'Must POST with to_profile set'}})
    PairProposal.objects
