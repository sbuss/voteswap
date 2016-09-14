from factory import fuzzy

from users.tests.factories import UserFactory


RANDOM_SEED = 1024


def create_profiles(num_profiles):
    fuzzy.reseed_random(RANDOM_SEED)
    return [user.profile
            for user in (UserFactory.create() for x in range(num_profiles))]
