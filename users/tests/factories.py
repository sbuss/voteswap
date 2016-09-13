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
        choice = random.choice(CANDIDATES)[0]
        while choice == self.preferred_candidate:
            choice = random.choice(CANDIDATES)[0]
        return choice


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = get_user_model()
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    username = factory.LazyAttribute(
        lambda o: ("%s.%s" % (o.first_name, o.last_name)).lower())
    email = factory.LazyAttribute(lambda o: "%s@gmail.com" % o.username)
    profile = factory.RelatedFactory(ProfileFactory, 'user')
