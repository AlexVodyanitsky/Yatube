import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='author')
        cls.first_group = Group.objects.create(
            title='Название',
            slug='test-slug',
            description='Описание'
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='Текст',
            group=cls.first_group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)

    def test_create_post_form(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый текст',
            'group': f'{self.first_group.pk}',
            'image': uploaded
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': f'{self.author}'}
        ))
        post = Post.objects.get(id=2)
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.text, 'Новый текст')
        self.assertEqual(post.group, self.first_group)
        self.assertEqual(post.image, 'posts/small.gif')

    def test_edit_post_form(self):
        second_group = Group.objects.create(
            title='Другое название',
            slug='other-test-slug',
            description='Другое описание'
        )
        form_data = {
            'text': 'Другой текст',
            'group': f'{second_group.pk}',
        }
        response = self.authorized_client_author.post(reverse(
            'posts:edit', kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': f'{self.post.id}'}
        ))
        edited_post = Post.objects.get(id=self.post.id)
        self.assertEqual(edited_post.author, self.author)
        self.assertEqual(edited_post.text, 'Другой текст')
        self.assertEqual(edited_post.group, second_group)

    def test_guest_client_post_request(self):
        response = self.guest_client.post(
            reverse('posts:post_create')
        )
        self.assertRedirects(
            response,
            f'{reverse("users:login")}?next={reverse("posts:post_create")}'
        )

    def test_guest_client_comment(self):
        response = self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id})
        )
        self.assertRedirects(
            response,
            f'{reverse("users:login")}?next='
            f'{reverse("posts:add_comment", kwargs={"post_id": self.post.id})}'
        )
