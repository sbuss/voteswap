from django.test import TestCase

from users.tests.factories import UserFactory


class BaseUsersTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(BaseUsersTest, cls).setUpClass()
        cls.users = [UserFactory.create() for x in range(100)]
