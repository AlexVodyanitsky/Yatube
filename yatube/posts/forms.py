from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    """Post creation form."""
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    """Comment creation form."""
    class Meta:
        model = Comment
        fields = ('text',)
