import datetime
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save, pre_save
# from django.core.urlresolvers import reverse
from django.urls import reverse
#from io import BytesIO
#from django.core.files import File
#from .utils import render_to_pdf

from accounts.models import GuestEmail, User as RealUser
User = settings.AUTH_USER_MODEL
# Create your models here.

import stripe
STRIPE_SECRET_KEY = getattr(settings, "STRIPE_SECRET_KEY", "XXX")
stripe.api_key = STRIPE_SECRET_KEY


class BillingProfileManager(models.Manager):
	def new_or_get(self, request):
		user = request.user
		guest_email_id = request.session.get('guest_email_id')
		register_email_id = request.session.get('register_email_id')
		created = False
		obj = None
		if user.is_authenticated:
			'logged in user checkout; remember payment stuff'
			obj, created = self.model.objects.get_or_create(user=user, email=user.email)

		elif guest_email_id is not None:
			'guest user checkout; auto reloads payment stuff'
			guest_email_obj = GuestEmail.objects.get(id=guest_email_id)
			obj, created = self.model.objects.get_or_create(email=guest_email_obj.email)

		elif register_email_id is not None:
			register_email_obj = RealUser.objects.get(id=register_email_id)
			obj, created = self.model.objects.get_or_create(email=register_email_obj.email)
			
		else:
			pass
		return obj, created

class BillingProfile(models.Model):
	user 		= models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True) 
	email 		= models.EmailField()
	active		= models.BooleanField(default=True)
	update	 	= models.DateTimeField(auto_now=True)
	timestamp 	= models.DateTimeField(auto_now_add=True)
	customer_id = models.CharField(max_length=120, null=True, blank=True)
	# customer_id in Stripe or BrainTree

	objects = BillingProfileManager()

	def __str__(self):
		return self.email

	def charge(self, order_obj, card=None):
		return Charge.objects.do(self, order_obj, card)

	#create subscribe object	
	def subscribe(self, order_obj, card=None):
		return BoxSubscription.objects.do(self, order_obj, card)
	
	#unsubscribe customer
	# def unsubscribe(self):
	# 	return Subscription.objects.undo(self)

	def get_cards(self):
		return self.card_set.all()

	def get_payment_method_url(self):
		return reverse('billing-payment-method')

	@property
	def has_card(self): # instance.has_card
		card_qs = self.get_cards()
		return card_qs.exists() # returns True or False

	@property
	def default_card(self):
		default_cards = self.get_cards().filter(active=True, default=True)
		if default_cards.exists():
			return default_cards.first()
		return None

	def set_cards_inactive(self):
		cards_qs = self.get_cards()
		cards_qs.update(active=False)
		return cards_qs.filter(active=True).count()

def billing_profile_created_receiver(sender, instance, *args, **kwargs):
	if not instance.customer_id and instance.email:
		print("ACTUAL API REQUEST: send to Stripe/BrainTree")
		customer = stripe.Customer.create(
				email = instance.email
			)
		print(customer)
		instance.customer_id = customer.id


pre_save.connect(billing_profile_created_receiver, sender=BillingProfile)


def user_created_receiver(sender, instance, created, *args, **kwargs):
	if created and instance.email:
		BillingProfile.objects.get_or_create(user=instance, email=instance.email)

post_save.connect(user_created_receiver, sender=User)



class CardManager(models.Manager):
	def all(self, *args, **kwargs): # ModelKlass.objects.all() --> ModelKlass.objects.filter(active=True) 
		return self.get_queryset().filter(active=True)

	def add_new(self, billing_profile, token):
		if token:
			customer = stripe.Customer.retrieve(billing_profile.customer_id)
			stripe_card_response = customer.sources.create(source=token)
			new_card = self.model(
					billing_profile = billing_profile,
					stripe_id = stripe_card_response.id,
					brand = stripe_card_response.brand,
					country = stripe_card_response.country,
					exp_month = stripe_card_response.exp_month,
					exp_year = stripe_card_response.exp_year,
					last4 = stripe_card_response.last4
				)
			new_card.save()
			return new_card
		return None



class Card(models.Model):
	billing_profile 		= models.ForeignKey(BillingProfile, on_delete=models.CASCADE)
	stripe_id 				= models.CharField(max_length=120)
	brand					= models.CharField(max_length=120, null=True, blank=True)
	country					= models.CharField(max_length=20, null=True, blank=True)
	exp_month				= models.IntegerField(null=True, blank=True)
	exp_year				= models.IntegerField(null=True, blank=True)
	last4 					= models.CharField(max_length=4, null=True, blank=True)
	default 				= models.BooleanField(default=True)
	active					= models.BooleanField(default=True)
	timestamp				= models.DateTimeField(auto_now_add=True)

	objects = CardManager()

	def __str__(self):
		return "{} {}".format(self.brand, self.last4)


def new_card_post_save_receiver(sender, instance, created, *args, **kwargs):
	if instance.default:
		billing_profile = instance.billing_profile
		qs = Card.objects.filter(billing_profile=billing_profile).exclude(pk=instance.pk)
		qs.update(default=False)

post_save.connect(new_card_post_save_receiver, sender=Card)


