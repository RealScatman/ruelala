from django.contrib import admin

from .models import BillingProfile, Card, Charge, BoxSubscription #, Subscription, InvoicePDF, TaxRate

# Register your models here.

class BillingProfileAdmin(admin.ModelAdmin):
	list_display = ['__str__','email', 'active','customer_id']
	readonly_fields = ['email', 'active','customer_id']
	class Meta:
		model = BillingProfile



admin.site.register(BillingProfile, BillingProfileAdmin)
admin.site.register(Card)
admin.site.register(Charge)
admin.site.register(BoxSubscription)