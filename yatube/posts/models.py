from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
LEN_OBJ_NAME = 15


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название сообщества'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Слаг (человеко-читаемый URL для страницы)'
    )
    description = models.TextField(verbose_name='Описание сообщества')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Сообщество'
        verbose_name_plural = 'Сообщества'


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор поста'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name='Сообщество',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    def __str__(self):
        return self.text[:LEN_OBJ_NAME]

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Связанный пост'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Напишите комментарий'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата комментария'
    )

    def __str__(self):
        return (
            f'Комментарий к посту с id {self.post.id}:'
            f'{self.text[:LEN_OBJ_NAME]}'
        )

    class Meta:
        ordering = ['-created']
        verbose_name = 'Коммент'
        verbose_name_plural = 'Комменты'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    def __str__(self):
        return (
            f'Пользователь {self.user} подписан '
            f'на автора {self.author}'
        )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]
