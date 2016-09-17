from django import forms

from polling.models import CANDIDATES
from polling.models import CANDIDATES_MAIN
from polling.models import STATES
from polling.models import State
from users.models import Profile


class LandingPageForm(forms.Form):
    state = forms.ChoiceField(choices=STATES)
    preferred_candidate = forms.ChoiceField(choices=CANDIDATES)
    second_candidate = forms.ChoiceField(
        choices=CANDIDATES_MAIN,
        required=False)
    reason = forms.Textarea()

    def clean(self):
        """Validate that second_candidate is supplied if swing state."""
        cleaned_data = super(LandingPageForm, self).clean()
        state = cleaned_data.get('state')
        preferred_candidate = cleaned_data.get('preferred_candidate')
        second_candidate = cleaned_data.get('second_candidate')
        if state and State.objects.get(name=state).tipping_point_rank > -1:
            # Convert CANDIDATES_MAIN to a dict because it's a list of tuples
            if preferred_candidate not in dict(CANDIDATES_MAIN):
                if second_candidate == "":
                    raise forms.ValidationError(
                        "You're in a swing state and selected a third party "
                        "candidate. You must also select a second choice.")

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
