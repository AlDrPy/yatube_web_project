from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):  # Smoke testing
    def test_homepage(self):
        guest_client = Client()
        response = guest_client.get('/')
        self.assertEqual(response.status_code, 200)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.author = User.objects.create_user(username='PostAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        self.post_author_client = Client()
        self.post_author_client.force_login(PostURLTests.author)

    def test_pages_urls_exist_for_guests(self):
        """Тестируем страницы, доступные любому пользователю."""
        pages = {
            'index': '/',
            'group_list': f'/group/{PostURLTests.group.slug}/',
            'profile': f'/profile/{PostURLTests.user.username}/',
            'post_detail': f'/posts/{PostURLTests.post.id}/'
        }
        for page, url in pages.items():
            with self.subTest(page=page):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_pages_urls_exist_for_authorized_users(self):
        """Тестируем страницы, доступные авторизованному пользователю."""
        pages = {
            'index': '/',
            'group_list': f'/group/{PostURLTests.group.slug}/',
            'profile': f'/profile/{PostURLTests.user.username}/',
            'post_detail': f'/posts/{PostURLTests.post.id}/',
            'post_create': '/create/',
        }
        for page, url in pages.items():
            with self.subTest(page=page):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_post_edit_url_works_for_post_author_only(self):
        """Проверяем, что страница post_edit доступна только автору поста."""
        url = f'/posts/{PostURLTests.post.id}/edit/'
        just_user = self.authorized_client
        author = self.post_author_client

        requests = {
            just_user: url.replace('edit/', ''),
            author: url
        }
        for client, result in requests.items():
            with self.subTest(client=client):
                response = client.get(url)
                if client is not author:
                    self.assertRedirects(response, result)
                else:
                    self.assertEqual(response.status_code, 200)

    def test_post_create_redirect_anonymous(self):
        """Тестируем перенаправление анонимного пользователя
        при создании нового поста."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, ('/auth/login/?next=/create/'))

    def test_post_edit_url_redirect_anonymous(self):
        """Тестируем перенаправление анонимного пользователя
        при попытке редактирования поста."""
        response = self.guest_client.get(
            f'/posts/{PostURLTests.post.id}/edit/', follow=True)
        self.assertRedirects(
            response,
            (f'/auth/login/?next=/posts/{PostURLTests.post.id}/edit/'))

    def test_post_comment_url_redirect_anonymous(self):
        """Тестируем перенаправление анонимного пользователя
        при попытке оставить комментарий."""
        response = self.guest_client.get(
            f'/posts/{PostURLTests.post.id}/comment/', follow=True)
        self.assertRedirects(
            response,
            (f'/auth/login/?next=/posts/{PostURLTests.post.id}/comment/'))

    def test_page_not_exists(self):
        '''Проверяем ошибку 404 для несуществующей страницы'''
        response = self.guest_client.get('/unexisting-page/')
        self.assertEqual(response.status_code, 404)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTests.user.username}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{PostURLTests.post.id}/edit/': 'posts/create_post.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.post_author_client.get(address)
                self.assertTemplateUsed(response, template)
