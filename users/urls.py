from django.conf.urls import url

from users.views import profile
from users.views import propose_swap
from users.views import update_profile

urlpatterns = [
    url('^profile/$', profile, name='profile'),
    url('^swap/$', propose_swap, name='propose_swap'),
    url('^profile/update/$', update_profile, name='update_profile'),
]