class ChargeManager(models.Manager):
	def do(self, billing_profile, order_obj, card=None): #Charge.objects.do()
		card_obj = card
		if card_obj is None:
			cards = billing_profile.card_set.filter(default=True)
			if cards.exists():
				card_obj = cards.first()
		if card_obj is None:
			return False, "No cards available"

		c = stripe.Charge.create(
			amount = int(order_obj.total * 100), #39.19
			currency = "usd",
			customer = billing_profile.customer_id,
			source = card_obj.stripe_id,
			metadata={"order_id":order_obj.order_id},
			)
		#print(c)
		new_charge_obj = self.model(
				billing_profile = billing_profile,
				stripe_id = c.id,
				paid = c.paid,
				refunded = c.refunded,
				outcome = c.outcome,
				outcome_type = c.outcome['type'],
				seller_message = c.outcome.get('seller_message'),
				risk_level = c.outcome.get('risk_level'),
		)
		new_charge_obj.save()
		return new_charge_obj.paid, new_charge_obj.seller_message



class Charge(models.Model):
	billing_profile 		= models.ForeignKey(BillingProfile, on_delete=models.CASCADE)
	stripe_id 				= models.CharField(max_length=120)
	paid					= models.BooleanField(default=False)
	refunded				= models.BooleanField(default=False)
	outcome					= models.TextField(null=True, blank=True)
	outcome_type			= models.CharField(max_length=120, blank=True, null=True)
	seller_message			= models.CharField(max_length=120, blank=True, null=True)
	risk_level				= models.CharField(max_length=120, blank=True, null=True)

	objects = ChargeManager()


class BoxSubscriptionManager(models.Manager):
	def do(self, billing_profile, order_obj, card=None): #Subscription.objects.do()
		card_obj = card
		if card_obj is None:
			cards = billing_profile.card_set.filter(default=True)
			if cards.exists():
				card_obj = cards.first()
		if card_obj is None:
			return False, "No cards available"
		sub_obj = order_obj.box.subscription
		#print(cart_obj)
		if order_obj.billing_address.delivery_frequency == 'every-week':
			qs = sub_obj.digitalplan_set.filter(interval_count=1)
			digital_plan_obj = qs.first()
			digital_plan_id = digital_plan_obj.plan_id
		else:
			qs = sub_obj.digitalplan_set.filter(interval_count=2)
			digital_plan_obj = qs.first()
			digital_plan_id = digital_plan_obj.plan_id
		#print(digital_plan_obj)
		#print(digital_plan_obj.plan_id)
		#tax_obj = TaxRate.objects.filter(active=True).first() # Must create a Tax Rate for Subscriptions to work!
		#print(tax_obj.stripe_id)
		#print(digital_plan_id)
		#plan_GcVcjefBiSHGx5

		c = stripe.Subscription.create(
			#billing= "charge automatically",
			#amount = int(order_obj.total * 100), #39.19
			#currency = "usd",
			customer = billing_profile.customer_id,
			#items = [{"plan":"plan_EWVFi6ylaKtwEy"}],
			items = [{"plan": digital_plan_id }],
			#default_tax_rates = [tax_obj.stripe_id],
			#plan_EWVFi6ylaKtwEy - test
			#plan_EXw8wjV0kny5vT - prod
			#once you create a is_digital basic subscription product 
			#(and create a digital plan object with that product attached, need to grab stripe plan ID)
			#source = card_obj.stripe_id,
			metadata={"order_id":order_obj.order_id},
			)
		#print(c)
		formatted_anchor = datetime.datetime.fromtimestamp(c.billing_cycle_anchor)
		formatted_start = datetime.datetime.fromtimestamp(c.current_period_start)
		formatted_end = datetime.datetime.fromtimestamp(c.current_period_end)
		#print(formatted_anchor)

		new_charge_obj = self.model(
				billing_profile = billing_profile,
				stripe_id = c.id,
				paid = True,
				billing = c.billing,
				canceled_at = c.canceled_at,
				plan = c.plan,
				usage_type = c.plan.get('usage_type'),
				interval = c.plan.get('interval'),
				currency = c.plan.get('currency'),
				amount = c.plan.get('amount'),
				billing_cycle_anchor = formatted_anchor,
				current_period_start = formatted_start,
				current_period_end = formatted_end,
				status = c.status,
		)
		new_charge_obj.save()
		return new_charge_obj.paid, new_charge_obj.usage_type
	
	def undo(self, billing_profile):
		c = stripe.Subscription.delete(billing_profile.stripe_id)
		print(c)
		return True



class BoxSubscription(models.Model):
	billing_profile 		= models.ForeignKey(BillingProfile, on_delete=models.CASCADE)
	stripe_id 				= models.CharField(max_length=120)
	billing					= models.CharField(max_length=120, blank=True, null=True)
	paid					= models.BooleanField(default=False)
	canceled_at				= models.CharField(max_length=120, blank=True, null=True)
	plan					= models.TextField(null=True, blank=True)
	usage_type				= models.CharField(max_length=120, blank=True, null=True)
	interval				= models.CharField(max_length=120, blank=True, null=True)
	currency				= models.CharField(max_length=120, blank=True, null=True)
	amount					= models.CharField(max_length=120, blank=True, null=True)
	billing_cycle_anchor	= models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
	current_period_start	= models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
	current_period_end		= models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
	status 					= models.CharField(max_length=120, blank=True, null=True)
	timestamp				= models.DateTimeField(auto_now_add=True)
	updated					= models.DateTimeField(auto_now=True)

	objects = BoxSubscriptionManager()


	def __str__(self):
		return "{} {} {}".format(self.stripe_id, self.interval, self.billing_profile)

