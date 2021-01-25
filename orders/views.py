import datetime
from django.db.models import Sum
from django.contrib import messages
from django.http import Http404, JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
#from django.core.urlresolvers import reverse, reverse_lazy
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin as LoginRequiredMixin2
from django.views.generic import View
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.utils.http import is_safe_url
from django.template.loader import get_template
# Create your views here.

from ecommerce2.mixins import NextUrlMixin

from .forms import AddressForm, UserAddressForm, StripeOrderChangeForm, OrderChangeForm, UserCheckinForm
from .mixins import CartOrderMixin, LoginRequiredMixin
from .models import UserAddress, UserCheckout, Order, StripeOrder, UserCheckin

from .utils import render_to_pdf

class GeneratePDF(LoginRequiredMixin, View):

	def dispatch(self, *args, **kwargs):
		user = self.request.user
		if not user.is_staff:
			return render(self.request, "400.html", {})
		return super(GeneratePDF, self).dispatch(*args, **kwargs)

	def get_object(self):
		qs = Order.objects.all().filter(pk = self.kwargs.get('pk'))
		if qs.count() == 1:
			return qs.first()
		raise Http404

	def get(self, request, *args, **kwargs):
		template = get_template('pdf/invoice.html')
		#InvoicePDF.objects.get(id=self.id)
		#kwargs={'order_id': self.order_id}
		order = self.get_object()
		context = {
			"order": order,
			# "invoice_id": 118,
			"order_id": order.order_id,
			"customer_name": order.user.user.full_name,
			"customer_email": order.user.user.email,
			"customer_company": "Beaker.Life LLC",
			"customer_address_1": order.billing_address.street,
			"customer_address_city": order.billing_address.city,
			"customer_address_state": order.billing_address.state,
			"customer_address_zipcode": order.billing_address.zipcode,
			"invoice_tax": order.cart.tax_total,
			"invoice_amount": order.order_total,
			"invoice_amount_paid": "0.00",
			"invoice_amount_outstanding": order.order_total,
			"invoice_time": datetime.date.today(),
			#"invoice_memo": "Beaker Life, LLC case acquistion fees for accepted cases at Anapol Weiss law firm.",
			#"invoice_memo": "Beaker Life, LLC will create website www.vaccineawarenesscenter.com, including all full stack web application development services, marketing services, design services.  In exchange for hourly charges paid to Beaker Life, LLC, David J. Carney, Esq. agrees to pay a per-case price for each case that is viable and can be filed in the United States Court of Federal Claims.  For Fiscal Year 2019 (January to December 2019), it is agreed that any case that is originated from www.vaccineawarenesscenter.com, a per-case price of $2,000 would be paid to Beaker Life LLC.  Beaker Life LLC realizes that such cases must be filed in order for the $2,000 payment to be triggered and that such payment can only be made when the case is filed.",
			#"invoice_memo_2": "David J. Carney recognizes the effort, time, and resources that Beaker Life, LLC has spent on creating the website and generating potential cases for Green & Schafle LLC.  The cases are listed below and while none have been filed at this time, it is agreed that $5,000 would be paid to Beaker Life, LLC now and would be credited against the below cases if and when they are filed.",
			"invoice_memo": "Customer Pickup",
			'download': True,
		}
		html = template.render(context)
		pdf = render_to_pdf('pdf/invoice.html', context)
		if pdf:
			response = HttpResponse(pdf, content_type='application/pdf')
			today_date = datetime.date.today()
			formatted_date = today_date.strftime("%Y_%m%d")
			filename = "Invoice_%s_%s_%s.pdf" %("BL", order.order_id, formatted_date)
			content = "inline; filename=%s" %(filename)
			download = request.GET.get("download")
			#print(download)
			if download:
				content = "attachment; filename=%s" %(filename)
			response['Content-Disposition'] = content
			return response
		return HttpResponse("Not found")

