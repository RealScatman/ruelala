import random
import os
from datetime import timedelta
from decimal import Decimal
from django.conf import settings
#from django.core.urlresolvers import reverse
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save, post_save
from django.contrib.auth.models import (
	AbstractBaseUser, BaseUserManager
)

from django.core.mail import send_mail
from django.template.loader import get_template
from django.utils import timezone

from products.models import Product

from ecommerce2.utils import random_string_generator, unique_key_generator, unique_slug_generator, get_filename

#from marketing.models import AuctionEmailPreference

DEFAULT_ACTIVATION_DAYS = getattr(settings, 'DEFAULT_ACTIVATION_DAYS', 7)

import stripe
STRIPE_SECRET_KEY = getattr(settings, "STRIPE_SECRET_KEY", "XXX")
stripe.api_key = STRIPE_SECRET_KEY


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
	return "subscriptions/{new_filename}/{final_filename}".format(
			new_filename=new_filename, final_filename=final_filename)


class UserManager(BaseUserManager):
	def create_user(self, email, password=None, full_name=None, is_active=False, is_staff=False, is_admin=False):
		if not email:
			raise ValueError("Users must have a email address")
		if not password:
			raise ValueError("Users must have a password")
		user_obj = self.model(
			email = self.normalize_email(email),
			full_name = full_name,
		)
		user_obj.set_password(password) # can use this to change the users password
		user_obj.staff = is_staff
		user_obj.admin = is_admin
		user_obj.is_active = is_active # changed user_obj.active to user_obj.is_active # updates is active to True to allow fast register
		user_obj.save(using=self._db)
		return user_obj

	def create_staffuser(self, email, full_name=None, password=None):
		user = self.create_user(
			email,
			full_name=full_name,
			password=password,
			is_staff=True
		)
		return user

	def create_superuser(self, email, full_name=None, password=None):
		user = self.create_user(
			email,
			full_name=full_name,
			password=password,
			is_staff=True,
			is_admin=True,
			is_active=True,
		)
		return user


class User(AbstractBaseUser):
	email 		= models.EmailField(max_length=255, unique=True)
	full_name	= models.CharField(max_length=255, blank=True, null=True)
	#company  	= models.CharField(max_length=255, blank=True, null=True) #added for law leads
	#specialty 	= models.CharField(max_length=120, default='vaccine', choices=SPECIALTY_CHOICES) #added for law leads
	active		= models.BooleanField(default=True) # able to login
	is_active	= models.BooleanField(default=False) # able to login
	is_member	= models.BooleanField(default=False, verbose_name='Is Subscriber') # signed up for free seller membership
	staff		= models.BooleanField(default=False) # staff user non super
	admin		= models.BooleanField(default=False) # superuser
	timestamp	= models.DateTimeField(auto_now_add=True)
	confirmed	= models.BooleanField(default=False, verbose_name='Is Confirmed Lawyer') # 
	# confirmed_date	= models.DateTimeField(auto_now_add=True) # 

	USERNAME_FIELD = 'email' #username
	# email and password are required by default
	REQUIRED_FIELDS = [] #['full_name'] # python manage.py createsuperuser

	objects = UserManager()
	
	def __str__(self):
		return self.email

	def get_full_name(self):
		if self.full_name:
			return self.full_name
		return self.email

	def get_short_name(self):
		return self.email

	def has_perm(self, perm, obj=None):
		return True

	def has_module_perms(self, app_label):
		return True

	@property
	def is_staff(self):
		if self.is_admin:
			return True
		return self.staff

	@property
	def is_admin(self):
		return self.admin

	@property
	def is_sub_member(self):
		if self.is_member:
			return True
		return False

	@property
	def is_confirmed_lawyer(self):
		if self.confirmed:
			return True
		return False

	@property
	def is_active_member(self):
		if self.is_active:
			return True
		return False

	def set_paid_member(self):
		if self.is_active:
			#user = self.user
			print("set paid is triggering...")
			#print(user)
			self.is_member = True
			self.save()
			#self.save()
			return True
		return False


	def is_seller(self):
		try:
			seller = self.seller
			return True
		except ObjectDoesNotExist:
			return False
	# @property
	# def is_active(self):
	# 	return self.active

	def notify_admin(self):
		if self.email:
			user_full_name = self.full_name
			#user_company = self.company
			# base_url = getattr(settings, 'BASE_URL', 'https://www.sample.link/')
			# key_path = reverse("account:email-activate", kwargs={'key':self.key}) # use reverse
			# path = "{base}{path}".format(base=base_url, path=key_path)
			context = {
				#'path': path,
				'full_name': user_full_name,
				#'company': user_company,
				'email': self.email,
			}
			txt_ = get_template("registration/emails/notify.txt").render(context)
			html_ = get_template("registration/emails/notify.html").render(context)
			subject = 'New User joined eGrocer!'
			from_email = settings.DEFAULT_FROM_EMAIL
			recipient_list = [settings.DEFAULT_FROM_EMAIL]
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


