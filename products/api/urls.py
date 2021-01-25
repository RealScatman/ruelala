#from django.urls import path, re_path
from django.conf.urls import include, url

from .views import (
        #PostDetailAPIView,
        #PostListCreateAPIView,
        #ProductListCreateAPIView,
        VariationListCreateAPIView,
        VariationDetailAPIView,
        VariationListCreateAPIView2
        #PostFeaturedAPIView
    )

app_name = 'products-api'

urlpatterns = [
    #url('', ProductListCreateAPIView.as_view(), name='list-create'),
    url('variations/$', VariationListCreateAPIView.as_view(), name='variation-list-create'),
    url('variations2/$', VariationListCreateAPIView2.as_view(), name='variation-list-create2'),
    #path('', PostListCreateAPIView.as_view(), name='list-create'),
    #path('featured/', PostFeaturedAPIView.as_view(), name='list-featured'),
    url(r'variations/(?P<pk>\d+)/$', VariationDetailAPIView.as_view(), name='variation-detail'),
    #re_path(r'^(?P<slug>[\w-]+)/$', PostDetailAPIView.as_view(), name='detail'),

]