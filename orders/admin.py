from django.contrib import admin

# Register your models here.

from .models import UserCheckout, UserAddress, Order, StripeOrder, UserCheckin


admin.site.register(UserCheckout)

class UserCheckinAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'order_id', 'parking_slot', 'active']
	class Meta:
		model = UserCheckin


admin.site.register(UserCheckin, UserCheckinAdmin)

admin.site.register(UserAddress)

class OrderAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'order_id', 'status']
	class Meta:
		model = Order

admin.site.register(Order, OrderAdmin)

class StripeOrderAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'order_id', 'billing_profile', 'box', 'billing_address', 'total', 'status']
	class Meta:
		model = StripeOrder

admin.site.register(StripeOrder, StripeOrderAdmin)
