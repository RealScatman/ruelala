from django.conf import settings
#from django.conf.urls import include, url
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.contrib import admin

from .views import GrowlerListView

app_name='growlers'

urlpatterns = [
	#url(r'^$', 'products.views.product_list', name='products'),
	re_path(r'^$', GrowlerListView.as_view(), name='growlers'),
	# url(r'^variations/$', ProductVariationListView.as_view(), name='product-variations-list'),
	# url(r'^(?P<pk>\d+)/$', ProductDetailView.as_view(), name='product_detail'),
	# url(r'^(?P<pk>\d+)/inventory/$', VariationListView.as_view(), name='product_inventory'),
]