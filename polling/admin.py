from django.contrib import admin

from polling.models import State


class StateAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'updated', 'tipping_point_rank', 'safe_rank', 'safe_for',
        'lean_rank', 'leans')


admin.site.register(State, StateAdmin)
