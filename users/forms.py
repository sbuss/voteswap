from django import forms
from django.http.request import QueryDict
from users.models import PairProposal
from users.models import Profile


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
