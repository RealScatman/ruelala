from django import forms
from django_select2.forms import Select2MultipleWidget

from django.forms.models import modelformset_factory
from crispy_forms.helper import FormHelper

from .models import Variation, Category, Size, Type, Availability, Product, ProductImage, ProductFeatured

CAT_CHOICES = (
	('electronics', 'Electronics'),
	('accessories', 'Accessories'),
)

AVAILABILITY_CHOICES = (
	('deliver', 'Deliver'),
	('pick-up-in-store', 'Pick Up in Store')
)

SIZE_CHOICES = (
	('4pk-16oz-cans', '4pk 16oz Cans'),
	('6pk-cans', '6pk Cans'),
	('12pk-cans', '12pk Cans'),
	('24pk-cans', '24pk Cans'),
	('30pk-cans', '30pk Cans'),
	('1-6-keg', '1/6 Keg'),
)


class ProductFilterForm(forms.Form):
	search = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Search'}), required=False)
	availability = forms.ModelMultipleChoiceField(
		label='Product Availability',
		queryset=Availability.objects.filter(active=True),
		#choices=AVAILABILITY_CHOICES,
		widget=forms.CheckboxSelectMultiple,
		required=False)
	category_id = forms.ModelMultipleChoiceField(
		label='Category',
		queryset=Category.objects.all(), 
		widget=forms.CheckboxSelectMultiple,
		#widget=Select2MultipleWidget,
		required=False)
	# category_title = forms.ChoiceField(
	# 	label='Category',
	# 	choices=CAT_CHOICES, 
	# 	widget=forms.CheckboxSelectMultiple, 
	# 	required=False)
	# size	= forms.TypedChoiceField(
	# 	label='Size',
	# 	#queryset=Variation.objects.all(),
	# 	choices=SIZE_CHOICES,
	# 	widget=forms.CheckboxSelectMultiple,
	# 	#to_field_name='slug',
	# 	# empty_value=None,
	# 	# error_messages=None,
	# 	required=False)
	size = forms.ModelMultipleChoiceField(
		label='Size',
		queryset=Size.objects.all(), 
		widget=forms.CheckboxSelectMultiple,
		#widget=Select2MultipleWidget,
		required=False)
	type = forms.ModelMultipleChoiceField(
		label='Type',
		queryset=Type.objects.all(), 
		widget=forms.CheckboxSelectMultiple,
		#widget=Select2MultipleWidget,
		required=False)
	#max_price = forms.DecimalField(decimal_places=2, max_digits=12, widget=forms.TextInput(attrs={'placeholder': 'Max Price'}), required=False)
	#min_price = forms.DecimalField(decimal_places=2, max_digits=12, required=False)

	# def __init__(self, *args, **kwargs):
	# 	super(ProductFilterForm, self).__init__(*args, **kwargs)
	# 	self.helper = FormHelper(self)
	# 	self.helper.form_show_errors = False
	# 	self.helper.error_text_inline = False
	# 	self.helper.form_show_labels = False


class VariationInventoryForm(forms.ModelForm):
	title = forms.CharField(label='Product Variation', widget=forms.TextInput(attrs={"class":"form-control", 'placeholder': 'ex. 6pk Cans or 12pk Btls'}))
	price = forms.DecimalField(decimal_places=2, max_digits=12, widget=forms.TextInput(attrs={"class":"form-control", 'placeholder': 'Regular Price'}), required=False)
	sale_price = forms.DecimalField(decimal_places=2, max_digits=12, widget=forms.TextInput(attrs={"class":"form-control", 'placeholder': 'Sale Price'}), required=False)
	inventory = forms.IntegerField(widget=forms.TextInput(attrs={"class":"form-control", 'placeholder': 'Add Inventory Count'}),)
	
	class Meta:
		model = Variation
		fields = [
			"title",
			"price",
			"sale_price",
			"inventory",
			"active",
			"featured",
			"availability",
			"size",
			"image",
		]

	# def __init__(self, *arg, **kwarg):
	# 	super(VariationInventoryForm, self).__init__(*arg, **kwarg)
	# 	self.empty_permitted = False


