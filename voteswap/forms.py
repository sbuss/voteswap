from django import forms

from polling.models import CANDIDATES
from polling.models import CANDIDATES_THIRD_PARTY
from polling.models import STATES


class LandingPageForm(forms.Form):
    state = forms.ChoiceField(choices=STATES)
    preferred_candidate = forms.ChoiceField(choices=CANDIDATES)
    second_candidate = forms.ChoiceField(
        choices=CANDIDATES_THIRD_PARTY,
        required=False)
    reason = forms.Textarea()
