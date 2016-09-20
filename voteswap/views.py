from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.shortcuts import render_to_response
from django.template.context import RequestContext
import requests

from users.models import Profile
from voteswap.match import get_friend_matches
# from voteswap.match import NoMatchNecessary
from voteswap.forms import LandingPageForm

import logging

logger = logging.getLogger(__name__)


def index(request):
    context = RequestContext(
        request, {'request': request, 'user': request.user})
    return render_to_response('index.html',
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
    context = RequestContext(request, {'form': form})
    return render_to_response('landing_page.html',
                              context_instance=context)


def _get_friends_for_user(user):
    """Get the user's facebook friends and get or create their Profiles."""
    social_user = user.social_auth.get()
    url = ('https://graph.facebook.com/{uid}/'
           'friends?fields=id,name,email',
           '&access_token={token}'.format(
               uid=social_user.uid,
               token=social_user.extra_data['access_token'],
           ))
    response = requests.get(url)
    try:
        data = response.json()["data"]
    except Exception:
        data = []
    friend_profiles = []
    for friend in data:
        profile, created = Profile.objects.get_or_create(
            fb_id=friend['id'], fb_name=friend['name'])
        friend_profiles.append(profile)
    user.profile.friends.add(*friend_profiles)


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
            _get_friends_for_user(request.user)
            return HttpResponseRedirect(reverse('users:profile'))
    except Exception as e:
        return HttpResponseServerError("Signup failed: %s" % e)
    return HttpResponseServerError("Unknown server error")


@login_required
def match(request):
    matches = get_friend_matches(request.user)
    context = RequestContext(
        request,
        {'request': request, 'user': request.user, 'matches': matches})
    return render_to_response('match.html',
                              context_instance=context)
