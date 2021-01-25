from django.conf import settings
#from django.conf.urls import include, url
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.contrib import admin

from .views import DeliveryZipCodeListView, ZipCodeListView

urlpatterns = [
	re_path(r'^$', DeliveryZipCodeListView.as_view(), name='delivery'),
	re_path(r'^zipcode/$', ZipCodeListView.as_view(), name='zip-code-data'),
	#url(r'^(?P<slug>\d+)/$', ProductDetailView.as_view(), name='deliveryzipcode_detail'),
]