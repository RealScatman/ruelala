from django.contrib.auth import authenticate, login, get_user_model
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
#from django.core.urlresolvers import reverse
from django.urls import reverse
from django.utils.safestring import mark_safe

User = get_user_model()

from .models import GuestEmail, BoxSelection #, EmailActivation,
#from addresses.models import DeliveryFrequency
from .signals import user_logged_in

DELIVERY_CHOICES = [
	('every-week', 'Every Week'),
	('every-other-week', 'Every Other Week')
]

# class ReactivateEmailForm(forms.Form):
# 	email = forms.EmailField()

# 	def clean_email(self):
# 		email = self.cleaned_data.get('email')
# 		qs = EmailActivation.objects.email_exists(email)
# 		if not qs.exists():
# 			register_link = reverse("register")
# 			msg = """This email does not exist, please <a href="{link}">register</a>.
# 			""".format(link=register_link)
# 			#messages.success(request, mark_safe(msg))
# 			raise forms.ValidationError(mark_safe(msg))
# 		return email

class UserAdminCreationForm(forms.ModelForm):
	""" A form for creating new users. Includes all the required fields, plus 
	a repeated password.
	"""
	password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
	password2 = forms.CharField(label='Password Confirm', widget=forms.PasswordInput)

	class Meta:
		model = User
		fields = ('full_name','email')

	def clean_password2(self):
		# Check that the two password entries match
		password1 = self.cleaned_data.get("password1")
		password2 = self.cleaned_data.get("password2")
		if password1 and password2 and password1 != password2:
			raise forms.ValidationError("Passwords do not match")
		return password2

	def save(self, commit=True):
		# Save the provided password in hashed format
		user = super(UserAdminCreationForm, self).save(commit=False)
		user.set_password(self.cleaned_data["password1"])
		if commit:
			user.save()
		return user


class UserDetailChangeForm(forms.ModelForm):
	full_name = forms.CharField(label='Name (displays on bids)', required=False, widget=forms.TextInput(attrs={"class": 'form-control'}))


	class Meta:
		model = User
		fields = ['full_name']

class UserAdminChangeForm(forms.ModelForm):
	"""A form for updating users. Includes all the fields on the user
	but replaces the password field with admin's password hash display field
	"""
	password = ReadOnlyPasswordHashField()

	class Meta:
		model = User
		fields = ('full_name','email', 'password', 'is_active', 'admin')

	def clean_password(self):
		# Regardless of what the user provides, return the initial value.
		# This is done here, rather than on the field, because the
		# field does not have access to the initial value
		return self.initial["password"]

# class UserSubscriptionForm(forms.ModelForm):
# 	is_member = forms.BooleanField(label='Active Subscription?', required=False)
# 	class Meta:
# 		model = User
# 		fields = [
# 			'is_member'
# 		]



class GuestForm(forms.ModelForm):
	#email = forms.EmailField()
	email 	= forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Your email address"}))


	class Meta:
		model = GuestEmail
		fields = [
			'email',
		]

	def __init__(self, request, *args, **kwargs):
		self.request = request
		super(GuestForm, self).__init__(*args, **kwargs)

	def save(self, commit=True):
		# Save the provided password in hashed format
		obj = super(GuestForm, self).save(commit=False)
		if commit:
			obj.save()
			request = self.request
			request.session['guest_email_id'] = obj.id
		return obj



