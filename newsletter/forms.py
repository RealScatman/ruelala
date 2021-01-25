from django import forms

from .models import SignUp

class ContactForm(forms.Form):
	full_name = forms.CharField(label='Full Name', widget=forms.TextInput(attrs={'placeholder': 'add your full name'}), required=False)
	email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'add your email'}))
	message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'provide a message'}))


class SignUpForm(forms.ModelForm):
	full_name = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'add your full name'}))
	email = forms.EmailField(label='', widget=forms.TextInput(attrs={'placeholder': 'add your email'}))
	class Meta:
		model = SignUp
		fields = ['full_name', 'email']
		### exclude = ['full_name']
	
	def clean_email(self):
		email = self.cleaned_data.get('email')
		email_base, provider = email.split("@")
		domain, extension = provider.split('.')
		# if not domain == 'USC':
		# 	raise forms.ValidationError("Please make sure you use your USC email.")
		# if not extension == "com":
		# 	raise forms.ValidationError("Please use a valid .COM email address")
		return email

	def clean_full_name(self):
		full_name = self.cleaned_data.get('full_name')
		#write validation code.
		return full_name