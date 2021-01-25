from django.core.exceptions import ImproperlyConfigured
from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

# Create your views here.

from .models import Growler

class GrowlerListView(ListView):
	model = Growler
	queryset = Growler.objects.all()


	def get_context_data(self, *args, **kwargs):
		context = super(GrowlerListView, self).get_context_data(*args, **kwargs)
		context["now"] = timezone.now()
		latest_growler = Growler.objects.last()
		context['latest_growler'] = latest_growler
		context["query"] = self.request.GET.get("q") #None
		return context

	def get_queryset(self, *args, **kwargs):
		qs = super(GrowlerListView, self).get_queryset(*args, **kwargs)
		query = self.request.GET.get("q")
		if query:
			qs = self.model.objects.filter(
				Q(title__icontains=query) |
				Q(description__icontains=query)
				)
			try:
				qs2 = self.model.objects.filter(
					Q(price=query)
				)
				qs = (qs | qs2).distinct()
			except:
				pass
		return qs
