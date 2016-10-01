from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
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
import json
import re

from polling.models import CANDIDATE_CLINTON
from polling.models import CANDIDATE_JOHNSON
from polling.models import CANDIDATE_STEIN
from polling.models import State
from users.forms import ConfirmPairProposalForm
from users.forms import PairProposalForm
from users.forms import RejectPairProposalForm
from users.forms import UpdateProfileForm
from users.models import PairProposal
from users.models import Profile
from voteswap.match import get_friend_matches

CANDIDATES_THIRD = [CANDIDATE_JOHNSON, CANDIDATE_STEIN]


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
            return "%s or %s" % CANDIDATES_THIRD
        else:
            return CANDIDATE_CLINTON

    @property
    def third_party(self):
        return self.profile.preferred_candidate in CANDIDATES_THIRD

    @property
    def needs_match(self):
        if self.state.is_swing or self.state.leans:
            return self.profile.preferred_candidate in CANDIDATES_THIRD
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
                self.profile.preferred_candidate in CANDIDATES_THIRD)

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
    try:
        profile_ctx = ProfileContext(user.profile)
    except Profile.DoesNotExist:
        return HttpResponseRedirect(reverse('users:update_profile'))
    if profile_ctx.profile_needs_updating:
        return HttpResponseRedirect(reverse('users:update_profile'))

    context = RequestContext(
        request,
        {
            'user': request.user,
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
    message = EmailMultiAlternatives(
        from_email=u'noreply@voteswap.us',
        to=[match.to_profile.user.email],
        subject=u"New VoteSwap with {user}".format(
            user=user.profile.fb_name))
    from_profile_context = ProfileContext(match.from_profile)
    to_profile_context = ProfileContext(match.to_profile)
    message.body = _format_email(
        render_to_string(
            'users/emails/propose_swap_email.txt',
            {'from_profile_ctx': from_profile_context,
             'to_profile_ctx': to_profile_context}))
    message.attach_alternative(
        _format_email(
            render_to_string(
                'users/emails/propose_swap_email.html',
                {'from_profile_ctx': from_profile_context,
                 'to_profile_ctx': to_profile_context})),
        'text/html')
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
    needs_update = False
    initial = {}
    if request.method == "POST":
        form = UpdateProfileForm(data=request.POST)
        if form.is_valid():
            form.save(request.user)
            return HttpResponseRedirect(reverse('users:profile'))
    else:
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            needs_update = True
        else:
            needs_update = ProfileContext(profile).profile_needs_updating
            initial = {
                'state': profile.state,
                'preferred_candidate': profile.preferred_candidate,
                'reason': profile.reason,
                'email': request.user.email,
            }
        form = UpdateProfileForm(initial=initial)
    context = RequestContext(
        request, {'form': form, 'needs_update': needs_update})
    return render_to_response(
        'users/update_profile.html', context_instance=context)


def _send_reject_swap_email(user, match):
    message = EmailMultiAlternatives(
        from_email=u'noreply@voteswap.us',
        to=[match.from_profile.user.email],
        subject=u"{user} rejected your VoteSwap".format(
            user=user.profile.fb_name))
    from_profile_context = ProfileContext(match.from_profile)
    to_profile_context = ProfileContext(match.to_profile)
    message.body = _format_email(
        render_to_string(
            'users/emails/reject_swap_email.txt',
            {'from_profile_ctx': from_profile_context,
             'to_profile_ctx': to_profile_context}))
    message.attach_alternative(
        _format_email(
            render_to_string(
                'users/emails/reject_swap_email.html',
                {'from_profile_ctx': from_profile_context,
                 'to_profile_ctx': to_profile_context})),
        'text/html')
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


def _send_confirm_swap_email(user, match):
    for from_profile, to_profile in [
            (match.from_profile, match.to_profile),
            (match.to_profile, match.from_profile)]:
        message = EmailMultiAlternatives(
            subject=u"Your VoteSwap with {user} is confirmed!".format(
                user=from_profile.fb_name),
            from_email='noreply@email.voteswap.us',
            to=[to_profile.user.email],
            reply_to=[from_profile.user.email])
        profile_context = ProfileContext(from_profile)
        paired_profile_context = ProfileContext(to_profile)
        message.body = _format_email(
            render_to_string(
                'users/emails/confirm_swap_email.txt',
                {'profile_ctx': profile_context,
                 'paired_profile_ctx': paired_profile_context}))
        message.attach_alternative(
            _format_email(
                render_to_string(
                    'users/emails/confirm_swap_email.html',
                    {'profile_ctx': profile_context,
                     'paired_profile_ctx': paired_profile_context})),
            'text/html')
        message.send()


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
            _send_confirm_swap_email(request.user, form.instance)
            return HttpResponseRedirect(reverse('users:profile'))
        else:
            return json_response({'status': 'error', 'errors': form.errors})
    else:
        return json_response(
            {'status': 'error',
             'errors': {'method': 'Must POST with to_profile set'}})
    PairProposal.objects


@login_required
def test_email(request):
    profile = request.user.profile
    proposal, created = PairProposal.objects.get_or_create(
        from_profile=profile,
        to_profile=profile)
    _send_swap_proposal_email(request.user, proposal)
    _send_reject_swap_email(request.user, proposal)
    _send_confirm_swap_email(request.user, proposal)
