from django import forms

from polling.models import CANDIDATES_ADVOCATED
from polling.models import STATES
from users.models import Profile


class LandingPageForm(forms.Form):
    state = forms.ChoiceField(
        choices=STATES, label="Your state")
    preferred_candidate = forms.ChoiceField(
        choices=CANDIDATES_ADVOCATED,
        label="Who do you want to vote for")
    reason = forms.CharField(
        widget=forms.Textarea(
            {'placeholder': "Because #NeverTrump"}),
        required=False,
        label="Why do you want to swap?")

    def save(self, user):
        """Create a Profile for the given user

        Args:
            user: The django User object to associate with the profile
        Returns the created Profile object
        """
        user_profile = Profile.objects.filter(user=user)
        fb_id = user.social_auth.get().uid
        fb_profile = Profile.objects.filter(fb_id=fb_id)

        if user_profile and fb_profile:
            profile = user_profile.get()
            profile.fb_id = fb_id
            profile.fb_name = fb_profile.get().fb_name or user.get_full_name()
            fb_profile.delete()
        elif user_profile:
            profile = user_profile.get()
            profile.fb_id = fb_id
            if not profile.fb_name:
                profile.fb_name = user.get_full_name()
        elif fb_profile:
            profile = fb_profile.get()
            profile.user = user
        else:
            profile = Profile.objects.create(
                user=user, fb_id=fb_id, fb_name=user.get_full_name())

        profile.user = user
        profile.state = self.cleaned_data['state']
        profile.preferred_candidate = self.cleaned_data['preferred_candidate']
        profile.reason = self.cleaned_data.get('reason', '')
        profile.active = True
        profile.full_clean()
        # TODO: Fetch friends from facbeook
        profile.save()
        return profile
