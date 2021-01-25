from django.contrib import admin

# Register your models here.

from .models import Growler

class GrowlerAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'price', 'inventory', 'active']

	class Meta:
		model = Growler

admin.site.register(Growler, GrowlerAdmin)
