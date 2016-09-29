from django.contrib import admin

from users.models import PairProposal
from users.models import Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'fb_name', 'state', 'preferred_candidate', 'is_paired')


class PairProposalAdmin(admin.ModelAdmin):
    list_display = (
        '_from_profile', '_to_profile',
        'date_proposed', 'date_confirmed', 'date_rejected')

    def _from_profile(self, obj):
        try:
            return obj.from_profile.fb_name
        except:
            return 'err'

    def _to_profile(self, obj):
        try:
            return obj.to_profile.fb_name
        except:
            return 'err'


admin.site.register(PairProposal, PairProposalAdmin)
admin.site.register(Profile, ProfileAdmin)
