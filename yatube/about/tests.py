from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class AboutURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='NoName')
        cls.templates_url_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }

    def setUp(self):
        self.guest_client = Client()

    def test_urls_without_errors(self):
        """The urls opens correctly."""
        for url in list(self.templates_url_names):
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_use_correct_templates(self):
        """The urls use correct templates."""
        for address, template in self.templates_url_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
