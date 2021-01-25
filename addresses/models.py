from datetime import datetime, timedelta
from django.db import models
#from django.core.urlresolvers import reverse #new code added
from django.urls import reverse
from django.db.models.signals import pre_save, post_save
from billing.models import BillingProfile
from delivery.models import DeliveryZipCode

# Create your models here.

ADDRESS_TYPES = (
	('billing', 'Billing Address'),
	('shipping', 'Shipping Address'),
)

DELIVERY_CHOICES = [
	('every-week', 'Every Week'),
	('every-other-week', 'Every Other Week')
]

class Address(models.Model):
	billing_profile     = models.ForeignKey(BillingProfile, on_delete=models.CASCADE)
	name                = models.CharField(max_length=120, null=True, blank=True, help_text='Shipping to? Who is it for?')
	nickname            = models.CharField(max_length=120, null=True, blank=True, help_text='Internal Reference Nickname')
	address_type	    = models.CharField(max_length=120, choices=ADDRESS_TYPES)
	address_line_1	    = models.CharField(max_length=120)
	address_line_2	    = models.CharField(max_length=120, null=True, blank=True)
	city			    = models.CharField(max_length=120)
	country			    = models.CharField(max_length=120, default='United States of America')
	state			    = models.CharField(max_length=120)
	postal_code		    = models.CharField(max_length=120)
	delivery_frequency	= models.CharField(max_length=120, choices=DELIVERY_CHOICES, default='Every Week')
	delivery_day        = models.ForeignKey(DeliveryZipCode, null=True, blank=True, on_delete=models.SET_NULL)

	#def __str__(self):
	#	return str(self.billing_profile)

	def __str__(self):
		if self.nickname:
			return str(self.nickname)
		return str(self.address_line_1)

	def get_absolute_url(self):
		return reverse("address-update", kwargs={"pk": self.pk})

	def get_short_address(self):
		for_name = self.name 
		if self.nickname:
			for_name = "{} | {},".format( self.nickname, for_name)
		return "{for_name}\n{line1}\n{city}, {state} {postal_code}".format(
			for_name = for_name or "",
			line1 = self.address_line_1,
			city = self.city,
			state = self.state,
			postal_code = self.postal_code
            )

	#old code below

	def get_address(self):
		return "{line1}\n{line2}\n{city}\n{state}, {postal}\n{country}".format(
				line1 = self.address_line_1,
				line2 = self.address_line_2 or "",
				city = self.city,
				state = self.state,
				postal = self.postal_code,
				country = self.country
			)

class DeliveryFrequency(models.Model):
	billing_profile     = models.ForeignKey(BillingProfile, on_delete=models.CASCADE)
	delivery_frequency	= models.CharField(max_length=120, choices=DELIVERY_CHOICES, default='Every Week')
	delivery_start		= models.DateTimeField(null=True, blank=True)
	active				= models.BooleanField(default=True)
	delivered           = models.BooleanField(default=False)

	def __str__(self):
		return self.delivery_frequency
	
	def get_email_date(self):
		delivery_weel_start = self.delivery_start
		date_N_days_ago = delivery_weel_start - timedelta(days=2)
		return date_N_days_ago

	def get_tuesday_delivery_date(self):
		delivery_weel_start = self.delivery_start
		date_N_days_ahead = delivery_weel_start + timedelta(days=2)
		return date_N_days_ahead

	def get_wednesday_delivery_date(self):
		delivery_weel_start = self.delivery_start
		date_N_days_ahead = delivery_weel_start + timedelta(days=3)
		return date_N_days_ahead
	
	def get_absolute_url(self):
		return reverse("delivery-update", kwargs={"pk": self.pk})

	@property
	def get_html_url(self):
		#url = reverse('deliveryfrequency_edit', args=(self.id,))
		#url = ''
		#return f'<p>{self.billing_profile}</p><a href="">edit</a>'
		return f'<p><i class="fas fa-box-open"></i> Box</p><a class="legal-sm" href="">edit</a>'

def post_save_deliveryfrequency_create_receiver(sender, instance, created, *args, **kwargs):
	if created and instance.billing_profile:
		#instance.send_welcome()
		delivery_start = instance.delivery_start
		print(delivery_start)
		delivery_start_formatted = datetime.strptime(delivery_start, '%Y-%m-%d %H:%M')
		print(delivery_start_formatted)
		# new_delivery_start_formatted = delivery_start.strftime("%m/%d/%Y")
		# print(new_delivery_start_formatted)
		new_delivery_start = delivery_start_formatted + timedelta(days=7)
		print(new_delivery_start)
		third_delivery_start = delivery_start_formatted + timedelta(days=14)
		forth_delivery_start = delivery_start_formatted + timedelta(days=21)
		fifth_delivery_start = delivery_start_formatted + timedelta(days=28)
		sixth_delivery_start = delivery_start_formatted + timedelta(days=35)
		seventh_delivery_start = delivery_start_formatted + timedelta(days=42)
		#new_delivery_start_formatted = datetime.strptime(new_delivery_start, '%Y-%m-%d %H:%M:%S.%f')
		# new_delivery_start_formatted = new_delivery_start_formatted.strftime("%m/%d/%Y")
		# print(new_delivery_start)
		#instance.notify_admin()
		DeliveryFrequency.objects.bulk_create([
			DeliveryFrequency(billing_profile=instance.billing_profile,
								delivery_start=new_delivery_start,
								delivery_frequency=instance.delivery_frequency),
			DeliveryFrequency(billing_profile=instance.billing_profile,
								delivery_start=third_delivery_start,
								delivery_frequency=instance.delivery_frequency),
			DeliveryFrequency(billing_profile=instance.billing_profile,
								delivery_start=forth_delivery_start,
								delivery_frequency=instance.delivery_frequency),
			DeliveryFrequency(billing_profile=instance.billing_profile,
								delivery_start=fifth_delivery_start,
								delivery_frequency=instance.delivery_frequency),
			DeliveryFrequency(billing_profile=instance.billing_profile,
								delivery_start=sixth_delivery_start,
								delivery_frequency=instance.delivery_frequency),
			DeliveryFrequency(billing_profile=instance.billing_profile,
								delivery_start=seventh_delivery_start,
								delivery_frequency=instance.delivery_frequency),
		])
post_save.connect(post_save_deliveryfrequency_create_receiver, sender=DeliveryFrequency)