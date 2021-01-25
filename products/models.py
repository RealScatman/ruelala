import random
import os
from django.conf import settings
from django.db.models import Q
#from django.core.urlresolvers import reverse
from django.urls import reverse
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.utils.safestring import mark_safe
from django.utils.text import slugify

from ecommerce2.utils import unique_slug_generator

# Create your models here.

def get_filename_ext(filepath):
	base_name = os.path.basename(filepath)
	name, ext = os.path.splitext(base_name)
	return name, ext

def upload_image_path(instance, filename):
	#print(instance)
	#print(filename)
	new_filename = random.randint(1,3910209312)
	name, ext = get_filename_ext(filename)
	final_filename = '{new_filename}{ext}'.format(new_filename=new_filename, ext=ext)
	return "variations/{new_filename}/{final_filename}".format(
			new_filename=new_filename, final_filename=final_filename)

class ProductQuerySet(models.query.QuerySet):
	def active(self):
		return self.filter(active=True)


class ProductManager(models.Manager):
	def get_queryset(self):
		return ProductQuerySet(self.model, using=self._db)

	def all(self, *args, **kwargs):
		return self.get_queryset().active()

	def get_related(self, instance):
		products_one = self.get_queryset().filter(categories__in=instance.categories.all())
		products_two = self.get_queryset().filter(default=instance.default).active()
		qs = (products_one | products_two).exclude(id=instance.id).distinct()
		return qs


class Product(models.Model):
	title 			= models.CharField(max_length=120)
	slug			= models.SlugField(blank=True, null=True)
	description 	= models.TextField(blank=True, null=True)
	price 			= models.DecimalField(decimal_places=2, max_digits=20)
	active 			= models.BooleanField(default=True)
	categories 		= models.ManyToManyField('Category', blank=True)
	default 		= models.ForeignKey('Category', related_name='default_category', null=True, blank=True, on_delete=models.SET_NULL)
	type 			= models.ForeignKey('Type', null=True, blank=True, on_delete=models.SET_NULL)

	objects = ProductManager()

	class Meta:
		ordering = ["-title"]

	def __str__(self): #def __str__(self):
		return self.title 

	# def get_absolute_url(self):
	# 	return reverse("products:product_detail", kwargs={"pk": self.pk})

	def get_absolute_url(self):
		return reverse("products:product_detail", kwargs={"slug": self.slug})

	# def get_variation_query_url(self):
	# 	var_obj = self.variation_set.first()
	# 	return "%s?var_display=%s" %(reverse("products:exp_detail", kwargs={"pk": self.pk}), var_obj.slug)

	def get_variation_query_url(self):
		var_obj = self.variation_set.first()
		return "%s?var_display=%s" %(reverse("products:exp_detail", kwargs={"slug": self.slug}), var_obj.slug)

	def get_image_url(self):
		img = self.productimage_set.first()
		if img:
			return img.image.url
		return img #None

def product_pre_save_receiver(sender, instance, *args, **kwargs):
	if not instance.slug:
		instance.slug = unique_slug_generator(instance)

pre_save.connect(product_pre_save_receiver, sender=Product)

class VariationQuerySet(models.query.QuerySet):
	def active(self):
		return self.filter(active=True)
	
	def featured(self):
		return self.filter(featured=True)


class VariationManager(models.Manager):
	def get_queryset(self):
		return VariationQuerySet(self.model, using=self._db)

	def all(self, *args, **kwargs):
		return self.get_queryset().active()

	def featured(self, *args, **kwargs):
		return self.get_queryset().featured()

	def get_related(self, instance):
		products_one = self.get_queryset().filter(product__categories__in=instance.product.categories.all())
		products_two = self.get_queryset().filter(product__default=instance.product.default).active()
		qs = (products_one | products_two).exclude(product__id=instance.product.id).distinct()
		return qs

class Variation(models.Model):
	product       = models.ForeignKey(Product, on_delete=models.CASCADE)
	title         = models.CharField(max_length=120)
	slug          = models.SlugField(blank=True, null=True)
	price         = models.DecimalField(decimal_places=2, max_digits=20)
	sale_price    = models.DecimalField(decimal_places=2, max_digits=20, null=True, blank=True)
	active        = models.BooleanField(default=True)
	featured      = models.BooleanField(default=False)
	inventory     = models.PositiveIntegerField(null=True, blank=True) #refer none == unlimited amount
	image		  = models.ImageField(upload_to=upload_image_path, null=True, blank=True)
	size          = models.ForeignKey('Size', null=True, blank=True, on_delete=models.SET_NULL)
	availability  = models.ForeignKey('Availability', null=True, blank=True, on_delete=models.SET_NULL)

	objects = VariationManager()

	class Meta:
		ordering = ["product__slug"]

	def __str__(self):
		return self.product.title

	def get_price(self):
		if self.sale_price is not None:
			return self.sale_price
		else:
			return self.price

	def get_html_price(self):
		if self.sale_price is not None:
			html_text = "<span class='sale-price'>%s</span> <span class='og-price'>%s</span>" %(self.sale_price, self.price)
		else:
			html_text = "<span class='price'>%s</span>" %(self.price)
		return mark_safe(html_text)

	def get_absolute_url(self):
		return self.product.get_absolute_url()
	
	# def get_variation_query_url(self):
	# 	return "%s?var_display=%s" %(reverse("exp_detail", kwargs={"pk": self.product.pk}), self.slug)

	def get_variation_query_url(self):
		return "%s?var_display=%s" %(reverse("exp_detail", kwargs={"slug": self.product.slug}), self.slug)

	def add_to_cart(self):
		return "%s?item=%s&qty=1" %(reverse("cart"), self.id)

	def remove_from_cart(self):
		return "%s?item=%s&qty=1&delete=True" %(reverse("cart"), self.id)

	def get_title(self):
		return "%s - %s" %(self.product.title, self.title)

	def get_image_url(self):
		return self.product.get_image_url()

	def get_var_image_url(self):
		img = self.image
		if img:
			#print(img)
			return img.url
		return self.product.get_image_url()

