from django.contrib import admin

from users.models import PairProposal
from users.models import Profile

admin.site.register(PairProposal)
admin.site.register(Profile)
