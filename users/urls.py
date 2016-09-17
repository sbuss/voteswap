from django.conf.urls import url

from users.views import profile

urlpatterns = [
    url('^profile/$', profile, name='profile'),
]