VariationInventoryFormSet = modelformset_factory(Variation, form=VariationInventoryForm, extra=1)


class VariationFilterForm(forms.Form):
	search = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Search'}), required=False)
	availability = forms.ModelMultipleChoiceField(
		label='Product Availability',
		queryset=Availability.objects.filter(active=True),
		#choices=AVAILABILITY_CHOICES,
		widget=forms.CheckboxSelectMultiple,
		required=False)
	category_id = forms.ModelMultipleChoiceField(
		label='Category',
		queryset=Category.objects.all(), 
		widget=forms.CheckboxSelectMultiple,
		#widget=Select2MultipleWidget,
		required=False)
	size = forms.ModelMultipleChoiceField(
		label='Size',
		queryset=Size.objects.all(), 
		widget=forms.CheckboxSelectMultiple,
		#widget=Select2MultipleWidget,
		required=False)
	type = forms.ModelMultipleChoiceField(
		label='Type',
		queryset=Type.objects.all(), 
		widget=forms.CheckboxSelectMultiple,
		#widget=Select2MultipleWidget,
		required=False)

class ProductImageForm(forms.ModelForm):
	class Meta:
		model = ProductImage
		fields = ["image", "product"]

ProductImageFormSet = modelformset_factory(ProductImage, form=ProductImageForm, extra=0)

class ProductForm(forms.ModelForm):
	title 	= forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Product Title"}))
	price = forms.DecimalField(decimal_places=2, max_digits=12, widget=forms.TextInput(attrs={"class":"form-control", 'placeholder': 'Regular Price'}), required=False)
	description = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control", 'rows': '3', "placeholder": "Product Description"}))
	type = forms.ModelChoiceField(queryset=Type.objects.all(), widget=forms.Select(attrs={"class": "form-control"}))
	default = forms.ModelChoiceField(queryset=Category.objects.all(), widget=forms.Select(attrs={"class": "form-control"}))
	categories = forms.ModelMultipleChoiceField(queryset=Category.objects.all(), widget=forms.CheckboxSelectMultiple(attrs={"class": ""}))
	# content = forms.CharField(widget=PagedownWidget(show_preview=False))
	# publish = forms.DateField(widget=forms.SelectDateWidget)

	class Meta:
		model = Product
		fields = [
			"title",
			"description",
			"price",
			"type",
			"categories",
			"default",
			#"image",
		]

class ProductFeaturedForm(forms.ModelForm):
	title 	= forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Splash Title"}))
	product = forms.ModelChoiceField(queryset=Product.objects.all(), widget=forms.Select(attrs={"class": "form-control"}))
	#price = forms.DecimalField(decimal_places=2, max_digits=12, widget=forms.TextInput(attrs={"class":"form-control", 'placeholder': 'Regular Price'}), required=False)
	text = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control", 'rows': '3', "placeholder": "Splash Description"}))
	#type = forms.ModelChoiceField(queryset=Type.objects.all(), widget=forms.Select(attrs={"class": "form-control"}))
	#default = forms.ModelChoiceField(queryset=Category.objects.all(), widget=forms.Select(attrs={"class": "form-control"}))
	#categories = forms.ModelMultipleChoiceField(queryset=Category.objects.all(), widget=forms.CheckboxSelectMultiple(attrs={"class": ""}))
	# content = forms.CharField(widget=PagedownWidget(show_preview=False))
	# publish = forms.DateField(widget=forms.SelectDateWidget)

	class Meta:
		model = ProductFeatured
		fields = [
			"title",
			"product",
			"text",
			#"description",
			#"price",
			#"type",
			#"categories",
			#"default",
			"make_image_background",
			"image",
		]