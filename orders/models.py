import math
import datetime
import braintree

from decimal import Decimal
from django.conf import settings
#from django.core.urlresolvers import reverse
from django.urls import reverse
from django.utils import timezone
from django.db import models
from django.db.models import Count, Sum, Avg
from django.db.models.signals import pre_save, post_save

from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.mail import send_mail
from django.template.loader import get_template

# Create your models here.
from addresses.models import Address, DeliveryFrequency
from carts.models import Cart
from accounts.models import BoxSelection, Subscription
from billing.models import BillingProfile
from ecommerce2.utils import unique_order_id_generator

#if settings.DEBUG:
gateway = braintree.BraintreeGateway(
	braintree.Configuration(
		braintree.Environment.Sandbox,
		merchant_id=settings.BRAINTREE_MERCHANT_ID,
		public_key=settings.BRAINTREE_PUBLIC,
		private_key=settings.BRAINTREE_PRIVATE,
		timeout=20
	)
)

class UserCheckoutManager(models.Manager):
	def new_or_get(self, request):
		user = request.user
		#guest_email_id = request.session.get('guest_email_id')
		#register_email_id = request.session.get('register_email_id')
		user_checkout_id = request.session.get("user_checkout_id")
		created = False
		obj = None
		if user.is_authenticated:
			'logged in user checkout; remember payment stuff'
			obj, created = self.model.objects.get_or_create(user=user, email=user.email)
		# elif guest_email_id is not None:
		# 	'guest user checkout; auto reloads payment stuff'
		# 	guest_email_obj = GuestEmail.objects.get(id=guest_email_id)
		# 	obj, created = self.model.objects.get_or_create(email=guest_email_obj.email)

		# elif register_email_id is not None:
		# 	register_email_obj = RealUser.objects.get(id=register_email_id)
		# 	obj, created = self.model.objects.get_or_create(email=register_email_obj.email)
		elif user_checkout_id is not None:
			#user_check_id = self.request.session.get("user_checkout_id")
			user_checkout_obj = UserCheckout.objects.get(id=user_checkout_id)
			obj, created = self.model.objects.get_or_create(email=user_checkout_obj.email)
		else:
			pass
		return obj, created

class UserCheckout(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL) #not required
	email = models.EmailField(unique=True) #--> required
	braintree_id = models.CharField(max_length=120, null=True, blank=True)

	objects = UserCheckoutManager()

	def __str__(self): #def __str__(self):
		return self.email

	@property
	def get_braintree_id(self):
		instance = self
		#print("getting hit from checkout login..")
		if not instance.braintree_id:
			#result = braintree.Customer.create({
			result = gateway.customer.create({
				"email": instance.email,
			})
			if result.is_success:
				print("new braintree_id being created.")
				instance.braintree_id = result.customer.id
				print(result)
				instance.save()
		return instance.braintree_id

	def get_client_token(self):
		customer_id = self.get_braintree_id
		if customer_id:
			client_token = gateway.client_token.generate({
				"customer_id": customer_id
			})
			#print(client_token)
			#print("client token available.")
			return client_token
		return None

	def staff_get_absolute_url(self):
		return reverse("staff-customer-detail", kwargs={'pk': self.pk})

def update_braintree_id(sender, instance, *args, **kwargs):
	if not instance.braintree_id:
		instance.get_braintree_id

post_save.connect(update_braintree_id, sender=UserCheckout)

class UserCheckin(models.Model):
	user_checkout        = models.ForeignKey(UserCheckout, on_delete=models.CASCADE)
	active               = models.BooleanField(default=False)
	order_id             = models.CharField(max_length=20, null=True, blank=True)
	parking_slot		 = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])	
	timestamp	         = models.DateTimeField(auto_now_add=True)
	updated				 = models.DateTimeField(auto_now=True)

	def __str__(self):
		return str(self.user_checkout)

ADDRESS_TYPE = (
	('billing', 'Billing'),
	('shipping', 'Shipping'),
)