class OrderDetail(LoginRequiredMixin2, DetailView):
	form_class = UserCheckinForm
	model = Order
	initial = {'key': 'value'}
	template_name = 'orders/order_detail.html'
	#default_next = '/login/'

	def get_object(self):
		qs = Order.objects.by_request(self.request).filter(pk = self.kwargs.get('pk'))
		if qs.count() == 1:
			return qs.first()
		raise Http404


	# def dispatch(self, request, *args, **kwargs):
	# 	try:
	# 		user_check_id = self.request.session.get("user_checkout_id")
	# 		user_checkout = UserCheckout.objects.get(id=user_check_id)
	# 	except UserCheckout.DoesNotExist:
	# 		if request.user.is_authenticated:
	# 			user_checkout = UserCheckout.objects.get(user=request.user)
	# 		else:
	# 			user_checkout = None
	# 			messages.success(request, "You are not authorized to view this page.")
	# 			return redirect("/")
	# 			#pass
	# 			# next_path = self.get_next_url()
	# 			# return redirect(next_path)
	# 	except:
	# 		user_checkout = None

	# 	obj = self.get_object()
	# 	if obj.user == user_checkout and user_checkout is not None:
	# 		return super(OrderDetail, self).dispatch(request, *args, **kwargs)
	# 	else:
	# 		raise Http404

	def get_success_url(self):
		request = self.request
		messages.success(request, "Check you order status below!")
		return self.get_next_url()

	def get(self, request, *args, **kwargs):
		obj = self.get_object()
		form = self.form_class()
		return render(request, self.template_name, {'order': obj, 'form': form})

	def post(self, request, *args, **kwargs):
		form = self.form_class(request.POST)
		#parking_slot = form.cleaned_data.get("parking_slot")
		parking_slot = request.POST.get("parking_slot")
		order = self.get_object()
		if form.is_valid():
			# <process form cleaned data>
			user_checkin, created = UserCheckin.objects.get_or_create(user_checkout=order.user, order_id=order.order_id, parking_slot=parking_slot, active=True)
			if created:
				order.user_checkin = user_checkin
				order.status = 'checked-in'
				order.save()
				messages.success(request, "Thank you for Checking in! We will be out with your delivery shortly!")
				return HttpResponseRedirect(reverse("order_detail", kwargs={"pk": order.pk}))
		else:
			messages.success(request, "Please select a valid slot between 1 and 5!")
			return HttpResponseRedirect(reverse("order_detail", kwargs={"pk": order.pk}))
		return render(request, self.template_name, {'form': form})



class OrderList(LoginRequiredMixin, ListView):
	queryset = Order.objects.all().not_created()

	def get_queryset(self): #added try block to ensure user_checkout can grab the right user instead of user id
		try:
			request = self.request
			#user_check_id = self.request.user.id
			user_check_email = self.request.user.email
			#print(user_check_id)
			print(user_check_email)
			#user_checkout = UserCheckout.objects.get(id=user_check_id)
			user_checkout = UserCheckout.objects.get(email=user_check_email)
			print(user_checkout)
			print("error here 1")
		except UserCheckout.DoesNotExist:
			print("error here 2")
			messages.success(request, "You do not currently have any orders.")
			return redirect('home')
			#user_checkout = UserCheckout.objects.get(user=request.user)
			#print(user_checkout)
		return super(OrderList, self).get_queryset().filter(user=user_checkout)


# class StaffOrderListView(LoginRequiredMixin, ListView):
# 	def get_queryset(self):
# 		return Order.objects.all()

class StaffOrderListView(LoginRequiredMixin, ListView):

	template_name = 'orders/stafforder_list.html'

	def dispatch(self, *args, **kwargs):
		user = self.request.user
		if not user.is_staff:
			return render(self.request, "400.html", {})
		return super(StaffOrderListView, self).dispatch(*args, **kwargs)

	def get_queryset(self):
		return Order.objects.all().not_created().order_by('-id')

	def get_context_data(self, *args, **kwargs):
		context = super(StaffOrderListView, self).get_context_data(*args, **kwargs)
		latest_qs = Order.objects.all().not_created().last()
		#latest_order = user_obj.order_set.all().order_by('-id')[0]
		context['latest_order'] = latest_qs
		return context

class StaffOrderDetailView(LoginRequiredMixin, DetailView):
	template_name = 'orders/stafforder_detail.html'

	def dispatch(self, *args, **kwargs):
		user = self.request.user
		if not user.is_staff:
			return render(self.request, "400.html", {})
		return super(StaffOrderDetailView, self).dispatch(*args, **kwargs)

	def get_object(self):
		qs = Order.objects.all().filter(pk = self.kwargs.get('pk'))
		if qs.count() == 1:
			return qs.first()
		raise Http404

class StaffOrderUpdateView(LoginRequiredMixin, UpdateView):
	form_class = OrderChangeForm
	template_name = 'orders/stafforder_update.html'

	def dispatch(self, *args, **kwargs):
		user = self.request.user
		if not user.is_staff:
			return render(self.request, "400.html", {})
		return super(StaffOrderUpdateView, self).dispatch(*args, **kwargs)

	def get_object(self):
		qs = Order.objects.all().filter(pk = self.kwargs.get('pk'))
		if qs.count() == 1:
			return qs.first()
		raise Http404

	def get_context_data(self, *args, **kwargs):
		context = super(StaffOrderUpdateView, self).get_context_data(*args, **kwargs)
		context['title'] = 'Change Order Status'
		return context

	def get_success_url(self):
		request = self.request
		messages.success(request, "Order Status has been updated! The customer has been notified via email!")
		return reverse("staff-order-detail", kwargs={'pk': self.kwargs.get('pk')})
		#return reverse("staff-order-list")