# def post_save_user_create_receiver(sender, instance, created, *args, **kwargs):
# 	if created and instance.email:
# 		#instance.send_welcome()
# 		instance.notify_admin()
# post_save.connect(post_save_user_create_receiver, sender=User)


# def post_save_user_confirm_receiver(sender, instance, created, *args, **kwargs):
# 	if instance.is_confirmed_lawyer == True and instance.is_active_member == False:
# 		obj = EmailActivation.objects.create(user=instance, email=instance.email)
# 		obj.send_activation()
# 		print("triggered...Error Code: Baboon")

# post_save.connect(post_save_user_confirm_receiver, sender=User)

# def post_save_user_active_receiver(sender, instance, created, *args, **kwargs):
# 	if instance.is_active_member:
# 		obj = AuctionEmailPreference.objects.get_or_create(user=instance)
# 		print("New User activated and now enrolled in New Auction Emails...")

# post_save.connect(post_save_user_active_receiver, sender=User)

# class EmailActivationQuerySet(models.query.QuerySet):
# 	def confirmable(self):
# 		now = timezone.now()
# 		start_range = now - timedelta(days=DEFAULT_ACTIVATION_DAYS)
# 		# does my object have a timestamp in here
# 		end_range = now
# 		return self.filter(
# 				activated = False,
# 				forced_expired = False
# 			).filter(
# 				timestamp__gt=start_range,
# 				timestamp__lte=end_range
# 			)

# class EmailActivationManager(models.Manager):
# 	def get_queryset(self):
# 		return EmailActivationQuerySet(self.model, using=self._db)

# 	def confirmable(self):
# 		return self.get_queryset().confirmable()

# 	def email_exists(self, email):
# 		return self.get_queryset().filter(Q(email=email) | Q(user__email=email)).filter(activated=False)


# class EmailActivation(models.Model):
# 	user 			= models.ForeignKey(User)
# 	email 			= models.EmailField()
# 	key 			= models.CharField(max_length=120, blank=True, null=True)
# 	activated		= models.BooleanField(default=False)
# 	forced_expired	= models.BooleanField(default=False)
# 	expires			= models.IntegerField(default=7) # 7 day expiration
# 	timestamp		= models.DateTimeField(auto_now_add=True)
# 	update			= models.DateTimeField(auto_now=True)

# 	objects = EmailActivationManager()


# 	def __str__(self):
# 		return self.email

# 	def can_activate(self):
# 		qs = EmailActivation.objects.filter(pk=self.pk).confirmable() # will return one object
# 		if qs.exists():
# 			return True
# 		return False

# 	def activate(self):
# 		if self.can_activate():
# 			user = self.user
# 			user.is_active = True
# 			user.save()
# 			self.activated = True
# 			self.save()
# 			return True
# 		return False

# 	def regenerate(self):
# 		self.key = None
# 		self.save()
# 		if self.key is not None:
# 			return True
# 		return False


# 	def send_activation(self):
# 		if not self.activated and not self.forced_expired:
# 			if self.key:
# 				base_url = getattr(settings, 'BASE_URL', 'https://www.beaker.life')
# 				key_path = reverse("account:email-activate", kwargs={'key':self.key}) # use reverse
# 				path = "{base}{path}".format(base=base_url, path=key_path)
# 				context = {
# 					'path': path,
# 					'email': self.email,
# 				}
# 				txt_ = get_template("registration/emails/verify.txt").render(context)
# 				html_ = get_template("registration/emails/verify.html").render(context)
# 				subject = 'One-Click Email Verification'
# 				from_email = settings.DEFAULT_FROM_EMAIL
# 				recipient_list = [self.email]
# 				sent_mail = send_mail(
# 							subject,
# 							txt_,
# 							from_email,
# 							recipient_list,
# 							html_message=html_,
# 							fail_silently=False,
# 					)
# 				return sent_mail
# 		return False




# def pre_save_email_activation(sender, instance, *args, **kwargs):
# 	if not instance.activated and not instance.forced_expired:
# 		if not instance.key:
# 			instance.key = unique_key_generator(instance)


# pre_save.connect(pre_save_email_activation, sender=EmailActivation)

# def post_save_user_create_receiver(sender, instance, created, *args, **kwargs):
# 	if created:
# 		obj = EmailActivation.objects.create(user=instance, email=instance.email)
# 		obj.send_activation()


