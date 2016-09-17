from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext

from voteswap.forms import LandingPageForm


def index(request):
    context = RequestContext(
        request, {'request': request, 'user': request.user})
    return render_to_response('index.html',
                              context_instance=context)


def landing_page(request):
    if hasattr(request, 'user') and request.user.is_authenticated():
        return HttpResponseRedirect(reverse('users:profile'))
    form = LandingPageForm()
    context = RequestContext(request, {'form': form})
    return render_to_response('landing_page.html',
                              context_instance=context)


def signup(request):
    if request.method == "POST":
        pass
    else:
        pass
