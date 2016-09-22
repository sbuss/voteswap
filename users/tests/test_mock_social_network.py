from users.mocks import MockSocialNetwork
from users.tests import BaseUsersTest


class TestProfile(BaseUsersTest):
    def setUp(self):
        super(TestProfile, self).setUp()
        self.social_network = MockSocialNetwork()

    def test_friends(self):
        friends = self.social_network.get_friends(self.users[0].id)
        self.assertEqual(len(friends), 9)

    def test_friends_of_friends(self):
        friends = self.social_network.get_friends_of_friends(self.users[0].id)
        self.assertEqual(len(friends), 12)

    def test_foaf_exclude(self):
        friends = self.social_network.get_friends_of_friends(
            self.users[0].id, exclude_friends=True)
        self.assertEqual(len(friends), 3)