# post_save.connect(post_save_user_create_receiver, sender=User)

class GuestEmail(models.Model):
	email 		= models.EmailField()
	active		= models.BooleanField(default=True)
	update	 	= models.DateTimeField(auto_now=True)
	timestamp 	= models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.email


class BoxSelectionManager(models.Manager):

	def new_or_get(self,request):
		box_id = request.session.get("box_id", None)
		# register_email_id = request.session.get('register_email_id')
		# print(register_email_id)
		qs = self.get_queryset().filter(id=box_id)
		if qs.count() == 1:
			new_obj = False
			box_obj = qs.first()
			if request.user.is_authenticated and box_obj.user is None:
				box_obj.user = request.user
				box_obj.save()
		# elif register_email_id is not None:
		# 	register_email_obj = User.objects.get(id=register_email_id)
		# 	box_obj = BoxSelection.objects.update(user=register_email_obj)
		# 	request.session['box_id'] = box_obj.id 
		# 	#new_obj = True
		# 	return box_obj, new_obj
		# 	#box_obj.save()
		else:
			box_obj = BoxSelection.objects.new(user=request.user)
			new_obj = True
			request.session['box_id'] = box_obj.id 

		return box_obj, new_obj


	def new(self, user=None):
		print(user)
		user_obj = None
		if user is not None:
			if user.is_authenticated:
				user_obj = user
		return self.model.objects.create(user=user_obj)
	
	def update(self, user=None):
		user_obj = None
		updated = False
		if user is not None:
			user = user_obj
			update = self.model.objects.update(user=user_obj)
			updated = True
			return updated
		return updated


class BoxSelection(models.Model):
	user         = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
	subscription = models.ForeignKey('Subscription', null=True, blank=True, on_delete=models.SET_NULL)
	subtotal	 = models.DecimalField(default=0.00, max_digits=100, decimal_places=2)
	total		 = models.DecimalField(default=0.00, max_digits=100, decimal_places=2)
	timestamp    = models.DateTimeField(auto_now_add=True, auto_now=False)
	updated      = models.DateTimeField(auto_now_add=False, auto_now=True)

	objects = BoxSelectionManager()

	def __str__(self):
		try:
			return "%s box cost %s" %(self.subscription.title, self.total)
		except:
			return "%s box cost %s" %('None', self.total)


def pre_save_boxselection_receiver(sender, instance, *args, **kwargs):
	if instance.subtotal > 0:
		instance.total = Decimal(instance.subtotal) * Decimal(1.06) # 6 % tax
	else:
		instance.total = 0.00

pre_save.connect(pre_save_boxselection_receiver, sender=BoxSelection)


class Subscription(models.Model):
	title       = models.CharField(max_length=120)
	slug	    = models.SlugField(blank=True, null=True)
	description = models.TextField(blank=True, null=True)
	image		= models.ImageField(upload_to=upload_image_path, null=True, blank=True)
	price       = models.DecimalField(decimal_places=2, max_digits=20)
	products    = models.ManyToManyField(Product, blank=True)
	active      = models.BooleanField(default=True)

	def __str__(self):
		return self.title

def subscription_pre_save_receiver(sender, instance, *args, **kwargs):
	if not instance.slug:
		instance.slug = unique_slug_generator(instance)

pre_save.connect(subscription_pre_save_receiver, sender=Subscription)


class DigitalPlan(models.Model):
	subscription    = models.ForeignKey(Subscription, on_delete=models.CASCADE)
	amount 		    = models.PositiveIntegerField(default=19999)
	interval 	    = models.CharField(max_length=120, default='month')
	interval_count  = models.CharField(max_length=120, default='1')
	currency	    = models.CharField(max_length=60, default='usd', null=False, blank=False)
	plan_id		    = models.CharField(max_length=120, null=True, blank=True)
	stripe_plan     = models.TextField(null=True, blank=True)
	active 		    = models.BooleanField(default=True)

	def __str__(self):
		return self.subscription.title


def digitalplan_pre_save_receiver(sender, instance, *args, **kwargs):
	if instance.active:
		print("ACTUAL API REQUEST: send to Stripe for Subscription Plan linked to Membership creation...")	
		stripe_plan = stripe.Plan.create(
		amount=instance.amount,
		interval=instance.interval,
		interval_count=instance.interval_count,
		product={
			"name": instance.subscription.title
			},
		currency=instance.currency,
		active=instance.active,
		)
		#print(stripe_plan)
		instance.plan_id = stripe_plan.id
		instance.stripe_plan = stripe_plan
		#instance.save()
		return True

pre_save.connect(digitalplan_pre_save_receiver, sender=DigitalPlan)