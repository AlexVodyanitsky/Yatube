from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='NoName')
        cls.author = User.objects.create(username='author')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Текст',
        )
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test-slug',
            description='Описание'
        )
        cls.templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/author/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)

    def test_urls_for_guest_exists(self):
        for url in list(self.templates_url_names)[:-2]:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_for_authorized_exists(self):
        testing_url = list(self.templates_url_names)[-2]
        response = self.authorized_client.get(testing_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_for_author_exists(self):
        testing_url = list(self.templates_url_names)[-1]
        response = self.authorized_client_author.get(testing_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        for address, template in self.templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_404_page(self):
        response = self.authorized_client.get('/n0t_ex15ting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
