from django.contrib.auth import get_user_model
from django.test import TestCase

from users.tests.factories import UserFactory


class BaseUsersTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(BaseUsersTest, cls).setUpClass()
        cls.users = [UserFactory.create() for x in range(100)]

    @classmethod
    def tearDownClass(cls):
        get_user_model().objects.all().delete()
