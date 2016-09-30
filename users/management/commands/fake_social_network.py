from django.core.management.base import BaseCommand
from users.models import Profile
from fixtures import generate_random_network


class Command(BaseCommand):
    help = 'Generate a fake social network'

    def handle(self, *args, **options):
        if Profile.objects.count():
            raise RuntimeError(
                "You probably don't want to run this if there are already "
                "users in the system.")
        generate_random_network.create_profiles(100)
        generate_random_network.assign_friends()
