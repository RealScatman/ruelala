
from django import forms
from django.contrib.auth import get_user_model

from .models import UserAddress, StripeOrder, Order, UserCheckin

User = get_user_model()

class GuestCheckoutForm(forms.Form):
	email = forms.EmailField()
	email2 = forms.EmailField(label='Verify Email')

	def clean_email2(self):
		email = self.cleaned_data.get("email")
		email2 = self.cleaned_data.get("email2")

		if email == email2:
			user_exists = User.objects.filter(email=email).count()
			if user_exists != 0:
				raise forms.ValidationError("This User already exists. Please login instead.")
			return email2
		else:
			raise forms.ValidationError("Please confirm emails are the same")




class AddressForm(forms.Form):
	billing_address = forms.ModelChoiceField(
			queryset=UserAddress.objects.filter(type="billing"),
			widget = forms.RadioSelect,
			empty_label = None
			)
	# shipping_address = forms.ModelChoiceField(
	# 	queryset=UserAddress.objects.filter(type="shipping"),
	# 	widget = forms.RadioSelect,
	# 	empty_label = None,
		
	# 	)



class UserAddressForm(forms.ModelForm):
	class Meta:
		model = UserAddress
		fields = [
			'street',
			'city',
			'state',
			'zipcode',
			'type'
		]

ORDER_STATUS_CHOICES = (
	('created', 'Created'),
	('paid', 'Paid'),
	('ready', 'Ready'),
	('shipped', 'Shipped'),
	('picked-up', 'Picked Up'),
	('refunded', 'Refunded'),
)

class StripeOrderChangeForm(forms.ModelForm):
	status = forms.ChoiceField(
		label='Order Status:', 
		choices=ORDER_STATUS_CHOICES,
		required=False, 
		widget=forms.Select(attrs={"class": 'form-control'}))


	class Meta:
		model = StripeOrder
		fields = ['status']

class OrderChangeForm(forms.ModelForm):
	status = forms.ChoiceField(
		label='Order Status:', 
		choices=ORDER_STATUS_CHOICES,
		required=False, 
		widget=forms.Select(attrs={"class": 'form-control'}))


	class Meta:
		model = Order
		fields = ['status']

class UserCheckinForm(forms.ModelForm):
	# status = forms.ChoiceField(
	# 	label='Order Status:', 
	# 	choices=ORDER_STATUS_CHOICES,
	# 	required=False, 
	# 	widget=forms.Select(attrs={"class": 'form-control'}))
	parking_slot = forms.IntegerField(label='', widget=forms.TextInput(attrs={"class": 'form-control mb-1 text-center', "placeholder": 'parking slot number'}))

	class Meta:
		model = UserCheckin
		fields = ['parking_slot']

	def save(self, commit=True):
		#request = self.request
		# Save the provided password in hashed format
		user_checkin = super(UserCheckinForm, self).save(commit=False)
		#user.set_password(self.cleaned_data["password1"])
		#user.is_active = False # send confirmation email via signals
		#user.is_active = False
		user_checkin.active = True # set this to true to bypass activation email process
		# box_obj, new_obj = BoxSelection.objects.new_or_get(self.request)
		# box_obj.user = user
		# box_obj = BoxSelection.objects.new_or_get(self.request)
		#box_obj = BoxSelection.objects.update(user=user)
		#obj = EmailActivation.objects.create(user=user)
		#obj.send_activation_email()
		if commit:
			print("User checking in...")
			user_checkin.save()
			#box_obj.save()
			#request = self.request
			#request.session['register_email_id'] = user.id
		return user_checkin