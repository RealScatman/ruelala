import requests

from django.core.exceptions import ImproperlyConfigured
from django.contrib import messages
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import FormView
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone

from django_filters import FilterSet, CharFilter, NumberFilter, RangeFilter, BooleanFilter
# Create your views here.
from .forms import VariationInventoryFormSet, ProductFilterForm, VariationFilterForm, ProductForm, VariationInventoryForm, ProductImageFormSet, ProductFeaturedForm
from .mixins import StaffRequiredMixin
from .models import Product, Variation, Category, ProductImage


# def product_list(request):
# 	qs = Product.objects.all()
# 	ordering = request.GET.get("ordering")
# 	if ordering:
# 		qs = Product.objects.all().order_by(ordering)
# 	f = ProductFilter(request.GET, queryset=qs)
# 	return render(request, "products/product_list.html", {"object_list": f })


class CategoryListView(ListView):
	model = Category
	queryset = Category.objects.all()
	template_name = "products/category_list.html"

	def get_context_data(self, *args, **kwargs):
		context = super(CategoryListView, self).get_context_data(*args, **kwargs)
		#all_variations = Variation.objects.filter(active=True)
		all_categories = Category.objects.all()
		#context["all_variations"] = all_variations
		context["all_categories"] = all_categories
		#context["filter_form"] = ProductFilterForm(data=self.request.GET or None)
		return context



class CategoryDetailView(DetailView):
	model = Category

	def get_context_data(self, *args, **kwargs):
		context = super(CategoryDetailView, self).get_context_data(*args, **kwargs)
		obj = self.get_object()
		product_set = obj.product_set.all()
		#print(product_set)
		variations = Variation.objects.filter(product__in=product_set)
		#print(variations)
		default_products = obj.default_category.all()
		products = ( product_set | default_products ).distinct()
		context["products"] = products
		context["variations"] = variations
		all_categories = Category.objects.all()
		context["all_categories"] = all_categories
		return context


class VariationListView(StaffRequiredMixin, ListView):
	#form_class = VariationInventoryForm
	model = Variation
	queryset = Variation.objects.all()
	#template_name = "products/variation_list.html"

	def get_context_data(self, *args, **kwargs):
		context = super(VariationListView, self).get_context_data(*args, **kwargs)
		context["formset"] = VariationInventoryFormSet(queryset=self.get_queryset())
		return context

	def get_queryset(self, *args, **kwargs):
		product_pk = self.kwargs.get("pk")
		if product_pk:
			product = get_object_or_404(Product, pk=product_pk)
			queryset = Variation.objects.filter(product=product)
		return queryset

	def post(self, request, *args, **kwargs):
		formset = VariationInventoryFormSet(request.POST, request.FILES)
		if formset.is_valid():
			formset.save(commit=False)
			for form in formset:
				new_item = form.save(commit=False)
				product_pk = self.kwargs.get("pk")
				product = get_object_or_404(Product, pk=product_pk)
				new_item.product = product
				#print(new_item.title)
				#new_item.save()
				if new_item.title != '':
					new_item.save()
				else:
					pass	
				# if form.empty_permitted and not form.has_changed():
				# 	print("getting hit")
				# 	return redirect("product-variations-list")
					
			messages.success(request, "Your inventory and pricing has been updated.")
			return redirect("products:product-variations-list")
		raise Http404


class ProductFilter(FilterSet):
	search = CharFilter(field_name='title', lookup_expr='icontains', distinct=True)
	category = CharFilter(field_name='categories__title', lookup_expr='icontains', distinct=True)
	category_id = CharFilter(field_name='categories__id', lookup_expr='icontains', distinct=True)
	min_price = NumberFilter(field_name='variation__price', lookup_expr='gte', distinct=True) # (some_price__gte=somequery)
	max_price = NumberFilter(field_name='variation__price', lookup_expr='lte', distinct=True)
	size = CharFilter(field_name='variation__size', lookup_expr='exact', distinct=True)
	type = CharFilter(field_name='type__id', lookup_expr='icontains', distinct=True)
	availability = CharFilter(field_name='variation__availability', lookup_expr='exact', distinct=True)

	class Meta:
		model = Product
		fields = [
			'min_price',
			'max_price',
			'category',
			'type',
			'availability',
			'title',
			'search',
			'size',
			'description',
		]