class StaffCustomerDetailView(LoginRequiredMixin, DetailView):
	template_name = 'orders/staffcustomer_detail.html'

	def dispatch(self, *args, **kwargs):
		user = self.request.user
		if not user.is_staff:
			return render(self.request, "400.html", {})
		return super(StaffCustomerDetailView, self).dispatch(*args, **kwargs)

	def get_object(self):
		qs = UserCheckout.objects.all().filter(pk = self.kwargs.get('pk'))
		if qs.count() == 1:
			return qs.first()
		raise Http404

	def get_context_data(self, *args, **kwargs):
		context = super(StaffCustomerDetailView, self).get_context_data(*args, **kwargs)
		user_qs = UserCheckout.objects.all().filter(pk = self.kwargs.get('pk'))
		user_obj = user_qs.first()
		lifetime_value_dict = user_obj.order_set.all().aggregate(Sum('order_total'))
		latest_order = user_obj.order_set.all().order_by('-id')[0]
		print(latest_order)
		#print(lifetime_value_dict)
		lifetime_value = lifetime_value_dict['order_total__sum']
		#print(lifetime_value)
		context['lifetime_value'] = lifetime_value
		context['latest_order'] = latest_order
		return context


class UserAddressCreateView(CreateView):
	form_class = UserAddressForm
	template_name = "forms.html"
	success_url = "/checkout/address/"

	def get_checkout_user(self):
		user_check_id = self.request.session.get("user_checkout_id")
		user_checkout = UserCheckout.objects.get(id=user_check_id)
		return user_checkout

	def form_valid(self, form, *args, **kwargs):
		form.instance.user = self.get_checkout_user()
		return super(UserAddressCreateView, self).form_valid(form, *args, **kwargs)







class AddressSelectFormView(CartOrderMixin, FormView):
	form_class = AddressForm
	template_name = "orders/address_select.html"


	def dispatch(self, *args, **kwargs):
		b_address, s_address = self.get_addresses()
		if b_address.count() == 0:
			messages.success(self.request, "Please add a billing address before continuing")
			return redirect("user_address_create")
		# elif s_address.count() == 0:
		# 	messages.success(self.request, "Please add a shipping address before continuing")
		# 	return redirect("user_address_create")
		else:
			return super(AddressSelectFormView, self).dispatch(*args, **kwargs)


	def get_addresses(self, *args, **kwargs):
		#user_check_id = self.request.session.get("user_checkout_id")
		user_check_email = self.request.user.email
		#user_checkout = UserCheckout.objects.get(id=user_check_id)
		user_checkout = UserCheckout.objects.get(email=user_check_email)
		b_address = UserAddress.objects.filter(
				user=user_checkout,
				type='billing',
			)
		# s_address = UserAddress.objects.filter(
		# 		user=user_checkout,
		# 		type='shipping',
		# 	)
		s_address = UserAddress.objects.filter(
				user=user_checkout,
				type='billing',
			) # trick system to populate a shipping address tht is same as billing
		return b_address, s_address


	def get_form(self, *args, **kwargs):
		form = super(AddressSelectFormView, self).get_form(*args, **kwargs)
		b_address, s_address = self.get_addresses()

		form.fields["billing_address"].queryset = b_address
		#form.fields["shipping_address"].queryset = s_address
		return form

	def form_valid(self, form, *args, **kwargs):
		billing_address = form.cleaned_data["billing_address"]
		#shipping_address = form.cleaned_data["shipping_address"] #### switched to same as billing for non delivery online sales
		order = self.get_order()
		order.billing_address = billing_address
		#order.shipping_address = shipping_address #### switched to same as billing for non delivery online sales
		order.shipping_address = billing_address
		order.save()
		return  super(AddressSelectFormView, self).form_valid(form, *args, **kwargs)

	def get_success_url(self, *args, **kwargs):
		print("success")
		return "/checkout/"


class StripeOrderListView(LoginRequiredMixin, ListView):
	def get_queryset(self):
		return StripeOrder.objects.by_request(self.request).not_created()


class StripeOrderDetailView(LoginRequiredMixin, DetailView):

	def get_object(self):
		qs = StripeOrder.objects.by_request(self.request).filter(order_id = self.kwargs.get('order_id'))
		if qs.count() == 1:
			return qs.first()
		raise Http404


