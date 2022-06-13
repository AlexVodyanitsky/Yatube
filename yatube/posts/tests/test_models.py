from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Название',
            slug='test-slug',
            description='Описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Текст',
            group=cls.group,
        )

    def test_verbose_name(self):
        """Verbose names are as expected."""
        field_verboses = {
            'text': 'Текст поста',
            'group': 'Группа'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text(self):
        """Help texts are as expected."""
        field_help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text, expected_value
                )

    def test_post_str_method_works(self):
        """Post str method works correctly."""
        self.assertEqual(self.post.text[:15], str(self.post))

    def test_group_str_method_works(self):
        """Group str method works correctly."""
        self.assertEqual(self.group.title, str(self.group))
