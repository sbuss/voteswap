from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.shortcuts import render_to_response
from django.template.context import RequestContext

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

def splash_page(request):
    return render_to_response('splash.html')



@login_required
def confirm_signup(request):
    data = request.session.get('landing_page_form', None)
    if not data:
        return HttpResponseRedirect(reverse('signup'))
    logger.info("Data in confirm_signup is %s" % data)

    form = LandingPageForm(data=data)
    try:
        if form.is_valid():
            form.save(request.user)
            return HttpResponseRedirect(reverse('users:profile'))
    except Exception as e:
        return HttpResponseServerError("Signup failed: %s" % e)
    return HttpResponseServerError("Unknown server error")