# def product_list(request):
# 	qs = Product.objects.all()
# 	ordering = request.GET.get("ordering")
# 	if ordering:
# 		qs = Product.objects.all().order_by(ordering)
# 	f = ProductFilter(request.GET, queryset=qs)
# 	return render(request, "products/product_list.html", {"object_list": f })


class FilterMixin(object):
	filter_class = None
	search_ordering_param = "ordering"

	def get_queryset(self, *args, **kwargs):
		try:
			qs = super(FilterMixin, self).get_queryset(*args, **kwargs)
			return qs
		except:
			raise ImproperlyConfigured("You must have a queryset in order to use the FilterMixin")

	def get_context_data(self, *args, **kwargs):
		context = super(FilterMixin, self).get_context_data(*args, **kwargs)
		qs = self.get_queryset()
		ordering = self.request.GET.get(self.search_ordering_param)
		if ordering:
			qs = qs.order_by(ordering)
			#print("firing")
			#print(qs)
		filter_class = self.filter_class
		#print(filter_class)
		#print("fireing") #this is not compatible with django-filter==1.1.0 only compatible with django-filter==0.11.0
		if filter_class: # this is broken  added == None to ensure product list renders; 
			f = filter_class(self.request.GET, queryset=qs)
			context["object_list"] = f.qs
			#print(f)
		return context


def product_create(request):
	if not request.user.is_staff or not request.user.is_admin:
		raise Http404
		
	form = ProductForm(request.POST or None)
	#image_form = ProductImageForm(request.FILES or None)

	if form.is_valid():
		product_instance = form.save(commit=False)
		#instance.user = request.user
		#image_form.product = product_instance
		# try:
		# 	image_instance = image_form.save(commit=False)
		# 	print(image_instance)
		# 	image_form.product = product_instance
		# 	image_instance.save()
		# except:
		# 	print("exception on image...")
		# 	pass
		product_instance.save()
		form.save_m2m()
		# message success
		messages.success(request, "Product Successfully Created!")
		return HttpResponseRedirect(product_instance.get_variation_query_url())
	context = {
		"form": form,
		#"image_form": image_form,
	}
	return render(request, "products/product_form.html", context)


class ProductImageListView(StaffRequiredMixin, ListView):
	# if not request.user.is_staff or not request.user.is_admin:
	# 	raise Http404
	model = ProductImage
	queryset = ProductImage.objects.all()
		
	#form = ProductImageForm(request.POST or None)
	#image_form = ProductImageForm(request.FILES or None)
	#product_instance = get_object_or_404(Product, pk=pk)

	def get_context_data(self, *args, **kwargs):
		context = super(ProductImageListView, self).get_context_data(*args, **kwargs)
		context["formset"] = ProductImageFormSet(queryset=self.get_queryset())
		return context

	def get_queryset(self, *args, **kwargs):
		product_pk = self.kwargs.get("pk")
		if product_pk:
			product = get_object_or_404(Product, pk=product_pk)
			queryset = ProductImage.objects.filter(product=product)
		return queryset

	def post(self, request, *args, **kwargs):
		formset = ProductImageFormSet(request.POST, request.FILES)
		product_pk = self.kwargs.get("pk")
		product_instance = get_object_or_404(Product, pk=product_pk)
		# if formset.is_valid():
		# 	image_instance = form.save(commit=False)
		# 	#instance.user = request.user
		# 	#form.product = product_instance
		# 	# try:
		# 	# 	image_instance = image_form.save(commit=False)
		# 	# 	print(image_instance)
		# 	# 	image_form.product = product_instance
		# 	# 	image_instance.save()
		# 	# except:
		# 	# 	print("exception on image...")
		# 	# 	pass
		# 	image_instance.save()
		# 	#form.save_m2m()
		# 	# message success
		# 	messages.success(request, "Product Default Image Set Successfully!")
		# 	return HttpResponseRedirect(product_instance.get_absolute_url())
		if formset.is_valid():
			formset.save(commit=False)
			for form in formset:
				new_image = form.save(commit=False)
				#if new_item.title:
				product_pk = self.kwargs.get("pk")
				product = get_object_or_404(Product, pk=product_pk)
				new_image.product = product
				new_image.save()
				
			messages.success(request, "Product Default Image Set Successfully!")
			return redirect(product_instance.get_variation_query_url())
		raise Http404
	# context = {
	# 	"form": form,
	# 	#"image_form": image_form,
	# }
	#return render(request, "products/product_form.html", context)



