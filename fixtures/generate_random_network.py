from django.contrib.auth import get_user_model
from factory import fuzzy

from users.tests.factories import UserFactory
from users.mocks import MockSocialNetwork


RANDOM_SEED = 1024


def create_profiles(num_profiles):
    # This seed does nothing because I'm using fake-factory instead of
    # factory.fuzzy. TODO fix it
    fuzzy.reseed_random(RANDOM_SEED)
    return [user.profile
            for user in (UserFactory.create() for x in range(num_profiles))]


def assign_friends():
    m = MockSocialNetwork()
    users = get_user_model().objects.select_related('profile').order_by('id')
    for user in users:
        if not getattr(user, 'profile', False):
            print(user)
            continue
        friends = m.get_friends(user.id)
        user.profile.friends.add(*[friend.id for friend in friends])
