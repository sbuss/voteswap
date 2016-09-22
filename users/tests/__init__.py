from django.test import TestCase

from users.tests.factories import UserFactory


class BaseUsersTest(TestCase):
    def setUp(self):
        super(BaseUsersTest, self).setUp()
        self.users = [UserFactory.create() for x in range(100)]
