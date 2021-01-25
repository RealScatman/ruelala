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

from products.models import Type
from ecommerce2.utils import unique_slug_generator

class GrowlerQuerySet(models.query.QuerySet):
	def active(self):
		return self.filter(active=True)


class GrowlerManager(models.Manager):
	def get_queryset(self):
		return GrowlerQuerySet(self.model, using=self._db)

	def all(self, *args, **kwargs):
		return self.get_queryset().active()


class Growler(models.Model):
	title       = models.CharField(max_length=120)
	slug		= models.SlugField(blank=True, null=True)
	description = models.TextField(blank=True, null=True)
	price       = models.DecimalField(decimal_places=2, max_digits=20)
	abv         = models.DecimalField(decimal_places=1, max_digits=3)
	type        = models.ForeignKey(Type, null=True, blank=True, on_delete=models.CASCADE)
	inventory   = models.IntegerField(null=True, blank=True)
	active      = models.BooleanField(default=True)
	timestamp   = models.DateTimeField(auto_now_add=True)
	updated     = models.DateTimeField(auto_now=True)

	objects = GrowlerManager()

	class Meta:
		ordering = ["-title"]

	def __str__(self): #def __str__(self):
		return self.title 

	# def get_absolute_url(self):
	# 	return reverse("growler_detail", kwargs={"slug": self.slug})

	# def get_image_url(self):
	# 	img = self.growlerimage_set.first()
	# 	if img:
	# 		return img.image.url
	# 	return img #None

def growler_pre_save_receiver(sender, instance, *args, **kwargs):
	if not instance.slug:
		instance.slug = unique_slug_generator(instance)

pre_save.connect(growler_pre_save_receiver, sender=Growler)