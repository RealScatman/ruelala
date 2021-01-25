from django import forms

from .models import PickupTime


class PickupTimeForm(forms.ModelForm):

	pickup_date = forms.DateField(
		widget=forms.TextInput(
			attrs={
			"class": "form-control",
			"placeholder": "Add a Pickup Date"
			}
			)
		)

	timeslot = forms.TimeField(
		widget=forms.TextInput(
			attrs={
			"class": "form-control",
			"placeholder": "Add a Timeslot"
			}
			)
		)

	# address_line_2 = forms.CharField(
	# required=False,
	# widget=forms.TextInput(
	# 	attrs={
	# 	"class": "form-control",
	# 	"placeholder": "Address line 2"
	# 	}
	# 	)
	# )

	# city = forms.CharField(
	# widget=forms.TextInput(
	# 	attrs={
	# 	"class": "form-control",
	# 	"placeholder": "City"
	# 	}
	# 	)
	# )

	# # country = forms.CharField(
	# # widget=forms.TextInput(
	# # 	attrs={
	# # 	"class": "form-control",
	# # 	"placeholder": "Country"
	# # 	}
	# # 	)
	# # )

	# state = forms.CharField(
	# widget=forms.TextInput(
	# 	attrs={
	# 	"class": "form-control",
	# 	"placeholder": "State"
	# 	}
	# 	)
	# )

	# postal_code = forms.CharField(
	# widget=forms.TextInput(
	# 	attrs={
	# 	"class": "form-control",
	# 	"placeholder": "Zip Code"
	# 	}
	# 	)
	# )
	# delivery_frequency = forms.ChoiceField(
	# 	label='Delivery Frequency', 
	# 	choices=DELIVERY_CHOICES, 
	# 	widget=forms.Select(attrs={"class": "form-control"}))

	class Meta:
		model = PickupTime
		fields = [
			#'billing_profile',
			#'address_type',
			'pickup_date',
			'timeslot',
			#'city',
			#'country',		
			# 'state',
			# 'postal_code',
			# 'delivery_frequency',

		]