def product_post_saved_receiver(sender, instance, created, *args, **kwargs):
	product = instance
	size_qs = Size.objects.filter(pk=1)
	size_obj = size_qs.first()
	#print(size_obj)
	variations = product.variation_set.all()
	images = product.productimage_set.all()
	if variations.count() == 0:
		new_var = Variation()
		new_var.product = product
		new_var.title = "Default"
		new_var.price = product.price
		new_var.inventory = 5
		new_var.size = size_obj
		new_var.save()
	if images.count() == 0:
		new_image = ProductImage()
		new_image.product = product
		#new_image.image = 'somedefault image from static...'
		new_image.save()

post_save.connect(product_post_saved_receiver, sender=Product)

def variation_pre_save_receiver(sender, instance, *args, **kwargs):
	if not instance.slug:
		instance.slug = unique_slug_generator(instance)

pre_save.connect(variation_pre_save_receiver, sender=Variation)

def image_upload_to(instance, filename):
	title = instance.product.title
	slug = slugify(title)
	basename, file_extension = filename.split(".")
	new_filename = "%s-%s.%s" %(slug, instance.id, file_extension)
	return "products/%s/%s" %(slug, new_filename)

class ProductImage(models.Model):
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	image = models.ImageField(upload_to=image_upload_to, default='AmblerBeverage.jpg')

	def __str__(self):
		return self.product.title

class CategoryQuerySet(models.query.QuerySet):
	def active(self):
		return self.filter(active=True)

class CategoryManager(models.Manager):
	def get_queryset(self):
		return CategoryQuerySet(self.model, using=self._db)

	def all(self, *args, **kwargs):
		return self.get_queryset().active()

class Category(models.Model):
	title 		= models.CharField(max_length=120, unique=True)
	slug 		= models.SlugField(unique=True)
	description = models.TextField(null=True, blank=True)
	active 		= models.BooleanField(default=True)
	timestamp 	= models.DateTimeField(auto_now_add=True, auto_now=False)

	objects = CategoryManager()

	class Meta:
		ordering = ["-title"]

	def __str__(self):
		return self.title

	def get_absolute_url(self):
		return reverse("categories:category_detail", kwargs={"slug": self.slug })

def category_pre_save_receiver(sender, instance, *args, **kwargs):
	if not instance.slug:
		instance.slug = unique_slug_generator(instance)

pre_save.connect(category_pre_save_receiver, sender=Category)

def image_upload_to_featured(instance, filename):
	title = instance.product.title
	slug = slugify(title)
	basename, file_extension = filename.split(".")
	new_filename = "%s-%s.%s" %(slug, instance.id, file_extension)
	return "products/%s/featured/%s" %(slug, new_filename)

class ProductFeatured(models.Model):
	product 		= models.ForeignKey(Product, on_delete=models.CASCADE)
	image 			= models.ImageField(upload_to=image_upload_to_featured)
	title 			= models.CharField(max_length=120, null=True, blank=True)
	text 			= models.CharField(max_length=220, null=True, blank=True)
	text_right 		= models.BooleanField(default=False)
	text_css_color 	= models.CharField(max_length=6, null=True, blank=True)
	text_css_shadow_color = models.CharField(max_length=6, null=True, blank=True)
	show_price 		= models.BooleanField(default=False)
	make_image_background = models.BooleanField(default=False)
	active			 = models.BooleanField(default=True)

	def __str__(self):
		return self.product.title

class Size(models.Model):
	title = models.CharField(max_length=120, unique=True)
	slug = models.SlugField(unique=True)
	description = models.TextField(null=True, blank=True)
	active = models.BooleanField(default=True)
	timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)

	def __str__(self):
		return self.title

def size_pre_save_receiver(sender, instance, *args, **kwargs):
	if not instance.slug:
		instance.slug = unique_slug_generator(instance)

pre_save.connect(size_pre_save_receiver, sender=Size)

class Availability(models.Model):
	title = models.CharField(max_length=120, unique=True)
	slug = models.SlugField(unique=True)
	description = models.TextField(null=True, blank=True)
	active = models.BooleanField(default=True)
	timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)

	def __str__(self):
		return self.slug

	# def get_absolute_url(self):
	# 	return reverse("category_detail", kwargs={"slug": self.slug })

def availability_pre_save_receiver(sender, instance, *args, **kwargs):
	if not instance.slug:
		instance.slug = unique_slug_generator(instance)

pre_save.connect(availability_pre_save_receiver, sender=Availability)

class Type(models.Model):
	title = models.CharField(max_length=120, unique=True)
	slug = models.SlugField(blank=True, null=True)
	description = models.TextField(null=True, blank=True)
	active = models.BooleanField(default=True)
	timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)

	def __str__(self):
		return self.title

def type_pre_save_receiver(sender, instance, *args, **kwargs):
	if not instance.slug:
		instance.slug = unique_slug_generator(instance)

pre_save.connect(type_pre_save_receiver, sender=Type)