class UserAddress(models.Model):
	user = models.ForeignKey(UserCheckout, on_delete=models.CASCADE)
	type = models.CharField(max_length=120, choices=ADDRESS_TYPE)
	street = models.CharField(max_length=120)
	city = models.CharField(max_length=120)
	state = models.CharField(max_length=120)
	zipcode = models.CharField(max_length=120)

	def __str__(self):
		return self.street

	def get_address(self):
		return "%s, %s, %s %s" %(self.street, self.city, self.state, self.zipcode)

ORDER_STATUS_CHOICES = (
	('created', 'Created'),
	('paid', 'Paid'),
	('ready', 'Ready'),
	('shipped', 'Shipped'),
	('picked-up', 'Picked Up'),
	('checked-in', 'Checked In'),
	('refunded', 'Refunded'),
)

class OrderManagerQuerySet(models.query.QuerySet):
	def recent(self):
		#return self.order_by("-updated","-timestamp")
		return self.order_by('-timestamp')

	def by_request(self, request):
		user_checkout, created = UserCheckout.objects.new_or_get(request)
		return self.filter(user=user_checkout)

	def get_sales_breakdown(self):
		recent = self.recent().not_refunded()
		recent_data = recent.totals_data()
		recent_cart_data = recent.cart_data()

		shipped = recent.not_refunded().by_status(status='shipped')
		shipped_data = shipped.totals_data()

		paid = recent.by_status(status='paid')
		paid_data = paid.totals_data()
		data = {
			'recent': recent,
			'recent_data': recent_data,
			'recent_cart_data': recent_cart_data,
			'shipped': shipped,
			'shipped_data': shipped_data,
			'paid': paid,
			'paid_data': paid_data
		}
		return data

	def by_weeks_range(self, weeks_ago=7, number_of_weeks=2):
		if number_of_weeks > weeks_ago:
			number_of_weeks = weeks_ago
		days_ago_start = weeks_ago * 7 # days_ago_start = 49
		days_ago_end = days_ago_start - (number_of_weeks * 7) # days_ago_end = 49 - 14 = 35
		start_date = timezone.now() - datetime.timedelta(days=days_ago_start)
		end_date = timezone.now() - datetime.timedelta(days=days_ago_end)
		return self.by_range(start_date, end_date=end_date)

	def by_range(self, start_date, end_date=None):
		if end_date is None:
			return self.filter(updated__gte=start_date)
		return self.filter(updated__gte=start_date).filter(updated__lte=end_date)

	def by_date(self):
		now = timezone.now() - datetime.timedelta(days=13)
		return self.filter(updated__day__gte=now.day)

	def totals_data(self):
		return self.aggregate(
				Sum("order_total"),
				Avg("order_total")
			)

	def cart_data(self):
		return self.aggregate(
			Sum("cart__items__price"),
			Avg("cart__items__price"),
			Count("cart__items")
			)

	def by_status(self, status="shipped"):
		return self.filter(status=status)

	def not_refunded(self):
		return self.exclude(status='refunded')

	def not_created(self):
		return self.exclude(status='created')

class OrderManager(models.Manager):
	def get_queryset(self):
		return OrderManagerQuerySet(self.model, using=self._db)

	def by_request(self, request):
		return self.get_queryset().by_request(request)