class ProductListView(FilterMixin, ListView):
	model = Product
	queryset = Product.objects.all()
	filter_class = ProductFilter


	def get_context_data(self, *args, **kwargs):
		context = super(ProductListView, self).get_context_data(*args, **kwargs)
		context["now"] = timezone.now()
		context["query"] = self.request.GET.get("q") #None
		context["filter_form"] = ProductFilterForm(data=self.request.GET or None)
		return context

	def get_queryset(self, *args, **kwargs):
		qs = super(ProductListView, self).get_queryset(*args, **kwargs)
		query = self.request.GET.get("q")
		if query:
			qs = self.model.objects.filter(
				Q(title__icontains=query) |
				Q(description__icontains=query)
				)
			try:
				qs2 = self.model.objects.filter(
					Q(price=query)
				)
				qs = (qs | qs2).distinct()
			except:
				pass
		return qs




import random
class ProductDetailView(DetailView):
	model = Product
	#template_name = "product.html"
	#template_name = "<appname>/<modelname>_detail.html"
	def get_context_data(self, *args, **kwargs):
		context = super(ProductDetailView, self).get_context_data(*args, **kwargs)
		# print(self.request.META['QUERY_STRING'])
		initial_selection = self.request.META['QUERY_STRING']
		true_selection = initial_selection.split('=')
		print(true_selection)
		real_selection = true_selection[1]
		print(real_selection)
		instance = self.get_object()
		#order_by("-title")
		var_obj = Variation.objects.filter(slug=real_selection, product=instance)
		print(var_obj)
		context["related"] = sorted(Product.objects.get_related(instance)[:6], key= lambda x: random.random())
		context["initial_selection"] = real_selection
		context["initial_variation"] = var_obj
		return context

class ExpDetailView(DetailView):
	model = Product
	template_name = "products/exp_detail.html"
	#template_name = "<appname>/<modelname>_detail.html"
	def get_context_data(self, *args, **kwargs):
		context = super(ExpDetailView, self).get_context_data(*args, **kwargs)
		#print(self.request.META['QUERY_STRING'])
		initial_selection = self.request.META['QUERY_STRING']
		true_selection = initial_selection.split('=')
		#print(true_selection)
		real_selection = true_selection[1]
		#print(real_selection)
		#print(self.request.META)
		instance = self.get_object()
		#order_by("-title")
		var_qs = Variation.objects.filter(slug=real_selection, product=instance)
		var_obj = var_qs.first()
		print(var_obj)
		context["related"] = sorted(Variation.objects.get_related(var_obj)[:6], key= lambda x: random.random())
		context["initial_selection"] = real_selection
		context["var_obj"] = var_obj
		return context

# def product_detail_view_func(request, id):
# 	#product_instance = Product.objects.get(id=id)
# 	product_instance = get_object_or_404(Product, id=id)
# 	try:
# 		product_instance = Product.objects.get(id=id)
# 	except Product.DoesNotExist:
# 		raise Http404
# 	except:
# 		raise Http404

# 	template = "products/product_detail.html"
# 	context = {	
# 		"object": product_instance
# 	}
# 	return render(request, template, context)

class VariationFilter(FilterSet):
	search = CharFilter(field_name='product__title', lookup_expr='icontains', distinct=True)
	category = CharFilter(field_name='product__categories__title', lookup_expr='icontains', distinct=True)
	category_id = CharFilter(field_name='product__categories__id', lookup_expr='icontains', distinct=True)
	min_price = NumberFilter(field_name='price', lookup_expr='gte', distinct=True) # (some_price__gte=somequery)
	max_price = NumberFilter(field_name='price', lookup_expr='lte', distinct=True)
	size = CharFilter(field_name='size', lookup_expr='exact', distinct=True)
	type = CharFilter(field_name='product__type__id', lookup_expr='icontains', distinct=True)
	availability = CharFilter(field_name='availability', lookup_expr='exact', distinct=True)

	class Meta:
		model = Product
		fields = [
			'min_price',
			'max_price',
			'category',
			'type',
			'availability',
			'title',
			'search',
			'size',
			'description',
		]


