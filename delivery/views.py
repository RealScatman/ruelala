import random
import csv

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import render, redirect, reverse
from django.views.generic import UpdateView, ListView
from django.views.generic.edit import FormMixin
from django.utils.safestring import mark_safe
from .forms import ZipCodeImportForm, CheckZipCodeForm

from .models import DeliveryZipCode, ZipCode, ZipCodeImport
# Create your views here.

class DeliveryZipCodeListView(FormMixin, ListView):
	model = DeliveryZipCode
	queryset = DeliveryZipCode.objects.all()
	template_name = "delivery/deliveryzipcode_list.html"
	form_class = CheckZipCodeForm
	success_url = '/delivery/'

	def get_context_data(self, *args, **kwargs):
		context = super(DeliveryZipCodeListView, self).get_context_data(*args, **kwargs)
		context["form"] = self.get_form()
		return context

	def post(self, request, *args, **kwargs):
		# create a form to receive  an email
		form = self.get_form()
		if form.is_valid():
			print(form.cleaned_data)
			#request = self.request
			#messages.success(request, "Activation link sent, please check your email.")
			return self.form_valid(form)
		else:
			return self.form_invalid(form)

	def form_valid(self, form):
		#msg = "Activation link sent, please check your email."""
		request = self.request
		#messages.success(request, "Great News! We deliver to your area!")
		zipcode = form.cleaned_data.get("zipcode")
		obj = DeliveryZipCode.objects.zipcode_exists(zipcode).first()
		print(obj)
		if obj is not None:
			delivery_day = obj.delivery_day
			product_link = reverse("account:subscription-list")
			msg = """<i class="far fa-check-circle"></i> Good news! We deliver to your area on <b>{day}s</b>! Get Started by selecting a <a href="{link}">box</a>.
			""".format(day=delivery_day, link=product_link)
			messages.success(request, mark_safe(msg))
		else:
			msg = """<i class="fas fa-times"></i> Uh oh! We do not currently deliver to your area!
			"""
			messages.warning(request, mark_safe(msg))
		#messages.success(request, "Great News! We deliver to your area!")
		return super(DeliveryZipCodeListView, self).form_valid(form)


class ZipCodeImportView(SuccessMessageMixin, UpdateView):
	form_class = ZipCodeImportForm
	#template_name = 'base/forms.html' # yeah create this
	template_name = 'delivery/zip-code-import.html' # yeah create this
	#success_url = '/settings/ign-import/'
	success_url = '/delivery/zipcode/'
	success_message = "A Master zipcode csv import was successful. Thank you."

	def dispatch(self, *args, **kwargs):
		# user = self.request.user
		# if not user.is_authenticated():
		# 	return redirect("/login/?next=/settings/ign/") # HttpResponse("Not allowed", status=400)
		return super(ZipCodeImportView, self).dispatch(*args, **kwargs)
	
	def get_context_data(self, *args, **kwargs):
		context = super(ZipCodeImportView, self).get_context_data(*args, **kwargs)
		context['title'] = 'Master ZipCode Data Import'
		context['zip_code_import'] = ZipCodeImport.objects.all()[:1]
		return context

	def get_object(self):
		#user = self.request.user
		# obj, created = IgnImport.objects.get_or_create() # get_absolute_url
		# print(obj, created)
		# #print(obj)
		# return obj
		qs = ZipCodeImport.objects.all()
		if qs.count() == 1:
			return qs.first()
		return None

class ZipCodeListView(LoginRequiredMixin, ListView):
	template_name = 'delivery/zip-code-list.html'


	def dispatch(self, *args, **kwargs):
		zip_code = ZipCode.objects.all()
		#print(ign_content)
		if zip_code.count() > 0:
			pass
		else:
			return HttpResponseRedirect(reverse('zip-code-import'))
			#return HttpResponseRedirect(reverse('ign-pref')) #good one
			#return redirect("/settings/ign/")
		return super(ZipCodeListView, self).dispatch(*args, **kwargs)

	def get_context_data(self, *args, **kwargs):
		context = super(ZipCodeListView, self).get_context_data(*args, **kwargs)
		return context

	def get_queryset(self, *args, **kwargs):
		request = self.request
		return ZipCode.objects.all().order_by('zipcode')