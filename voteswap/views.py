from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.shortcuts import render_to_response
from django.template.context import RequestContext
import requests

from polling.models import State
from users.models import Profile
from voteswap.match import get_friend_matches
# from voteswap.match import NoMatchNecessary
from voteswap.forms import LandingPageForm

import logging

logger = logging.getLogger(__name__)


def logout(request):
    auth_logout(request)
    return HttpResponseRedirect(reverse('index'))


def login(request):
    form = LandingPageForm()
    context = RequestContext(request, {'form': form})
    return render_to_response('sign_up.html',
                              context_instance=context)


def landing_page(request):
    if hasattr(request, 'user') and request.user.is_authenticated():
        return HttpResponseRedirect(reverse('users:profile'))

    if request.method == "POST":
        form = LandingPageForm(data=request.POST)
        if form.is_valid():
            # Save the data to session
            data = form.cleaned_data
            request.session['landing_page_form'] = data
            # redirect to FB login, with '?next' set to send the user to
            # confirm_signup
            fb_login_url = "{base}?next={next}".format(
                base=reverse('social:begin', args=['facebook']),
                next=reverse(confirm_signup))
            return HttpResponseRedirect(fb_login_url)
    else:
        form = LandingPageForm()
    swing_states = list(State.objects.exclude(tipping_point_rank=-1).order_by(
        'tipping_point_rank').values_list('name', flat=True))[:6]
    swing_states[-1] = "or %s" % swing_states[-1]
    swing_states = ', '.join(swing_states)
    context = RequestContext(
        request, {'form': form, 'swing_states': swing_states})
    return render_to_response('landing_page.html',
                              context_instance=context)


def _add_facebook_friends_for_user(user, next_url=""):
    """Get the user's facebook friends and get or create their Profiles.

    Args:
        user: The User object
        next_url: Given when iterating through pages of a response. If not set
            then the first page will be fetched.
    """
    social_user = user.social_auth.get()
    if not next_url:
        url = ('https://graph.facebook.com/{uid}/'
               'friends?fields=id,name,email'
               '&access_token={token}').format(
                   uid=social_user.uid,
                   token=social_user.extra_data['access_token'])
    else:
        url = next_url
    response = requests.get(url)
    try:
        data = response.json()
    except Exception:
        data = []
    friend_profiles = []
    for friend in data['data']:
        profile, created = Profile.objects.get_or_create(
            fb_id=friend['id'], fb_name=friend['name'])
        friend_profiles.append(profile)
    user.profile.friends.add(*friend_profiles)
    if 'next' in data.get('paging', {}):
        _add_facebook_friends_for_user(user, data['paging']['next'])


@login_required
def confirm_signup(request):
    # This happens after logging in, now we can get their friends
    data = request.session.get('landing_page_form', None)
    if not data:
        return HttpResponseRedirect(reverse('signup'))
    logger.info("Data in confirm_signup is %s" % data)

    form = LandingPageForm(data=data)
    try:
        if form.is_valid():
            form.save(request.user)
            _add_facebook_friends_for_user(request.user)
            return HttpResponseRedirect(reverse('users:profile'))
    except Exception as e:
        return HttpResponseServerError("Signup failed: %s" % e)
    return HttpResponseServerError("Unknown server error")


@login_required
def match(request):
    matches = get_friend_matches(request.user.profile)
    context = RequestContext(
        request,
        {'request': request, 'user': request.user, 'matches': matches})
    return render_to_response('match.html',
                              context_instance=context)


def about(request):
    context = RequestContext(request)
    return render_to_response('about.html', context_instance=context)


def press(request):
    context = RequestContext(request)
    return render_to_response('press.html', context_instance=context)
