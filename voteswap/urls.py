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
from django.views.generic import TemplateView

from voteswap.views import about
from voteswap.views import confirm_signup
from voteswap.views import landing_page
from voteswap.views import logout
from voteswap.views import press
from voteswap.views import match
from users.views import profile


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url('', include('social.apps.django_app.urls', namespace='social')),
    url('^home/$', landing_page, name='index'),
    url('^$', landing_page, name='landing_page'),
    url('^gary-johnson/$', landing_page, {'gary': True}, name='landing_page'),
    url('^ows/$', landing_page, {'ows': True}, name='landing_page'),
    url('^occupy/$', landing_page, {'occupy': True}, name='landing_page'),
    url('^logout/$', logout, name='logout'),
    url('^about/$', about, name='about'),
    url('^press/$', press, name='press'),
    url('^user/', include('users.urls', namespace='users')),
    url('^swap/', profile, name='swap'),
    url('^signup/confirm$', confirm_signup, name='confirm_signup'),
    url('^signup/$', landing_page, name='signup'),
    # TODO: Remove this and fix the tests
    url('^match/$', match, name='match'),
    url('^privacy/$',
        TemplateView.as_view(template_name='privacy-policy.html'),
        name='privacy'),
    url('^tos/$',
        TemplateView.as_view(template_name='terms-of-service.html'),
        name='tos'),
]