class StaffStripeOrderListView(LoginRequiredMixin, ListView):

	template_name = 'orders/staffstripeorder_list.html'

	def dispatch(self, *args, **kwargs):
		user = self.request.user
		if not user.is_staff:
			return render(self.request, "400.html", {})
		return super(StaffStripeOrderListView, self).dispatch(*args, **kwargs)

	def get_queryset(self):
		return StripeOrder.objects.all().not_created()

class StaffStripeOrderDetailView(LoginRequiredMixin, DetailView):
	template_name = 'orders/staffstripeorder_detail.html'

	def dispatch(self, *args, **kwargs):
		user = self.request.user
		if not user.is_staff:
			return render(self.request, "400.html", {})
		return super(StaffStripeOrderDetailView, self).dispatch(*args, **kwargs)

	def get_object(self):
		qs = StripeOrder.objects.all().filter(order_id = self.kwargs.get('order_id'))
		if qs.count() == 1:
			return qs.first()
		raise Http404

class StripeOrderUpdateView(LoginRequiredMixin, UpdateView):
	form_class = StripeOrderChangeForm
	template_name = 'orders/staffstripeorder_update.html'

	def dispatch(self, *args, **kwargs):
		user = self.request.user
		if not user.is_staff:
			return render(self.request, "400.html", {})
		return super(StripeOrderUpdateView, self).dispatch(*args, **kwargs)

	def get_object(self):
		qs = StripeOrder.objects.all().filter(order_id = self.kwargs.get('order_id'))
		if qs.count() == 1:
			return qs.first()
		raise Http404

	def get_context_data(self, *args, **kwargs):
		context = super(StripeOrderUpdateView, self).get_context_data(*args, **kwargs)
		context['title'] = 'Change Order Status'
		return context

	def get_success_url(self):
		return reverse("orders:staff-stripe-list")

class OrderCheckinUpdateView(LoginRequiredMixin, View):
	# form_class = UserCheckinForm
	# template_name = 'orders/order_detail.html'

	def dispatch(self, *args, **kwargs):
		user = self.request.user
		if not user.is_authenticated:
			return render(self.request, "400.html", {})
		return super(OrderCheckinUpdateView, self).dispatch(*args, **kwargs)

	def get_object(self):
		qs = Order.objects.all().filter(pk = self.kwargs.get('pk'))
		if qs.count() == 1:
			return qs.first()
		raise Http404

	def get_context_data(self, *args, **kwargs):
		context = super(OrderCheckinUpdateView, self).get_context_data(*args, **kwargs)
		context['title'] = 'User Checkin'
		return context

	# def get_success_url(self):
	# 	return reverse("order_detail", kwargs={"pk": self.pk})

	def get(self, request, *args, **kwargs):
		#template = get_template('orders/order_checkin.html')
		#InvoicePDF.objects.get(id=self.id)
		#kwargs={'order_id': self.order_id}
		order = self.get_object()
		# context = {
		# 	"order": order,
		# 	# "invoice_id": 118,
		# 	"order_id": order.order_id,
		# 	"customer_name": order.user.user.full_name,
		# 	"customer_email": order.user.user.email,
		# }
		#html = template.render(context)
		#pdf = render_to_pdf('pdf/invoice.html', context)
		user_checkin, created = UserCheckin.objects.get_or_create(user_checkout=order.user, order_id=order.order_id, active=True)
		if created:
			order.user_checkin = user_checkin
			order.status = 'checked-in'
			order.save()
			messages.success(request, "Thank you for Checking in! We will be out with your delivery shortly!")
			#return order.get_absolute_url()
			#return reverse_lazy("order_detail", kwargs={"pk": order.pk})
			#return super(OrderCheckinUpdateView, self).get(*args, **kwargs)
			return HttpResponseRedirect(reverse("order_detail", kwargs={"pk": order.pk}))
		# if pdf:
		# 	response = HttpResponse(pdf, content_type='application/pdf')
		# 	today_date = datetime.date.today()
		# 	formatted_date = today_date.strftime("%Y_%m%d")
		# 	filename = "Invoice_%s_%s_%s.pdf" %("BL", order.order_id, formatted_date)
		# 	content = "inline; filename=%s" %(filename)
		# 	download = request.GET.get("download")
		# 	#print(download)
		# 	if download:
		# 		content = "attachment; filename=%s" %(filename)
		# 	response['Content-Disposition'] = content
		# 	return response
		return HttpResponse("Not found")

	# def post(self, request, *args, **kwargs):
	# 	form = self.form_class(request.POST)
	# 	if form.is_valid():
	# 		# <process form cleaned data>
	# 		return HttpResponseRedirect('/success/')

	# 	return render(request, self.template_name, {'form': form})