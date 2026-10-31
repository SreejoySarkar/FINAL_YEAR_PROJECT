from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import Admin


class AdminLoginTests(APITestCase):

    def setUp(self):
        self.admin = Admin.objects.create_user(
            username="testadmin",
            email="testadmin@example.com",
            password="TestPassword123",
            role="election_admin"
        )

    def test_login_with_wrong_password(self):
        response = self.client.post(
            "/api/admin/login",
            {
                "username": "testadmin",
                "password": "WrongPassword123"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
