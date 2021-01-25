from django.contrib import admin

# Register your models here.
from .models import ZipCodeImport, DeliveryZipCode, ZipCode

class DeliveryZipCodeAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'slug', 'active', 'timestamp']

	class Meta:
		model = DeliveryZipCode

admin.site.register(DeliveryZipCode, DeliveryZipCodeAdmin)

class ZipCodeAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'latitude', 'longitude', 'active']

	class Meta:
		model = ZipCode

admin.site.register(ZipCode, ZipCodeAdmin)

class ZipCodeImportAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'timestamp', 'updated']

	class Meta:
		model = ZipCodeImport

admin.site.register(ZipCodeImport, ZipCodeImportAdmin)