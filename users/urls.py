from django.conf.urls import url

from users.views import confirm_swap
from users.views import profile
from users.views import propose_swap
from users.views import reject_swap
from users.views import share
from users.views import update_profile

urlpatterns = [
    url('^profile/$', profile, name='profile'),
    url('^swap/$', propose_swap, name='propose_swap'),
    url('^swap/confirm/(?P<ref_id>[^/]+)/$',
        confirm_swap, name='confirm_swap'),
    url('^swap/reject/(?P<ref_id>[^/]+)/$', reject_swap, name='reject_swap'),
    url('^profile/update/$', update_profile, name='update_profile'),
    url('^share/$', share, name='share'),
]
