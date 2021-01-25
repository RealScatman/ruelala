from django import forms
from django.contrib import messages
#from django.core.urlresolvers import reverse
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import ZipCodeImport, DeliveryZipCode

class ZipCodeImportForm(forms.ModelForm):
	imported = forms.BooleanField(label='Start Master ZipCode Import?', required=False)
	class Meta:
		model = ZipCodeImport
		fields = [
			'imported'
		]

	def save(self, commit=True):
		obj = super(ZipCodeImportForm, self).save(commit=False)
		if commit:
			obj.save()
			#request = self.request
			#request.session['guest_email_id'] = obj.id
		return obj

class CheckZipCodeForm(forms.Form):
	zipcode = forms.CharField(label='See if we deliver to your area?', widget=forms.TextInput(attrs={"class": 'form-control text-center', "placeholder": "Check your zipcode"}))

	# def check_zipcode(self):
	# 	zipcode = self.cleaned_data.get('zipcode')
	# 	qs = DeliveryZipCode.objects.zipcode_exists(zipcode)
	# 	request = self.request
	# 	if qs.exists():
	# 		product_link = reverse("products")
	# 		msg = """We deliver you your area! Please select a <a href="{link}">box</a>.
	# 		""".format(link=product_link)
	# 		return messages.success(request, mark_safe(msg))
	# 		#raise forms.ValidationError(mark_safe(msg))
	# 	return zipcode