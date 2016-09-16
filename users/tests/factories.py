import random

from django.contrib.auth import get_user_model
import factory

from polling.models import CANDIDATES
from polling.models import STATES
from users.models import Profile


class ProfileFactory(factory.DjangoModelFactory):
    class Meta:
        model = Profile
    state = factory.LazyAttribute(lambda o: random.choice(STATES)[0])

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


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = get_user_model()
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    username = factory.LazyAttributeSequence(
        lambda o, n: ("%s.%s.%s" % (o.first_name, o.last_name, n)).lower())
    email = factory.LazyAttribute(lambda o: "%s@gmail.com" % o.username)
    profile = factory.RelatedFactory(ProfileFactory, 'user')
