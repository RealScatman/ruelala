from django.conf import settings
#from django.conf.urls import include, url
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.views.generic import TemplateView, RedirectView

from accounts.views import LoginView, RegisterView, GuestRegisterView, box_detail_api_view
from addresses.views import (
    AddressCreateView,
    AddressListView,
    AddressUpdateView,
    checkout_address_create_view, 
    checkout_address_reuse_view,
    checkout_deliveryfrequency_create_view,
    DeliveryFrequencyDetailView
    )
from analytics.views import SalesView, SalesAjaxView #, StaffOrdersView
from newsletter.views import home, contact
from carts.views import CartView, ItemCountView, CheckoutView, CheckoutFinalView, pickup_time_select_view, PickupTimeListView, CartPickupView, CartTimeDisplayView, pickuptime_create
from delivery.views import ZipCodeImportView
from orders.views import (
                    AddressSelectFormView,
                    GeneratePDF, 
                    UserAddressCreateView, 
                    OrderList, 
                    OrderDetail,
                    StaffOrderListView,
                    StaffOrderDetailView,
                    StaffCustomerDetailView,
                    StaffOrderUpdateView,
                    OrderCheckinUpdateView
                    )
from billing.views import payment_method_view, payment_method_createview

from .views import about

urlpatterns = [
    # Examples:
    re_path(r'^$', home, name='home'),
    re_path(r'^api-auth/', include('rest_framework.urls')),
    re_path(r'^api/products/', include('products.api.urls', namespace='products-api')),
    re_path(r'^contact/$', contact, name='contact'),
    re_path(r'^about/$', about, name='about'),
    # url(r'^blog/', include('blog.urls')),
    re_path(r'^api/box/$', box_detail_api_view, name='api-box'),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^accounts/$', RedirectView.as_view(url='/account')),
    re_path(r'^account/', include("accounts.urls", namespace='account')),
    # url(r'^accounts/', include('registration.backends.default.urls')),
    re_path(r'^accounts/', include("accounts.passwords.urls")),
    re_path(r'^address/$', RedirectView.as_view(url='/addresses')),
    re_path(r'^addresses/$', AddressListView.as_view(), name='addresses'),
    re_path(r'^addresses/create/$', AddressCreateView.as_view(), name='address-create'),
    re_path(r'^addresses/(?P<pk>\d+)/$', AddressUpdateView.as_view(), name='address-update'),
    re_path(r'^analytics/sales/$', SalesView.as_view(), name='sales-analytics'),
    re_path(r'^analytics/sales/data/$', SalesAjaxView.as_view(), name='sales-analytics-data'),
    re_path(r'^delivery/detail/$', DeliveryFrequencyDetailView.as_view(), name='delivery-detail'),
    re_path(r'^checkout/address/create/$', checkout_address_create_view, name='checkout_address_create'),
    re_path(r'^checkout/address/reuse/$', checkout_address_reuse_view, name='checkout_address_reuse'),
    re_path(r'^checkout/delivery/create/$', checkout_deliveryfrequency_create_view, name='checkout_deliveryfrequency_create'),
    re_path(r'^login/$', LoginView.as_view(), name='login'),
    re_path(r'^logout/$', LogoutView.as_view(), name='logout'),
    re_path(r'^register/$', RegisterView.as_view(), name='register'),
    re_path(r'^register/guest/$', GuestRegisterView.as_view(), name='guest_register'),
    re_path(r'^select2/', include('django_select2.urls')),
    re_path(r'^delivery/', include('delivery.urls')),
    re_path(r'^billing/payment-method/$', payment_method_view, name='billing-payment-method'),
    re_path(r'^billing/payment-method/create/$', payment_method_createview, name='billing-payment-method-endpoint'),
    re_path(r'^products/', include('products.urls')),
    re_path(r'^growlers/', include('growlers.urls')),
    re_path(r'^news/', include("posts.urls", namespace='posts'), {"type": "regular"}),
    re_path(r'^categories/', include('products.urls_categories')),
    re_path(r'^orders/$', OrderList.as_view(), name='orders'),
    re_path(r'^orders/staff/$', StaffOrderListView.as_view(), name='staff-order-list'),
    re_path(r'^orders/staff/(?P<pk>\d+)/$', StaffOrderDetailView.as_view(), name='staff-order-detail'),
    re_path(r'^orders/staff/(?P<pk>\d+)/update$', StaffOrderUpdateView.as_view(), name='staff-order-update'),
    re_path(r'^orders/staff/customer/(?P<pk>\d+)/$', StaffCustomerDetailView.as_view(), name='staff-customer-detail'),
    re_path(r'^orders/(?P<pk>\d+)/$', OrderDetail.as_view(), name='order_detail'),
    re_path(r'^orders/(?P<pk>\d+)/generate-invoice/$', GeneratePDF.as_view(), name='order-generate-invoice'),
    re_path(r'^orders/(?P<pk>\d+)/check-in/$', OrderCheckinUpdateView.as_view(), name='order-generate-check-in'),
    re_path(r'^stripe-orders/', include("orders.urls", namespace='stripe-orders')),
    re_path(r'^cart/$', CartView.as_view(), name='cart'),
    re_path(r'^cart/pickup/$', CartPickupView.as_view(), name='cart-pickup'),
    re_path(r'^cart/pickup-time/create/$', pickuptime_create, name='cart-pickup-create'),
    re_path(r'^cart/time/$', CartTimeDisplayView.as_view(), name='cart_time'),
    re_path(r'^cart/count/$', ItemCountView.as_view(), name='item_count'),
    re_path(r'^cart/pickup-time/$', PickupTimeListView.as_view(), name='pickup_time_select'),
    re_path(r'^checkout/$', CheckoutView.as_view(), name='checkout'),
    re_path(r'^checkout/address/$', AddressSelectFormView.as_view(), name='order_address'),
    re_path(r'^checkout/address/add/$', UserAddressCreateView.as_view(), name='user_address_create'),
    re_path(r'^checkout/final/$', CheckoutFinalView.as_view(), name='checkout_final'),
    re_path(r'^settings/zip-code-import/$', ZipCodeImportView.as_view(), name='zip-code-import'),
]

if settings.DEBUG:
	urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)