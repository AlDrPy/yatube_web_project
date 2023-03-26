# deals/tests/test_views.py
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_pic = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.test_pic,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-group-slug2',
            description='Тестовое описание2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-group-slug'}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'NoName'}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': 1}): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': 1}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))

        response_posts = response.context['page_obj'].object_list
        first_post = response_posts[0]
        self.assertEqual(len(response_posts), 1)
        self.assertEqual(first_post.id, self.post.id)
        self.assertEqual(first_post.text, 'Тестовый пост')
        self.assertEqual(first_post.author.username, 'NoName')
        self.assertIsNotNone(first_post.image)
        self.assertTrue(first_post.image.name, 'posts/small.gif')

    def test_group_list_page_shows_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-group-slug'}))

        response_posts = response.context['page_obj'].object_list
        first_post = response_posts[0]
        response_group = response.context['group']
        db_posts_filtered = Post.objects.filter(group=self.group)
        self.assertIn(first_post, db_posts_filtered)
        self.assertEqual(len(response_posts), 1)
        self.assertEqual(first_post.group, self.group)
        self.assertEqual(response_group.title, 'Тестовая группа')
        self.assertEqual(response_group.slug, 'test-group-slug')
        self.assertEqual(response_group.description, 'Тестовое описание')
        self.assertIsNotNone(first_post.image)
        self.assertTrue(first_post.image.name, 'posts/small.gif')

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'NoName'}))

        response_posts = response.context['page_obj'].object_list
        first_post = response_posts[0]
        db_posts_filtered = Post.objects.filter(author=self.post.author)
        self.assertIn(first_post, db_posts_filtered)
        self.assertEqual(len(response_posts), 1)
        self.assertEqual(first_post.author, self.post.author)
        self.assertIsNotNone(first_post.image)
        self.assertTrue(first_post.image.name, 'posts/small.gif')

    def test_post_detail_page_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1}))

        db_posts_filtered = Post.objects.filter(id=self.post.id)
        response_post = response.context['post']
        self.assertIn(response_post, db_posts_filtered)
        self.assertIsNotNone(response_post.image)
        self.assertTrue(response_post.image.name, 'posts/small.gif')

    def test_post_create_page_shows_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create'))

        response_form = response.context['form']
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response_form.fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_shows_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': 1}))

        response_post = response.context['form'].instance
        db_posts_filtered = Post.objects.filter(id=self.post.id)
        self.assertIn(response_post, db_posts_filtered)

    def test_create_new_post_with_group(self):
        """Дополнительная проверка при создании нового поста с группой."""
        reverses = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-group-slug'}),
            reverse(
                'posts:profile',
                kwargs={'username': 'NoName'}),
        ]
        for reverse_name in reverses:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                response_post = response.context['page_obj'][0]
                self.assertEqual(response_post.id, self.post.id)

        # Убедимся, что пост не попал на страницу группы 2:
        response_gr2 = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test-group-slug2'}))
        object_list_gr2 = response_gr2.context['page_obj']
        self.assertEqual(len(object_list_gr2), 0)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.NUMBER_OF_POSTS = 13
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group-slug',
            description='Тестовое описание',
        )
        Post.objects.bulk_create([
            Post(
                text=f'test_post_{i}',
                author=cls.user,
                group=cls.group) for i in range(
                1, cls.NUMBER_OF_POSTS + 1)
        ])

    def setUp(self):
        self.client = Client()

    def test_first_page_contains_ten_records(self):
        '''Количество постов на первой странице равно 10.'''
        reverses = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-group-slug'}),
            reverse(
                'posts:profile',
                kwargs={'username': 'NoName'}),
        ]
        for reverse_name in reverses:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                # Проверка: количество постов на первой странице равно 10.
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        '''На второй странице должно быть три поста.'''
        reverses = [
            reverse('posts:index') + '?page=2',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-group-slug'}) + '?page=2',
            reverse(
                'posts:profile',
                kwargs={'username': 'NoName'}) + '?page=2',
        ]
        for reverse_name in reverses:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                # Проверка: на второй странице должно быть три поста.
                self.assertEqual(len(response.context['page_obj']), 3)


class CachePagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def test_cache_index_page(self):
        response1 = self.client.get(reverse('posts:index'))
        Post.objects.create(
            author=self.user,
            text='Тестовый пост2',
        )
        response2 = self.client.get(reverse('posts:index'))
        self.assertEqual(response1.content, response2.content)
        cache.clear()
        response3 = self.client.get(reverse('posts:index'))
        self.assertNotEqual(response1.content, response3.content)


class FollowTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='YourFan')
        cls.user_notfollower = User.objects.create_user(username='NotYourFan')
        cls.author = User.objects.create_user(username='Author')
        cls.author2 = User.objects.create_user(username='Author2')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Пост автора',
        )
        cls.post2 = Post.objects.create(
            author=cls.author2,
            text='Пост автора 2',
        )
        cls.follow = Follow.objects.create(
            user=cls.user_follower,
            author=cls.author,
        )

    def setUp(self):
        self.authorized_flw_client = Client()
        self.authorized_flw_client.force_login(FollowTests.user_follower)
        self.authorized_notflw_client = Client()
        self.authorized_notflw_client.force_login(FollowTests.user_notfollower)

    def test_follow_view(self):
        '''Тестирование функции подписки на автора.'''
        follow_count = Follow.objects.count()
        response = self.authorized_notflw_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username}
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.author.username})
        )

    def test_unfollow_view(self):
        '''Тестирование функции отписки от автора.'''
        follow_count = Follow.objects.count()
        response = self.authorized_flw_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author.username}
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.author.username})
        )

    def test_followers_see_only_their_author_posts(self):
        '''Посты авторов попадают только к подписчикам.'''
        response_flw = self.authorized_flw_client.get(
            reverse('posts:follow_index'))
        follower_posts = response_flw.context['page_obj']

        response_notflw = self.authorized_notflw_client.get(
            reverse('posts:follow_index'))
        non_follower_posts = response_notflw.context['page_obj']
        # Простые юзеры не получают избранных постов
        self.assertEqual(len(non_follower_posts), 0)
        # Посты автора попадают к подписчикам
        author_post = Post.objects.get(author=self.author)
        self.assertIn(author_post, follower_posts)
        # Посты других авторов не попадают к подписчикам
        author2_post = Post.objects.get(author=self.author2)
        self.assertNotIn(author2_post, follower_posts)