class Order(models.Model):
	status               = models.CharField(max_length=120, choices=ORDER_STATUS_CHOICES, default='created')
	cart                 = models.ForeignKey(Cart, on_delete=models.CASCADE)
	user                 = models.ForeignKey(UserCheckout, null=True, on_delete=models.SET_NULL)
	user_checkin         = models.ForeignKey(UserCheckin, related_name='user_checkin', null=True, blank=True, on_delete=models.SET_NULL)
	billing_address      = models.ForeignKey(UserAddress, related_name='billing_address', null=True, on_delete=models.SET_NULL)
	shipping_address     = models.ForeignKey(UserAddress, related_name='shipping_address', null=True, on_delete=models.SET_NULL)
	shipping_total_price = models.DecimalField(max_digits=50, decimal_places=2, default=0.00)
	order_total          = models.DecimalField(max_digits=50, decimal_places=2, )
	order_id             = models.CharField(max_length=20, null=True, blank=True)
	timestamp	         = models.DateTimeField(auto_now_add=True)
	updated				 = models.DateTimeField(auto_now=True)

	objects = OrderManager()

	def __str__(self):
		return str(self.cart.id)

	class Meta:
		ordering = ['-id']

	def get_absolute_url(self):
		return reverse("order_detail", kwargs={"pk": self.pk})

	def staff_get_absolute_url(self):   # New Code Experiment
		return reverse("staff-order-detail", kwargs={'pk': self.pk})

	def mark_completed(self, order_id=None):
		self.status = "paid"
		if order_id and not self.order_id:
			self.order_id = order_id
		self.save()

	def get_status(self):
		if self.status =="refunded":
			return "Refunded Order"
		elif self.status == "shipped":
			return "Shipped"
		elif self.status == "paid":
			return "Paid"
		return "Shipping Soon"

	def staff_get_status(self):
		if self.status =="refunded":
			return "Refunded Order"
		elif self.status == "shipped":
			return "Shipped"
		elif self.status =="paid":
			return "Paid, Awaiting Customer Pickup"
		return self.status

	def is_ready(self):
		if self.status =="ready":
			return True
		return False

	def is_checkedin(self):
		if self.status =="checked-in":
			return True
		return False
	
	def update_cartitems(self):
		cart_items = self.cart.cartitem_set.all()
		print(cart_items)
		for cart_item in cart_items:
			cart_item.item.inventory -= int(cart_item.quantity)
			print(cart_item.item.inventory)
			cart_item.item.save()
		#return True

	def pickup_date(self):
		cart_time_obj = self.cart.carttime_set.first()
		#return cart_time_obj
		return cart_time_obj.pickup_time.pickup_date

	def pickup_time_slot(self):
		cart_time_obj = self.cart.carttime_set.first()
		#return cart_time_obj
		return cart_time_obj.pickup_time.timeslot

	def checkin_slot(self):
		checkin_obj = self.user_checkin
		#return cart_time_obj
		return checkin_obj.parking_slot

	def send_order_id(self):
		bp_email = self.user.email
		user_name = self.cart.user.full_name
		billing_address_street = self.billing_address.street
		billing_address_city = self.billing_address.city
		billing_address_state = self.billing_address.state
		billing_address_zipcode = self.billing_address.zipcode
		order_total = self.order_total
		cart_items = self.cart.cartitem_set.all
		order_tax = self.cart.tax_total
		pickup_time = self.pickup_time_slot

		if self.order_id:
			base_url = getattr(settings, 'BASE_URL', 'https://www.beaker.life/')
			key_path = reverse("order_detail", kwargs={'pk':self.pk}) # use reverse
			path = "{base}{path}".format(base=base_url, path=key_path)
			if self.status == 'paid':
				context = {
					'path': path,
					'order': self.order_id,
					'email': bp_email,
					'user_name': user_name,
					'pickup_time': pickup_time,
					'billing_address_street': billing_address_street,
					'billing_address_city': billing_address_city,
					'billing_address_state': billing_address_state,
					'billing_address_zipcode': billing_address_zipcode,
					'order_total': order_total,
					'invoice_time': datetime.date.today(),
					'order_tax': order_tax,
					'cart_items': cart_items,
				}
				txt_ = get_template("orders/emails/order.txt").render(context)
				html_ = get_template("orders/emails/order.html").render(context)
				subject = 'Recent Order Receipt'
				from_email = settings.DEFAULT_FROM_EMAIL
				recipient_list = [bp_email, from_email]
				sent_mail = send_mail(
							subject,
							txt_,
							from_email,
							recipient_list,
							html_message=html_,
							fail_silently=False,
					)
				return sent_mail
		return False

	def send_ready_email(self):
		bp_email = self.user.email
		user_name = self.cart.user.full_name
		billing_address_street = self.billing_address.street
		billing_address_city = self.billing_address.city
		billing_address_state = self.billing_address.state
		billing_address_zipcode = self.billing_address.zipcode
		order_total = self.order_total
		cart_items = self.cart.cartitem_set.all
		order_tax = self.cart.tax_total
		pickup_time = self.pickup_time_slot

		if self.order_id:
			base_url = getattr(settings, 'BASE_URL', 'https://www.beaker.life/')
			key_path = reverse("order_detail", kwargs={'pk':self.pk}) # use reverse
			path = "{base}{path}".format(base=base_url, path=key_path)
			context = {
				'path': path,
				'order': self.order_id,
				'email': bp_email,
				'user_name': user_name,
				'pickup_time': pickup_time,
				'billing_address_street': billing_address_street,
				'billing_address_city': billing_address_city,
				'billing_address_state': billing_address_state,
				'billing_address_zipcode': billing_address_zipcode,
				'order_total': order_total,
				'invoice_time': datetime.date.today(),
				'order_tax': order_tax,
				'cart_items': cart_items,
			}
			txt_ = get_template("orders/emails/ready.txt").render(context)
			html_ = get_template("orders/emails/ready.html").render(context)
			subject = 'Your Order is Ready for Pickup!'
			from_email = settings.DEFAULT_FROM_EMAIL
			recipient_list = [bp_email, from_email]
			sent_mail = send_mail(
						subject,
						txt_,
						from_email,
						recipient_list,
						html_message=html_,
						fail_silently=False,
				)
			return sent_mail
		return False

	def send_checkedin_email(self):
		bp_email = self.user.email
		user_name = self.cart.user.full_name
		billing_address_street = self.billing_address.street
		billing_address_city = self.billing_address.city
		billing_address_state = self.billing_address.state
		billing_address_zipcode = self.billing_address.zipcode
		order_total = self.order_total
		cart_items = self.cart.cartitem_set.all
		order_tax = self.cart.tax_total
		pickup_time = self.pickup_time_slot
		checkin_slot = self.checkin_slot()

		if self.order_id:
			base_url = getattr(settings, 'BASE_URL', 'https://www.beaker.life/')
			key_path = reverse("order_detail", kwargs={'pk':self.pk}) # use reverse
			path = "{base}{path}".format(base=base_url, path=key_path)
			context = {
				'path': path,
				'order': self.order_id,
				'email': bp_email,
				'user_name': user_name,
				'pickup_time': pickup_time,
				'billing_address_street': billing_address_street,
				'billing_address_city': billing_address_city,
				'billing_address_state': billing_address_state,
				'billing_address_zipcode': billing_address_zipcode,
				'order_total': order_total,
				'invoice_time': datetime.date.today(),
				'order_tax': order_tax,
				'cart_items': cart_items,
				'checkin_slot': checkin_slot,
			}
			txt_ = get_template("orders/emails/checked_in.txt").render(context)
			html_ = get_template("orders/emails/checked_in.html").render(context)
			subject = "Order #{order_id} has Checked into slot {checkin_slot}".format(order_id=self.order_id, checkin_slot=checkin_slot)
			from_email = settings.DEFAULT_FROM_EMAIL
			recipient_list = [from_email]
			sent_mail = send_mail(
						subject,
						txt_,
						from_email,
						recipient_list,
						html_message=html_,
						fail_silently=False,
				)
			return sent_mail
		return False


