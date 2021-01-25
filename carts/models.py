import datetime
from decimal import Decimal
from django.conf import settings
#from django.core.urlresolvers import reverse
from django.urls import reverse
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save, post_save, post_delete
from django.utils import timezone

from products.models import Variation
# Create your models here.

class CartItem(models.Model):
	cart = models.ForeignKey("Cart", on_delete=models.CASCADE)
	item = models.ForeignKey(Variation, on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField(default=1)
	line_item_total = models.DecimalField(max_digits=10, decimal_places=2)

	def __str__(self):
		return self.item.title

	def remove(self):
		return self.item.remove_from_cart()

def cart_item_pre_save_receiver(sender, instance, *args, **kwargs):
	qty = int(instance.quantity)
	if qty >= 1:
		price = instance.item.get_price()
		line_item_total = Decimal(qty) * Decimal(price)
		instance.line_item_total = line_item_total

pre_save.connect(cart_item_pre_save_receiver, sender=CartItem)

def cart_item_post_save_receiver(sender, instance, *args, **kwargs):
	instance.cart.update_subtotal()

post_save.connect(cart_item_post_save_receiver, sender=CartItem)
post_delete.connect(cart_item_post_save_receiver, sender=CartItem)

class Cart(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
	items = models.ManyToManyField(Variation, through=CartItem)
	#pickup_time = models.ForeignKey("PickupTime", through="CartTime")
	timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
	updated = models.DateTimeField(auto_now_add=False, auto_now=True)
	subtotal = models.DecimalField(max_digits=50, decimal_places=2, default=25.00)
	tax_percentage  = models.DecimalField(max_digits=10, decimal_places=5, default=0.085)
	tax_total = models.DecimalField(max_digits=50, decimal_places=2, default=25.00)
	total = models.DecimalField(max_digits=50, decimal_places=2, default=25.00)
	# discounts
	# shipping

	def __str__(self):
		return str(self.id)

	def update_subtotal(self):
		print("updating...")
		subtotal = 0
		items = self.cartitem_set.all()
		for item in items:
			subtotal += item.line_item_total
		self.subtotal = "%.2f" %(subtotal)
		self.save()

	@property
	def is_delivery(self):
		qs = self.items.all() # every product
		new_qs = qs.filter(availability=2) # all products excluding delivery tagged product variation items
		if new_qs.exists():
			return False
		return True




def do_tax_and_total_receiver(sender, instance, *args, **kwargs):
	subtotal = Decimal(instance.subtotal)
	tax_total = round(subtotal * Decimal(instance.tax_percentage), 2) #8.5%
	#print(instance.tax_percentage)
	total = round(subtotal + Decimal(tax_total), 2)
	instance.tax_total = "%.2f" %(tax_total)
	instance.total = "%.2f" %(total)
	#instance.save()



pre_save.connect(do_tax_and_total_receiver, sender=Cart)

class PickupTime(models.Model):
	#user        = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
	pickup_date = models.DateField(blank=True)
	timeslot    = models.TimeField(blank=True)
	available   = models.BooleanField(default=True)
	count       = models.IntegerField(default=0)

	class Meta:
		ordering = ['-pickup_date','timeslot']

	def __str__(self):
		#return str(self.id)
		return "{}-{}".format(self.pickup_date, self.timeslot)

class CartTimeQuerySet(models.query.QuerySet):
	def active(self):
		return self.filter(active=True)

class CartTimeManager(models.Manager):
	def get_queryset(self, *args, **kwargs):
		return CartTimeQuerySet(self.model, using=self._db)

	def carttime_exists(self, cart):
		return self.get_queryset().filter(Q(cart=cart)).filter(active=True)

	def new_or_get(self, cart, active):
		cart = cart
		active = active
		# guest_email_id = request.session.get('guest_email_id')
		# register_email_id = request.session.get('register_email_id')
		today = timezone.now().date()
		now = timezone.localtime().time()
		pickup_time_qs = PickupTime.objects.filter(pickup_date=today, timeslot__gte=now)
		pickup_time_obj = pickup_time_qs.first()
		created = False
		obj = None
		print("cart time new or get...")
		if cart is not None:
			'cart is created and now a new cart pickup time is attached to the cart (first available)'
			print("triggered carttime_obj creation...")
			obj, created = self.model.objects.get_or_create(cart=cart, pickup_time=pickup_time_obj, active=active)
			pickup_time_obj.count += 1
			pickup_time_obj.save()
		# elif guest_email_id is not None:
		# 	'guest user checkout; auto reloads payment stuff'
		# 	guest_email_obj = GuestEmail.objects.get(id=guest_email_id)
		# 	obj, created = self.model.objects.get_or_create(email=guest_email_obj.email)	
		else:
			pass
		return obj, created


class CartTime(models.Model):
	cart = models.ForeignKey("Cart", null=True, blank=True, on_delete=models.SET_NULL)
	pickup_time = models.ForeignKey("PickupTime", on_delete=models.CASCADE)
	active = models.BooleanField(default=True)
	timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
	updated = models.DateTimeField(auto_now_add=False, auto_now=True)

	objects = CartTimeManager()

	class Meta:
		ordering = ['-updated']

	def __str__(self):
		return str(self.pickup_time.pickup_date)

	# def remove(self):
	# 	return self.pickup_time.remove_from_cart()