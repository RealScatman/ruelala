#from django.conf.urls import url
from django.urls import path, include, re_path

from .views import (
	# AccountHomeView,
	# AccountEmailActivateView,
	UserDetailUpdateView,
	# UserSubscriptionUpdateView
	SubscriptionListView,
	box_update,
	#box_home,
	BoxHomeView,
	checkout_home,
	checkout_done_view,
	checkout_delivery_frequency_create_view,
	MyHomeDetailView
	)

app_name='accounts'

urlpatterns = [
#     url(r'^$', AccountHomeView.as_view(), name='home'),
	  re_path(r'^subscriptions/setup/$', BoxHomeView.as_view(), name='box-home'),
      re_path(r'^details/$', UserDetailUpdateView.as_view(), name='user-update'),
#     url(r'^subscriptions/$', UserSubscriptionUpdateView.as_view(), name='user-subscription'),
	  re_path(r'^subscriptions/$', SubscriptionListView.as_view(), name='subscription-list'),
	  re_path(r'^subscriptions/home/$', MyHomeDetailView.as_view(), name='user-home'),
	  re_path(r'^update/$', box_update, name='update'),
	  re_path(r'^checkout/success/$', checkout_done_view, name='success'),
      re_path(r'^checkout/$', checkout_home, name='checkout'),
	  re_path(r'^subscriptions/delivery/$', checkout_delivery_frequency_create_view, name='checkout-delivery-frequency'),


#     url(r'^history/products/$', UserProductHistoryView.as_view(), name='user-product-history'),
#     url(r'^email/confirm/(?P<key>[0-9A-Za-z]+)/$', AccountEmailActivateView.as_view(), name='email-activate'),
#     url(r'^email/resend-activation/$', AccountEmailActivateView.as_view(), name='resend-activation'),
]