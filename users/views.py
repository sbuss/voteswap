from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext


@login_required
def profile(request):
    user = request.user
    context = RequestContext(request, {'profile': user.profile})
    return render_to_response('users/profile.html',
                              context_instance=context)
