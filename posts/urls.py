from django.conf import settings
#from django.conf.urls import url
from django.urls import path, include, re_path
from django.contrib import admin

from .views import (
	post_list,
	post_create,
	post_update,
	#post_delete,
	PostDetailView,
	#NewPostListView
	)

app_name='posts'

urlpatterns = [
	re_path(r'^$', post_list, name='list'),
	#url(r'^latest/$', NewPostListView.as_view(), name='new-list'),
    re_path(r'^create/$', post_create, name='create'),
    re_path(r'^(?P<slug>[\w-]+)/$', PostDetailView.as_view(), name='detail'),
    re_path(r'^(?P<slug>[\w-]+)/edit/$', post_update, name='update'),
    #url(r'^(?P<slug>[\w-]+)/delete/$', post_delete)
]