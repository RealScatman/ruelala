from django import forms

from .models import Address, DeliveryFrequency

DELIVERY_CHOICES = [
	('every-week', 'Every Week'),
	('every-other-week', 'Every Other Week')
]

class AddressForm(forms.ModelForm):

	address_line_1 = forms.CharField(
		widget=forms.TextInput(
			attrs={
			"class": "form-control",
			"placeholder": "Address Line 1"
			}
			)
		)

	address_line_2 = forms.CharField(
	required=False,
	widget=forms.TextInput(
		attrs={
		"class": "form-control",
		"placeholder": "Address line 2"
		}
		)
	)

	city = forms.CharField(
	widget=forms.TextInput(
		attrs={
		"class": "form-control",
		"placeholder": "City"
		}
		)
	)

	# country = forms.CharField(
	# widget=forms.TextInput(
	# 	attrs={
	# 	"class": "form-control",
	# 	"placeholder": "Country"
	# 	}
	# 	)
	# )

	state = forms.CharField(
	widget=forms.TextInput(
		attrs={
		"class": "form-control",
		"placeholder": "State"
		}
		)
	)

	postal_code = forms.CharField(
	widget=forms.TextInput(
		attrs={
		"class": "form-control",
		"placeholder": "Zip Code"
		}
		)
	)
	delivery_frequency = forms.ChoiceField(
		label='Delivery Frequency', 
		choices=DELIVERY_CHOICES, 
		widget=forms.Select(attrs={"class": "form-control"}))

	class Meta:
		model = Address
		fields = [
			#'billing_profile',
			#'address_type',
			'address_line_1',
			'address_line_2',
			'city',
			#'country',		
			'state',
			'postal_code',
			'delivery_frequency',

		]



class AddressCheckoutForm(forms.ModelForm):
	"""
	User-related checkout address create form
	"""
	class Meta:
		model = Address
		fields = [
			'nickname',
			'name',
			#'billing_profile',
			#'address_type',
			'address_line_1',
			'address_line_2',
			'city',
			'country',
			'state',
			'postal_code'
		]


class DeliveryFrequencyForm(forms.ModelForm):
	delivery_frequency = forms.ChoiceField(
	label='Delivery Frequency', 
	choices=DELIVERY_CHOICES, 
	widget=forms.Select(attrs={"class": "form-control"}))
	delivery_start = forms.DateTimeField(
	label='Delivery Start Date', 
	widget=forms.DateTimeInput(attrs={"class": "form-control"}))

	class Meta:
		model = DeliveryFrequency
		fields = [
			#'delivery_frequency',
			'delivery_start',
		]