def order_pre_save(sender, instance, *args, **kwargs):
	shipping_total_price = instance.shipping_total_price
	cart_total = instance.cart.total
	order_total = Decimal(shipping_total_price) + Decimal(cart_total)
	instance.order_total = order_total

pre_save.connect(order_pre_save, sender=Order)

# def post_save_order(sender, instance, created, *args, **kwargs):
# 	#print("running")
# 	if not created and instance.is_ready():
# 		print("Updating...notify email tigger on update...")
# 		instance.send_ready_email()

# post_save.connect(post_save_order, sender=Order)

def post_save_checkin_order(sender, instance, created, *args, **kwargs):
	#print("running")
	if not created and instance.is_checkedin():
		print("Notifying Business user is outside and checked in...")
		instance.send_checkedin_email()

post_save.connect(post_save_checkin_order, sender=Order)

#### BrainTree Orders above
#### Stripe Orders below for subscriptions


STRIPE_ORDER_STATUS_CHOICES = (
	('created', 'Created'),
	('paid', 'Paid'),
	('shipped', 'Shipped'),
	('refunded', 'Refunded'),
)

# Create your models here.

class StripeOrderManagerQuerySet(models.query.QuerySet):
	def recent(self):
		#return self.order_by("-updated","-timestamp")
		return self.order_by('-timestamp')

	def box_data(self):
		return self.aggregate(
			Sum("box__subscription__price"),
			Avg("box__subscription__price"),
			Count("box__subscription")
			)

	def by_status(self, status="shipped"):
		return self.filter(status=status)

	def not_refunded(self):
		return self.exclude(status='refunded')

	def by_request(self, request):
		billing_profile, created = BillingProfile.objects.new_or_get(request)
		return self.filter(billing_profile=billing_profile)

	def not_created(self):
		return self.exclude(status='created')


