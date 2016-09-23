from django.conf.urls import url

from users.views import profile
from users.views import propose_swap

urlpatterns = [
    url('^profile/$', profile, name='profile'),
    url('^swap/$', propose_swap, name='propose_swap'),
]
