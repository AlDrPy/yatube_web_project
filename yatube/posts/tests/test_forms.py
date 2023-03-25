import shutil
import tempfile

from posts.models import Post, Group, Comment
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)
        self.test_pic = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.test_pic,
            content_type='image/gif'
        )

    def test_create_post(self):
        """Валидная форма создает объект модели Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый тестовый пост',
            'group': self.group.pk,
            'image': self.uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={'username': 'NoName'}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Новый тестовый пост',
                group=self.group,
            ).exists()
        )
        post = Post.objects.get(text='Новый тестовый пост')
        self.assertIsNotNone(post.image)
        self.assertTrue(post.image.name, 'posts/small.gif')

    def test_edit_post(self):
        '''При редактировании поста изменения сохраняются верно.'''
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Изменённый пост',
            'group': self.group.pk,
            'image': self.uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertNotEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Изменённый пост',
                group=self.group
            ).exists()
        )
        db_post = Post.objects.get(id=self.post.id)
        self.assertEqual(db_post.text, 'Изменённый пост')
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id})
        )
        self.assertIsNotNone(db_post.image)
        self.assertTrue(db_post.image.name, 'posts/small.gif')


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(CommentCreateFormTests.user)

    def test_create_comment(self):
        """Валидная форма создает объект модели Comment."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Новый тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='Новый тестовый комментарий',
            ).exists()
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', kwargs={'post_id': 1}))
