from bisect import bisect_left

from django.contrib.auth import get_user_model
from networkx.generators.community import relaxed_caveman_graph

from users.models import Profile


RANDOM_SEED = 1024


def index(arr, element):
    """Efficient index lookup in a sorted array

    from https://docs.python.org/2/library/bisect.html"""
    i = bisect_left(arr, element)
    if i != len(arr) and arr[i] == element:
        return i
    raise ValueError


class MockSocialNetwork(object):
    """The MockSocialNetwork is for use in running the site locally.

    It is a randomly generated social network."""
    def __init__(self):
        self.user_ids = (get_user_model().objects.all().order_by('id')
                         .values_list('id', flat=True))
        self.num_users = len(self.user_ids)
        self.social_network = relaxed_caveman_graph(
            self.num_users,  # size of group
            10,  # num of cliques
            0.05,  # probability of rewiring intra-group to inter-group edge
            RANDOM_SEED)

    def _user_id_to_index(self, user_id):
        """Get the node in the social network for the given user."""
        return index(self.user_ids, user_id)

    def _index_to_user_id(self, index):
        return self.user_ids[index]

    def get_friends(self, user_id):
        """Get the Profiles of friends of the given user."""
        friends = [self._index_to_user_id(neighbor)
                   for neighbor in self.social_network.neighbors(
                       self._user_id_to_index(user_id))]
        return Profile.objects.filter(id__in=friends).select_related('user')

    def get_friends_of_friends(self, user_id, exclude_friends=False):
        exclude = set()
        all_friends = set()
        for neighbor in self.social_network.neighbors(
                self._user_id_to_index(user_id)):
            if exclude_friends:
                exclude.add(neighbor)
            all_friends.add(self._index_to_user_id(neighbor))
            for foaf in self.social_network.neighbors(neighbor):
                all_friends.add(self._index_to_user_id(foaf))
        friends = all_friends - exclude
        return Profile.objects.filter(id__in=friends).select_related('user')
