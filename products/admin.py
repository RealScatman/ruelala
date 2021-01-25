from django.contrib import admin

# Register your models here.

from .models import Product, Variation, ProductImage, Category, ProductFeatured, Size, Type, Availability

class ProductImageInline(admin.TabularInline):
	model = ProductImage
	extra = 0
	max_num = 10

class VariationInline(admin.TabularInline):
	model = Variation
	extra = 0
	max_num = 10


class ProductAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'price']
	inlines = [
		ProductImageInline,
		VariationInline,
	]
	class Meta:
		model = Product

class VariationAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'title', 'price', 'inventory', 'size', 'availability']
	class Meta:
		model = Variation


admin.site.register(Product, ProductAdmin)

admin.site.register(Variation, VariationAdmin)

admin.site.register(ProductImage)

admin.site.register(Category)

admin.site.register(Size)

admin.site.register(Type)

admin.site.register(Availability)

admin.site.register(ProductFeatured)