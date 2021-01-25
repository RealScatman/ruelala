# from django.conf.urls import url
from django.urls import path, include, re_path

from .views import (
	StripeOrderListView,
	StripeOrderDetailView,
	# StaffOrderDetailView,
	#StaffOrderListView,
	StaffStripeOrderListView,
	StaffStripeOrderDetailView,
	StripeOrderUpdateView,
	#OrderCheckinUpdateView
	# AuctionOrderListView,
	# AuctionOrderDetailView
	)

app_name='orders'

urlpatterns = [
    re_path(r'^$', StripeOrderListView.as_view(), name='stripe-list'),
	re_path(r'^staff/$', StaffStripeOrderListView.as_view(), name='staff-stripe-list'),
    # url(r'^auctions/$', AuctionOrderListView.as_view(), name='auction-list'),
    re_path(r'^(?P<order_id>[0-9A-Za-z]+)/$', StripeOrderDetailView.as_view(), name='stripe-detail'),
    re_path(r'^staff/(?P<order_id>[0-9A-Za-z]+)/$', StaffStripeOrderDetailView.as_view(), name='staff-stripe-detail'),
	re_path(r'^staff/(?P<order_id>[0-9A-Za-z]+)/update$', StripeOrderUpdateView.as_view(), name='staff-stripe-update'),
    # url(r'^auctions/(?P<order_id>[0-9A-Za-z]+)/$', AuctionOrderDetailView.as_view(), name='auction-detail'),
]