class StripeOrderManager(models.Manager):
	def get_queryset(self):
		return StripeOrderManagerQuerySet(self.model, using=self._db)

	def by_request(self, request):
		return self.get_queryset().by_request(request)

	def new_or_get(self, billing_profile, box_obj):
		created = False
		qs = self.get_queryset().filter(
			billing_profile=billing_profile, 
			box=box_obj, 
			active=True, 
			status='created'
			)
		if qs.count() == 1:
			obj = qs.first()
		else:
			obj = self.model.objects.create(billing_profile=billing_profile, box=box_obj)
			created = True
		return obj, created



# Random, Unique - Order Number
class StripeOrder(models.Model):
	billing_profile 	= models.ForeignKey(BillingProfile, null=True, blank=True, on_delete=models.CASCADE)
	order_id 			= models.CharField(max_length=120, blank=True) # AB31DE3
	shipping_address 	= models.ForeignKey(Address, related_name= "shipping_address", null=True, blank=True, on_delete=models.CASCADE)
	billing_address		= models.ForeignKey(Address, related_name= "billing_address", null=True, blank=True, on_delete=models.CASCADE)
	delivery_frequency  = models.ForeignKey(DeliveryFrequency, related_name= "order_delivery_frequency", null=True, blank=True, on_delete=models.CASCADE) #new to add delivery_start_date to order
	box 				= models.ForeignKey(BoxSelection, on_delete=models.CASCADE)
	status 				= models.CharField(max_length=120, default='created', choices=ORDER_STATUS_CHOICES)
	shipping_total 		= models.DecimalField(default=0.00, max_digits=100, decimal_places=2)
	total 				= models.DecimalField(default=0.00, max_digits=100, decimal_places=2)
	active				= models.BooleanField(default=True)
	updated				= models.DateTimeField(auto_now=True)
	timestamp			= models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.order_id

	objects = StripeOrderManager()

	class Meta:
		ordering = ['-timestamp', '-updated']

	def get_absolute_url(self):
		return reverse("stripe-orders:stripe-detail", kwargs={'order_id': self.order_id})

	def staff_get_absolute_url(self):   # New Code Experiment
		return reverse("stripe-orders:staff-stripe-detail", kwargs={'order_id': self.order_id})

	def get_status(self):
		if self.status =="refunded":
			return "Refunded Order"
		elif self.status == "shipped":
			return "Shipped"
		return "Shipping Soon"

	def staff_get_status(self):
		if self.status =="refunded":
			return "Refunded Order"
		elif self.status == "shipped":
			return "Shipped"
		elif self.status =="paid":
			return "Paid, Awaiting Shipping from Beaker Life"
		return self.status

	def update_total(self):
		box_total = self.box.total
		shipping_total = self.shipping_total
		new_total = math.fsum([box_total, shipping_total])
		formatted_total = format(new_total, '.2f')
		self.total = formatted_total
		self.save()
		return new_total

	def check_done(self):
		shipping_address_required = False
		shipping_done = False

		if shipping_address_required and self.shipping_address:
			shipping_done = True
		elif shipping_address_required and not self.shipping_address:
			print("triggered check done...")
			shipping_done = False
		else:
			shipping_done = True


		billing_profile = self.billing_profile
		# shipping_address = self.shipping_address
		billing_address = self.billing_address
		total = self.total
		if billing_profile and shipping_done and billing_address and total > 0:
			return True
		return False

	# def update_purchases(self):
	# 	for p in self.box.subscription.all():
	# 		obj, created = ProductPurchase.objects.get_or_create(
	# 				order_id=self.order_id,
	# 				product=p,
	# 				billing_profile=self.billing_profile,
	# 			)
	# 	return ProductPurchase.objects.filter(order_id=self.order_id).count()

	def mark_paid(self):
		if self.status != 'paid':
			if self.check_done():
				self.status = "paid"
				self.save()
				#self.update_purchases()

		return self.status

	# def send_order_id(self):
	# 	bp_email = self.billing_profile.email
	# 	if self.order_id:
	# 		if self.status == 'paid':
	# 			context = {
	# 				'order': self.order_id,
	# 				'email': bp_email,
	# 			}
	# 			txt_ = get_template("orders/emails/order.txt").render(context)
	# 			html_ = get_template("orders/emails/order.html").render(context)
	# 			subject = 'Recent Order Receipt'
	# 			from_email = settings.DEFAULT_FROM_EMAIL
	# 			recipient_list = [bp_email]
	# 			sent_mail = send_mail(
	# 						subject,
	# 						txt_,
	# 						from_email,
	# 						recipient_list,
	# 						html_message=html_,
	# 						fail_silently=False,
	# 				)
	# 			return sent_mail
	# 	return False



