"""voteswap URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.views import logout

from voteswap.views import confirm_signup
from voteswap.views import index
from voteswap.views import landing_page
from voteswap.views import splash_page


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url('', include('social.apps.django_app.urls', namespace='social')),
    url('^home/$', index, name='index'),
    url('^$', landing_page, name='landing_page'),
    url('^logout/$', logout, name='logout'),
    url('^user/', include('users.urls', namespace='users')),
    url('^signup/confirm$', confirm_signup, name='confirm_signup'),
    url('^signup/$', landing_page, name='signup'),
    url('^splash/$', splash_page, name='splash'),
]
