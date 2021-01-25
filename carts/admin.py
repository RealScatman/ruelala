from django.contrib import admin

# Register your models here.
from .models import Cart, CartItem, PickupTime, CartTime



class CartItemInline(admin.TabularInline):
	model = CartItem

class CartAdmin(admin.ModelAdmin):
	inlines = [
		CartItemInline
	]
	class Meta:
		model = Cart


class CartTimeAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'timestamp', 'updated', 'active']
	class Meta:
		model = CartTime

class PickupTimeAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'available', 'timeslot', 'count']
	class Meta:
		model = PickupTime

admin.site.register(Cart, CartAdmin)

admin.site.register(PickupTime, PickupTimeAdmin)

admin.site.register(CartTime, CartTimeAdmin)