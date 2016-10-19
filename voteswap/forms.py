from django import forms
import logging

from polling.models import CANDIDATES_ADVOCATED
from polling.models import STATES
from users.models import Profile

logger = logging.getLogger(__name__)


class LandingPageForm(forms.Form):
    state = forms.ChoiceField(
        choices=STATES, label="Your state")
    preferred_candidate = forms.ChoiceField(
        choices=CANDIDATES_ADVOCATED,
        label="Who do you want to vote for?")
    reason = forms.CharField(
        widget=forms.Textarea(
            {'placeholder': "Because #NeverTrump"}),
        required=False,
        label="Why do you want to swap?")
    allow_random = forms.BooleanField(
        required=False,
        initial=True,
        label="OK to match me with people I don't know")

    def save(self, user):
        """Create a Profile for the given user

        Args:
            user: The django User object to associate with the profile
        Returns the created Profile object
        """
        logger.info("Saving LandingPageForm")
        user_profile = Profile.objects.filter(user=user)
        fb_id = user.social_auth.get().uid
        fb_profile = Profile.objects.filter(fb_id=fb_id)

        if user_profile and fb_profile:
            logger.info(
                "%s has a profile and a fb_profile. Are they the same?", user)
            if user_profile.get().id != fb_profile.get().id:
                logger.info("%s's two profile aren't the same. Merging", user)
                profile = user_profile.get()
                profile.fb_id = fb_id
                profile.fb_name = (
                    fb_profile.get().fb_name or user.get_full_name())
                fb_profile.delete()
            else:
                logger.info("%s's two profiles are the same", user)
                profile = user_profile.get()
        elif user_profile:
            logger.info("User has an existing profile (%s), update it.",
                        user_profile)
            profile = user_profile.get()
            profile.fb_id = fb_id
            if not profile.fb_name:
                profile.fb_name = user.get_full_name()
        elif fb_profile:
            logger.info(
                "A profile with that facebook ID (%s) exists. Claim it",
                fb_id)
            profile = fb_profile.get()
            profile.user = user
        else:
            logger.info("No existing profile for user %s", user)
            profile = Profile.objects.create(
                user=user, fb_id=fb_id, fb_name=user.get_full_name())

        profile.user = user
        profile.state = self.cleaned_data['state']
        profile.preferred_candidate = self.cleaned_data['preferred_candidate']
        profile.reason = self.cleaned_data.get('reason', '')
        profile.allow_random = self.cleaned_data['allow_random']
        profile.active = True
        logger.info("Set profile fields. Cleaning")
        profile.full_clean()
        # TODO: Fetch friends from facbeook
        profile.save()
        logger.info("Saved profile %s", profile)
        return profile
