from django import forms
from django.http.request import QueryDict
from django.utils import timezone
from users.models import PairProposal
from users.models import Profile
from voteswap.forms import LandingPageForm


class PairProposalForm(forms.ModelForm):
    _error_messages = {
        'same_profile': "You cannot pair with yourself"
    }

    class Meta:
        model = PairProposal
        fields = ['from_profile', 'to_profile']

    def __init__(self, from_profile, *args, **kwargs):
        data = kwargs.get('data', QueryDict()).copy()
        data['from_profile'] = from_profile.id
        kwargs['data'] = data
        super(PairProposalForm, self).__init__(*args, **kwargs)
        self.fields['from_profile'].queryset = Profile.objects.filter(
            id=from_profile.id)
        self.fields['to_profile'].queryset = from_profile.all_unpaired_friends


class ConfirmPairProposalForm(forms.ModelForm):
    class Meta:
        model = PairProposal
        fields = ['from_profile', 'to_profile']

    def __init__(self, *args, **kwargs):
        super(ConfirmPairProposalForm, self).__init__(*args, **kwargs)
        from_profile = self.instance.from_profile
        self.fields['from_profile'].queryset = Profile.objects.filter(
            id=from_profile.id)
        self.fields['to_profile'].queryset = from_profile.all_unpaired_friends

    def save(self):
        self.instance.from_profile.paired_with = self.instance.to_profile
        self.instance.date_confirmed = timezone.now()
        super(ConfirmPairProposalForm, self).save()


class RejectPairProposalForm(forms.ModelForm):
    class Meta:
        model = PairProposal
        fields = ['from_profile', 'to_profile', 'reason_rejected']

    def __init__(self, *args, **kwargs):
        super(RejectPairProposalForm, self).__init__(*args, **kwargs)
        from_profile = self.instance.from_profile
        self.fields['from_profile'].queryset = Profile.objects.filter(
            id=from_profile.id)
        self.fields['to_profile'].queryset = from_profile.all_unpaired_friends

    def save(self):
        self.instance.date_rejected = timezone.now()
        super(RejectPairProposalForm, self).save()


class UpdateProfileForm(LandingPageForm):
    email = forms.EmailField(
        required=True, label="Email",
        help_text=("We need your email to notify you when you are paired to "
                   "swap your vote"))

    def save(self, user):
        super(UpdateProfileForm, self).save(user)
        user.email = self.cleaned_data['email']
        user.save()
        return user.profile
