import random

from django.contrib.auth import get_user_model
import factory
from social.apps.django_app.default.models import UserSocialAuth

from polling.models import CANDIDATES
from polling.models import STATES
from users.models import Profile


class ProfileFactory(factory.DjangoModelFactory):
    class Meta:
        model = Profile
    state = factory.Sequence(lambda n: STATES[n % 51][0])

    @factory.lazy_attribute
    def preferred_candidate(self):
        return random.choice(CANDIDATES)[0]

    @factory.lazy_attribute
    def second_candidate(self):
        return random.choice(CANDIDATES)[0]

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        while kwargs['preferred_candidate'] == kwargs['second_candidate']:
            kwargs['second_candidate'] = random.choice(CANDIDATES)[0]
        return kwargs


class SocialAuthFactory(factory.DjangoModelFactory):
    class Meta:
        model = UserSocialAuth
    provider = 'Facebook'
    uid = factory.Sequence(lambda n: str(n))


def _lazy_uid(profile):
    if profile.user:
        try:
            return profile.user.social_auth.get().uid
        except:
            pass
    return ''


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = get_user_model()
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    username = factory.LazyAttributeSequence(
        lambda o, n: ("%s.%s.%s" % (o.first_name, o.last_name, n)).lower())
    email = factory.LazyAttribute(lambda o: "%s@gmail.com" % o.username)
    profile = factory.RelatedFactory(
        ProfileFactory, 'user',
        fb_id=factory.LazyAttribute(_lazy_uid),
        active=True)
    social_auth = factory.RelatedFactory(SocialAuthFactory, 'user')
