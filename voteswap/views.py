from collections import namedtuple
import datetime
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils import timezone
import requests
import time

from polling.models import State
from users.models import Profile
from users.models import SignUpLog
from voteswap.match import get_friend_matches
# from voteswap.match import NoMatchNecessary
from voteswap.forms import LandingPageForm

import logging

logger = logging.getLogger(__name__)

SignUpInfo = namedtuple("SignUpInfo", ["timestamp", "referer", "ip"])


def _attach_signup_info(request):
    key = 'signupinfo'
    existing_info = request.session.get(key, None)
    now = timezone.datetime.now()
    if existing_info:
        # If it's less than 1 hour old, do nothing
        existing_info = SignUpInfo(*existing_info)
        last_update = datetime.datetime.fromtimestamp(existing_info.timestamp)
        if now - last_update < datetime.timedelta(hours=1):
            return

    def get_client_ip():
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    request.session[key] = SignUpInfo(
        int(time.mktime(now.timetuple())),
        request.META.get('HTTP_REFERER', ''),
        get_client_ip())


def logout(request):
    logger.info("%s logging out", request.user)
    auth_logout(request)
    return HttpResponseRedirect(reverse('index'))


def signup(request):
    _attach_signup_info(request)
    logger.info("signup form")
    form = LandingPageForm()
    context = RequestContext(request, {'form': form})
    return render_to_response('sign_up.html',
                              context_instance=context)


def landing_page(request):
    _attach_signup_info(request)
    if hasattr(request, 'user') and request.user.is_authenticated():
        logger.info("%s redirected from landing page to profile", request.user)
        return HttpResponseRedirect(reverse('users:profile'))

    if request.method == "POST":
        logger.info("posted to landing page")
        form = LandingPageForm(data=request.POST)
        if form.is_valid():
            # Save the data to session
            data = form.cleaned_data
            request.session['landing_page_form'] = data
            logger.info("Saved data to session: %s", data)
            # redirect to FB login, with '?next' set to send the user to
            # confirm_signup
            fb_login_url = "{base}?next={next}".format(
                base=reverse('social:begin', args=['facebook']),
                next=reverse(confirm_signup))
            logger.info("Redirecting landing page signup to facebook")
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
    logger.info("Fetching facebook friends for %s, next_url is %s",
                user, next_url)
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
    except Exception as e:
        logger.exception("No json response in data: %s", e)
        data = []
    friend_profiles = []
    for friend in data['data']:
        profile, created = Profile.objects.get_or_create(
            fb_id=friend['id'], fb_name=friend['name'])
        friend_profiles.append(profile)
    user.profile.friends.add(*friend_profiles)
    if 'next' in data.get('paging', {}):
        next_url = data['paging']['next']
        logger.info("Found next in facebook response: %s", next_url)
        _add_facebook_friends_for_user(user, next_url)


@login_required
def confirm_signup(request):
    logger.info("Facebook login successful, creating profile")
    # This happens after logging in, now we can get their friends
    data = request.session.get('landing_page_form', None)
    if not data:
        logger.error("No session data, redirect to signup page")
        return HttpResponseRedirect(reverse('signup'))
    logger.info("Data in confirm_signup is %s" % data)

    try:
        if request.user.profile.fb_id:
            try:
                del request.session['landing_page_form']
            except KeyError:
                pass
            logger.info(("%s's profile already exists. They clicked join "
                         "instead of login. Redirecting to their profile"),
                        request.user)
            # Skip sign up, they probably clicked "Join" on accident
            return HttpResponseRedirect(reverse('users:profile'))
    except:
        pass

    form = LandingPageForm(data=data)
    try:
        if form.is_valid():
            form.save(request.user)
            signupinfo = request.session.get('signupinfo')
            if signupinfo:
                SignUpLog.objects.create(
                    user=request.user,
                    referer=signupinfo.referer,
                    ip=signupinfo.ip)
            logger.info("Created profile for user %s", request.user)
            _add_facebook_friends_for_user(request.user)
            return HttpResponseRedirect(reverse('users:profile'))
        else:
            logger.error("LandingPageForm invalid for user %s: %s",
                         request.user, form.errors)
    except Exception as e:
        logger.exception("Signup failed: %s", e)
        return HttpResponseServerError("Signup failed: %s" % e)
    finally:
        try:
            del request.session['landing_page_form']
        except KeyError:
            pass
    logger.error("Sign up failed for unknown reasons. No extra data to report")
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
    _attach_signup_info(request)
    logger.info("about page")
    context = RequestContext(request)
    return render_to_response('about.html', context_instance=context)


def press(request):
    _attach_signup_info(request)
    logger.info("press page")
    context = RequestContext(request)
    return render_to_response('press.html', context_instance=context)