class LoginForm(forms.Form):
	email 	= forms.EmailField(label='Email', widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Your email address"}))
	#username = forms.CharField(widget=forms.TextInput(attrs={"class":"form-control","placeholder": "Enter Username"}))
	#password = forms.CharField(widget=forms.PasswordInput(attrs={"class":"form-control","placeholder": "Enter Password"}))
	password = forms.CharField(widget=forms.PasswordInput(attrs={"class":"form-control","placeholder": "Enter Password"}))

	def __init__(self, request, *args, **kwargs):
		self.request = request
		super(LoginForm, self).__init__(*args, **kwargs)

	def clean(self):
		request = self.request
		data = self.cleaned_data
		email = data.get("email")
		password = data.get("password")
		qs = User.objects.filter(email=email)
		if qs.exists():
			# user email is registered, check active/email activation
			not_active = qs.filter(is_active=False)
			if not_active.exists():
				## user is not active, check email activation
				link = reverse("account:resend-activation")
				reconfirm_msg = """Go here to
				<a href='{resend_link}'>resend confirmation email</a>.
				""".format(resend_link= link)
				confirm_email = EmailActivation.objects.filter(email=email)
				is_confirmable = confirm_email.confirmable().exists()
				if is_confirmable:
					msg1 = "Please check your email to confirm your account or " + reconfirm_msg.lower()
					raise forms.ValidationError(mark_safe(msg1))
				email_confirm_exists = EmailActivation.objects.email_exists(email).exists()
				if email_confirm_exists:
					msg2 = "Email not confirmed. " + reconfirm_msg
					raise forms.ValidationError(mark_safe(msg2))
				if not is_confirmable and not email_confirm_exists:
					raise forms.ValidationError("This user is inactive.")




		user = authenticate(request, username=email, password=password)
		if user is None:
			raise forms.ValidationError("Invalid Credentials")
		login(request, user)
		self.user = user
		user_logged_in.send(user.__class__, instance=user, request=request) # randomly deleted from lecture 186 ?? next 4 lines as well
		try:
			del request.session['guest_email_id']
		except:
			pass
		return data


class RegisterForm(forms.ModelForm):
	""" A form for creating new users. Includes all the required fields, plus 
	a repeated password.
	"""
	full_name 	= forms.CharField(label='', widget=forms.TextInput(attrs={"class": 'form-control mb-3', "placeholder": "Your full name"}))
	email 		= forms.EmailField(label='', widget=forms.EmailInput(attrs={"class": "form-control mb-3", "placeholder": "Your email address"}))
	#law_firm 	= forms.CharField(label='', widget=forms.TextInput(attrs={"class": 'form-control mb-3', "placeholder": "Your law firm"}))
	#specialty	= forms.ChoiceField(label='*Cases you are interested in', choices=SPECIALTY_CHOICES, widget=forms.Select(attrs={"class": "form-control mb-2"}), required=True)
	password1 	= forms.CharField(label='Password', widget=forms.PasswordInput(attrs={"class": 'form-control', "placeholder": "Enter Password"}))
	password2 	= forms.CharField(label='Password Confirm', widget=forms.PasswordInput(attrs={"class": 'form-control', "placeholder": "Confirm Password"}))

	class Meta:
		model = User
		fields = ('full_name','email', 
					#'law_firm', 'specialty'
				)

	def __init__(self, request, *args, **kwargs):
		self.request = request
		super(RegisterForm, self).__init__(*args, **kwargs)

	def clean_password2(self):
		# Check that the two password entries match
		password1 = self.cleaned_data.get("password1")
		password2 = self.cleaned_data.get("password2")
		if password1 and password2 and password1 != password2:
			raise forms.ValidationError("Passwords do not match")
		return password2

	def save(self, commit=True):
		#request = self.request
		# Save the provided password in hashed format
		user = super(RegisterForm, self).save(commit=False)
		user.set_password(self.cleaned_data["password1"])
		#user.is_active = False # send confirmation email via signals
		#user.is_active = False
		user.is_active = True # set this to true to bypass activation email process
		#obj = EmailActivation.objects.create(user=user)
		#obj.send_activation_email()
		if commit:
			print("register commit?")
			user.save()
		return user


class RegisterLiteForm(forms.ModelForm):
	""" A form for creating new users. Includes all the required fields, plus 
	a repeated password.
	"""
	full_name 	= forms.CharField(label='', widget=forms.TextInput(attrs={"class": 'form-control mb-3', "placeholder": "Your full name"}))
	email 		= forms.EmailField(label='', widget=forms.EmailInput(attrs={"class": "form-control mb-3", "placeholder": "Your email address"}))
	#law_firm 	= forms.CharField(label='', widget=forms.TextInput(attrs={"class": 'form-control mb-3', "placeholder": "Your law firm"}))
	#specialty	= forms.ChoiceField(label='*Cases you are interested in', choices=SPECIALTY_CHOICES, widget=forms.Select(attrs={"class": "form-control mb-2"}), required=True)
	password1 	= forms.CharField(label='Password', widget=forms.PasswordInput(attrs={"class": 'form-control', "placeholder": "Enter Password"}))
	password2 	= forms.CharField(label='Password Confirm', widget=forms.PasswordInput(attrs={"class": 'form-control', "placeholder": "Confirm Password"}))

	class Meta:
		model = User
		fields = ('full_name','email', 
					#'law_firm', 'specialty'
				)

	def __init__(self, request, *args, **kwargs):
		self.request = request
		super(RegisterLiteForm, self).__init__(*args, **kwargs)

	def clean_password2(self):
		# Check that the two password entries match
		password1 = self.cleaned_data.get("password1")
		password2 = self.cleaned_data.get("password2")
		if password1 and password2 and password1 != password2:
			raise forms.ValidationError("Passwords do not match")
		return password2

	def save(self, commit=True):
		#request = self.request
		# Save the provided password in hashed format
		user = super(RegisterLiteForm, self).save(commit=False)
		user.set_password(self.cleaned_data["password1"])
		#user.is_active = False # send confirmation email via signals
		#user.is_active = False
		user.is_active = True # set this to true to bypass activation email process
		# box_obj, new_obj = BoxSelection.objects.new_or_get(self.request)
		# box_obj.user = user
		# box_obj = BoxSelection.objects.new_or_get(self.request)
		#box_obj = BoxSelection.objects.update(user=user)
		#obj = EmailActivation.objects.create(user=user)
		#obj.send_activation_email()
		if commit:
			print("register commit?")
			user.save()
			#box_obj.save()
			request = self.request
			request.session['register_email_id'] = user.id
		return user


# class DeliveryFrequencyForm(forms.ModelForm):
# 	delivery_frequency 	= forms.ChoiceField(label='Delivery Frequency', choices=DELIVERY_CHOICES, widget=forms.Select(attrs={"class": "form-control mb-3"}))

# 	class Meta:
# 		model = DeliveryFrequency
# 		fields = ('delivery_frequency',
# 				)

# 	def __init__(self, request, *args, **kwargs):
# 		self.request = request
# 		super(DeliveryFrequencyForm, self).__init__(*args, **kwargs)

	
# 	def save(self, commit=True):
# 		# Save the provided password in hashed format
# 		obj = super(DeliveryFrequencyForm, self).save(commit=False)
# 		if commit:
# 			obj.save()
# 			#request = self.request
# 			#request.session['guest_email_id'] = obj.id
# 		return obj