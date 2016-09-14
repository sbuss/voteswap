from factory import fuzzy

from users.tests.factories import UserFactory


RANDOM_SEED = 1024


def create_profiles(num_profiles):
    # This seed does nothing because I'm using fake-factory instead of
    # factory.fuzzy. TODO fix it
    fuzzy.reseed_random(RANDOM_SEED)
    return [user.profile
            for user in (UserFactory.create() for x in range(num_profiles))]