class ProductVariationListView(FilterMixin, ListView):
	model = Variation
	queryset = Variation.objects.all()
	filter_class = VariationFilter
	template_name = "products/product_variation_list.html"


	def get_context_data(self, *args, **kwargs):
		context = super(ProductVariationListView, self).get_context_data(*args, **kwargs)
		context["now"] = timezone.now()
		context["query"] = self.request.GET.get("q") #None
		context["filter_form"] = VariationFilterForm(data=self.request.GET or None)
		context["filter-method"] = self.request.GET
		context['filter_url'] = reverse_lazy("products:product-variations-list")
		return context

	def get_queryset(self, *args, **kwargs):
		qs = super(ProductVariationListView, self).get_queryset(*args, **kwargs)
		query = self.request.GET.get("q")
		if query:
			qs = self.model.objects.filter(
				Q(product__title__icontains=query) |
				Q(product__description__icontains=query)
				)
			try:
				qs2 = self.model.objects.filter(
					Q(price=query)
				)
				qs = (qs | qs2).distinct()
			except:
				pass
		return qs


def product_featured_create(request):
	if not request.user.is_staff or not request.user.is_admin:
		raise Http404
		
	form = ProductFeaturedForm(request.POST or None, request.FILES or None)
	#image_form = ProductImageForm(request.FILES or None)

	if form.is_valid():
		product_instance = form.save(commit=False)
		#instance.user = request.user
		#image_form.product = product_instance
		# try:
		# 	image_instance = image_form.save(commit=False)
		# 	print(image_instance)
		# 	image_form.product = product_instance
		# 	image_instance.save()
		# except:
		# 	print("exception on image...")
		# 	pass
		product_instance.save()
		form.save_m2m()
		# message success
		messages.success(request, "Product Featured Successfully Created!")
		return HttpResponseRedirect(product_instance.product.get_variation_query_url())
	context = {
		"form": form,
		#"image_form": image_form,
	}
	return render(request, "products/product_featured_form.html", context)


# class ProductVariationAPIListView(ListView):
# 	model = Variation
# 	queryset = Variation.objects.all()
# 	#filter_class = VariationFilter
# 	template_name = "products/product_variation_list_api.html"


# 	def get_context_data(self, *args, **kwargs):
# 		context = super(ProductVariationListView, self).get_context_data(*args, **kwargs)
# 		# context["now"] = timezone.now()
# 		# context["query"] = self.request.GET.get("q") #None
# 		# context["filter_form"] = VariationFilterForm(data=self.request.GET or None)
# 		# context["filter-method"] = self.request.GET
# 		# context['filter_url'] = reverse_lazy("product-variations-list")
# 		return context

# 	def get_queryset(self, *args, **kwargs):
# 		qs = super(ProductVariationListView, self).get_queryset(*args, **kwargs)
# 		# query = self.request.GET.get("q")
# 		# if query:
# 		# 	qs = self.model.objects.filter(
# 		# 		Q(product__title__icontains=query) |
# 		# 		Q(product__description__icontains=query)
# 		# 		)
# 		# 	try:
# 		# 		qs2 = self.model.objects.filter(
# 		# 			Q(price=query)
# 		# 		)
# 		# 		qs = (qs | qs2).distinct()
# 		# 	except:
# 		# 		pass
# 		return qs


def product_variation_api_list_view(request):
	response = requests.get('http://127.0.0.1:8000/api/products/variations/')
	search = request.GET.get("search", None)
	# query = request.GET.get("q", None)
	if search:
		response = requests.get('http://127.0.0.1:8000/api/products/variations/?search=%s' % search)
	else:
		response = requests.get('http://127.0.0.1:8000/api/products/variations/')
	# print(query)
	# if query:
	# 	response = requests.get('http://127.0.0.1:8000/api/products/variations/?q=%s' % query)
	# else:
	# 	response = requests.get('http://127.0.0.1:8000/api/products/variations/')
	# slug  = request.GET.get('slug', None)
	# if slug is not None:
	# 	print('product variation API fetch by product slug')
	# 	response = requests.get('http://127.0.0.1:8000/api/products/variations/?slug=%s' % slug)
	# category = request.GET.get('category', None)
	# if category is not None:
	# 	# print("getting hit")
	# 	response = requests.get('http://127.0.0.1:8000/api/products/variations/?category=%s' % category)
	variation_data = response.json()
	return render(request, 'products/home.html', {
		'filter_form': VariationFilterForm(data=request.GET or None),
		'filter-method': request.GET,
		'filter_url': reverse_lazy("products-api:variation-list-create"),
		'object_list': variation_data['results'],
		'object_next': variation_data['next'],
		'results_count': variation_data['count'],
		#'country': variation_data['country_name']
	})