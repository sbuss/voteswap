from django import forms

from polling.models import CANDIDATES
from polling.models import CANDIDATES_THIRD_PARTY
from polling.models import STATES
from users.models import Profile


class LandingPageForm(forms.Form):
    state = forms.ChoiceField(choices=STATES)
    preferred_candidate = forms.ChoiceField(choices=CANDIDATES)
    second_candidate = forms.ChoiceField(
        choices=CANDIDATES_THIRD_PARTY,
        required=False)
    reason = forms.Textarea()

    def save(self, user):
        """Create a Profile for the given user

        Args:
            user: The django User object to associate with the profile
        Returns the created Profile object
        """
        profile = Profile.objects.create(
            user=user,
            state=self.cleaned_data['state'],
            preferred_candidate=self.cleaned_data['preferred_candidate'],
            second_candidate=self.cleaned_data.get('second_candidate', ''),
            reason=self.cleaned_data.get('reason', ''))
        return profile