def pre_save_create_stripeorder_id(sender, instance, *args, **kwargs):
	if not instance.order_id:
		instance.order_id = unique_order_id_generator(instance)
	qs = StripeOrder.objects.filter(box=instance.box).exclude(billing_profile=instance.billing_profile)
	if qs.exists():
		qs.update(active=False)

pre_save.connect(pre_save_create_stripeorder_id, sender=StripeOrder)


def post_save_box_total(sender, instance, created, *args, **kwargs):
	if not created:
		box_obj = instance
		box_total = box_obj.total
		box_id = box_obj.id
		qs = StripeOrder.objects.filter(box__id=box_id)
		if qs.count() == 1:
			order_obj = qs.first()
			order_obj.update_total()

post_save.connect(post_save_box_total, sender=BoxSelection)


def post_save_stripeorder(sender, instance, created, *args, **kwargs):
	#print("running")
	if created:
		#print("Updating... first")
		instance.update_total()

post_save.connect(post_save_stripeorder, sender=StripeOrder)


class SubscriptionPurchaseQuerySet(models.query.QuerySet):
	def active(self):
		return self.filter(refunded=False)

	# def digital(self):
	# 	return self.filter(product__is_digital=True)

	def by_request(self, request):
		billing_profile, created = BillingProfile.objects.new_or_get(request)
		return self.filter(billing_profile=billing_profile)

class SubscriptionPurchaseManager(models.Manager):
	def get_queryset(self):
		return SubscriptionPurchaseQuerySet(self.model, using=self._db)

	def all(self):
		return self.get_queryset().active()

	# def digital(self):
	# 	return self.get_queryset().active().digital()

	def by_request(self, request):
		return self.get_queryset().by_request(request)

	# def products_by_request(self, request):
	# 	qs = self.by_request(request).digital()  # add .digital() to the queryset to filter onlydigital products in the view...
	# 	ids_ = [x.product.id for x in qs]
	# 	products_qs = Product.objects.filter(id__in=ids_).distinct()
	# 	return products_qs


class SubscriptionPurchase(models.Model):
	order_id 			= models.CharField(max_length=120)
	billing_profile 	= models.ForeignKey(BillingProfile, on_delete=models.CASCADE) # billingprofile.productpurchase_set.all()
	subscription 	    = models.ForeignKey(Subscription, on_delete=models.CASCADE) # product.productpurchase_set.count()
	refunded 			= models.BooleanField(default=False)
	updated				= models.DateTimeField(auto_now=True)
	timestamp 			= models.DateTimeField(auto_now_add=True)

	objects = SubscriptionPurchaseManager()

	def __str__(self):
		return self.subscription.title