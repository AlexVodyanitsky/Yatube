import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='NoName')
        cls.second_user = User.objects.create(username='NoName2')
        cls.author = User.objects.create(username='author')
        cls.group = Group.objects.create(
            title='Название',
            slug='test-slug',
            description='Описание'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Текст',
            group=cls.group,
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            text='Коммент',
            author=cls.user,
            post=cls.post
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.second_authorized_client = Client()
        self.second_authorized_client.force_login(self.second_user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)
        cache.clear()

    def test_pages_use_correct_template(self):
        """The page templates used are as expected."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}
            ),
            'posts/profile.html': reverse(
                'posts:profile', kwargs={'username': f'{self.author}'}
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            ),
            'posts/create_post.html': reverse('posts:post_create'),
            'core/404.html': '/n0t_ex15ting_page/'
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
        response = self.authorized_client_author.get(reverse(
            'posts:edit', kwargs={'post_id': f'{self.post.id}'}))
        self.assertTemplateUsed(response, 'posts/create_post.html')
        response = self.authorized_client.get(reverse(
            'posts:edit', kwargs={'post_id': f'{self.post.id}'}), follow=True)
        self.assertTemplateUsed(response, 'posts/post_detail.html')

    def page_show_correct_context(self, url, param=None):
        """Basic context checking for all pages."""
        response = self.authorized_client_author.get(reverse(
            url, kwargs=param))
        if url in ('posts:post_create', 'posts:edit'):
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)
        else:
            if url == 'posts:post_detail':
                post = response.context['post']
                comment = response.context['comments'][0]
                self.assertEqual(comment.text, 'Коммент')

            else:
                post = response.context['page_obj'][0]
            self.assertEqual(post.author.username, 'author')
            self.assertEqual(post.text, 'Текст')
            self.assertEqual(post.group, self.post.group)
            self.assertEqual(post.image, self.post.image)

    def test_index_show_correct_context(self):
        """Index page uses context as expected."""
        self.page_show_correct_context('posts:index')

    def test_group_list_show_correct_context(self):
        """Group list page uses context as expected."""
        self.page_show_correct_context('posts:group_list',
                                       param={'slug': 'test-slug'})

    def test_profile_show_correct_context(self):
        """Profile page uses context as expected."""
        self.page_show_correct_context('posts:profile',
                                       param={'username': f'{self.author}'})

    def test_post_detail_show_correct_context(self):
        """Post page uses context as expected."""
        self.page_show_correct_context('posts:post_detail',
                                       param={'post_id': f'{self.post.id}'})

    def test_post_create_show_correct_context(self):
        """Create page uses context as expected."""
        self.page_show_correct_context('posts:post_create')

    def test_post_edit_show_correct_context(self):
        """Edit page uses context as expected."""
        self.page_show_correct_context('posts:edit',
                                       param={'post_id': f'{self.post.id}'})

    def test_index_cash(self):
        """Context index is cashed."""
        first_response = self.authorized_client.get(reverse('posts:index'))
        Post.objects.get(pk=self.post.pk).delete()
        second_response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_response.content, second_response.content)
        cache.clear()
        self.assertEqual(Post.objects.count(), 0)

    def test_authorized_client_follows(self):
        """Follow func check."""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': f'{self.author}'}
        ))
        follow = Follow.objects.get(id=1)
        self.assertEqual(follow.user.username, 'NoName')
        self.assertEqual(follow.author.username, 'author')

    def test_authorized_client_unfollows(self):
        """Unfollow func check."""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': f'{self.author}'}
        ))
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': f'{self.author}'}
        ))
        self.assertFalse(Follow.objects.filter(
            user_id=1,
            author_id=2).exists())

    def test_followers_see_new_post(self):
        """Follower can see post on the follow index page."""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': f'{self.author}'}
        ))
        form_data = {
            'text': 'Новый текст',
            'group': f'{self.group.pk}',
            'image': self.uploaded,
        }
        self.authorized_client_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post.author.username, 'author')
        self.assertEqual(first_post.text, 'Текст')
        self.assertEqual(first_post.group, self.post.group)
        self.assertEqual(first_post.image, self.post.image)
        second_response = self.second_authorized_client.get(reverse(
            'posts:follow_index'))
        second_page_obj = second_response.context['page_obj']
        self.assertEqual(len(second_page_obj), 0)

    def test_post_delete(self):
        """Post author is able to delete his post."""
        self.authorized_client_author.get(reverse(
            'posts:post_delete', kwargs={'post_id': f'{self.post.id}'}))
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='author')
        cls.group = Group.objects.create(
            title='Название',
            slug='test-slug',
            description='Описание'
        )
        Post.objects.bulk_create(
            [
                Post(
                    author=cls.author,
                    text=f'{i}',
                    group=cls.group
                ) for i in range(settings.POSTS_NUM + 3)
            ]
        )

    def setUp(self):
        self.guest_client = Client()

    def test_pages_contains_count_of_records(self):
        """Paginator works correctly."""
        reverse_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': f'{self.author}'}),
        ]
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response_page_1 = self.guest_client.get(reverse_name)
                response_page_2 = self.guest_client.get(
                    reverse_name, {'page': '2'}
                )
                self.assertEqual(
                    len(response_page_1.context['page_obj']),
                    settings.POSTS_NUM
                )
                self.assertEqual(len(response_page_2.context['page_obj']), 3)
