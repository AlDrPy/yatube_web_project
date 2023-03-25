from django.contrib.auth import get_user_model
from django.test import TestCase, Client


User = get_user_model()


class CoreURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(CoreURLTests.user)

    def test_404_page_uses_custom_template(self):
        '''Проверяем, что страница 404 отдаёт кастомный шаблон.'''
        clients = [
            self.guest_client,
            self.authorized_client
        ]
        for client in clients:
            with self.subTest(client=client):
                response = client.get('/unexisting-page/')
                self.assertTemplateUsed(response, 'core/404.html')
