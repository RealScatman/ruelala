from django import forms

from pagedown.widgets import PagedownWidget

from .models import Post


class PostForm(forms.ModelForm):
	title 	= forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Post Title"}))
	content = forms.CharField(widget=PagedownWidget(show_preview=False))
	publish = forms.DateField(widget=forms.SelectDateWidget)

	class Meta:
		model = Post
		fields = [
			"title",
			"content",
			"image",
			"draft",
			"featured",
			"publish",
		]
