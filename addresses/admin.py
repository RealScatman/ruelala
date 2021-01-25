from django.contrib import admin

from .models import Address, DeliveryFrequency

# Register your models here.

class DeliveryFrequencyAdmin(admin.ModelAdmin):
	#search_fields = ['email']
	list_display = ('__str__', 'billing_profile', 'delivery_frequency', 'delivery_start')

	class Meta:
		model = DeliveryFrequency

admin.site.register(Address)

admin.site.register(DeliveryFrequency, DeliveryFrequencyAdmin)