import operator
import csv

from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save, pre_save

from ecommerce2.utils import delivery_slug_generator

# Create your models here.

class ZipCodeImport(models.Model):
    imported					= models.BooleanField(default=False)
    timestamp					= models.DateTimeField(auto_now_add=True)
    updated						= models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.imported)

def zipcode_import_create_receiver(sender, instance, created, *args, **kwargs):
    if created:

        file_path = 'delivery/data/short_zip_list.csv' # switch to bigger file when rdy

        with open(file_path,  encoding = "ISO-8859-1") as f:
            reader = csv.reader(f)
            next(reader, None)

            for row in reader:
                _, created = ZipCode.objects.get_or_create(
                    zipcode=row[0],
                    latitude=row[1],
                    longitude=row[2]
                    )

post_save.connect(zipcode_import_create_receiver, sender=ZipCodeImport)


class DeliveryZipCodeQuerySet(models.query.QuerySet):
    def active(self):
        return self.filter(active=True)

class DeliveryZipCodeManager(models.Manager):
    def get_queryset(self):
        return DeliveryZipCodeQuerySet(self.model, using=self._db)

    def all(self, *args, **kwargs):
        return self.get_queryset().active()

    def zipcode_exists(self, zipcode):
        return self.get_queryset().filter(Q(zipcodes__zipcode=zipcode)).filter(active=True)

# 	def get_related(self, instance):
# 		products_one = self.get_queryset().filter(categories__in=instance.categories.all())
# 		products_two = self.get_queryset().filter(default=instance.default).active()
# 		qs = (products_one | products_two).exclude(id=instance.id).distinct()
# 		return qs


class DeliveryZipCode(models.Model):
    delivery_day  = models.CharField(max_length=120)
    slug		  = models.SlugField(blank=True, null=True)
    zipcodes      = models.ManyToManyField('ZipCode', blank=True)
    active        = models.BooleanField(default=True)
    timestamp	  = models.DateTimeField(auto_now_add=True)

    objects = DeliveryZipCodeManager()

    class Meta:
        ordering = ["delivery_day"]

    def __str__(self):
        return self.delivery_day 

def deliveryzipcode_pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = delivery_slug_generator(instance)

pre_save.connect(deliveryzipcode_pre_save_receiver, sender=DeliveryZipCode)


class ZipCode(models.Model):
    zipcode       = models.CharField(max_length=120)
    latitude      = models.CharField(max_length=120)
    longitude     = models.CharField(max_length=120)
    active        = models.BooleanField(default=True)
    timestamp	  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-zipcode"]

    def __str__(self):
        return self.zipcode 