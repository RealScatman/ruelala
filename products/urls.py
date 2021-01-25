from django.conf import settings
#from django.conf.urls import include, url
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.contrib import admin

from .views import ProductDetailView, ProductListView, VariationListView, ProductVariationListView, product_create, ProductImageListView, ExpDetailView, product_featured_create, product_variation_api_list_view

app_name='products'

urlpatterns = [
	#url(r'^$', 'products.views.product_list', name='products'),
	re_path(r'^$', ProductListView.as_view(), name='products'),
	re_path(r'^create/$', product_create, name='product-create'),
	re_path(r'^create-featured/$', product_featured_create, name='product-featured-create'),
	re_path(r'^home/$', product_variation_api_list_view, name='product-variation-list-view'),
	re_path(r'^variations/$', ProductVariationListView.as_view(), name='product-variations-list'),
	#re_path(r'^exp/(?P<pk>\d+)/$', ExpDetailView.as_view(), name='exp_detail'),
	re_path(r'^exp/(?P<slug>[\w-]+)/$', ExpDetailView.as_view(), name='exp_detail'),
	#re_path(r'^(?P<pk>\d+)/$', ProductDetailView.as_view(), name='product_detail'),
	re_path(r'^(?P<slug>[\w-]+)/$', ProductDetailView.as_view(), name='product_detail'),
	re_path(r'^(?P<pk>\d+)/inventory/$', VariationListView.as_view(), name='product_inventory'),
	re_path(r'^(?P<pk>\d+)/image/$', ProductImageListView.as_view(), name='product_image'),
]