
from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Добавить картинку'
        }

    def clean_text(self):
        data = self.cleaned_data['text']
        if data.isspace():
            raise forms.ValidationError(
                'Поле текст не должно быть пустым'
            )
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {'text': 'Текст комментария'}

    def clean_text(self):
        data = self.cleaned_data['text']
        if data.isspace():
            raise forms.ValidationError(
                'Поле текст не должно быть пустым'
            )
        return data
