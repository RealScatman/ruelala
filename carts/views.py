import braintree
import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
#from django.core.urlresolvers import reverse
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.utils.http import is_safe_url
from django.utils import timezone

from django.shortcuts import render, get_object_or_404, redirect

from django.views.generic import ListView
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin, DetailView
from django.views.generic.edit import FormMixin, FormView
# Create your views here.

from accounts.forms import LoginForm, RegisterForm
from orders.forms import GuestCheckoutForm
from orders.mixins import CartOrderMixin
from orders.models import UserCheckout, UserAddress, Order
from products.models import Variation, Product

from .forms import PickupTimeForm

from .models import Cart, CartItem, PickupTime, CartTime

#if settings.DEBUG:

gateway = braintree.BraintreeGateway(
	braintree.Configuration(
		braintree.Environment.Sandbox,
		merchant_id=settings.BRAINTREE_MERCHANT_ID,
		public_key=settings.BRAINTREE_PUBLIC,
		private_key=settings.BRAINTREE_PRIVATE,
		timeout=20
	)
)



class ItemCountView(View):
	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			cart_id = self.request.session.get("cart_id")
			if cart_id == None:
				count = 0
			else:
				cart = Cart.objects.get(id=cart_id)
				count = cart.items.count()
			request.session["cart_item_count"] = count
			return JsonResponse({"count": count})
		else:
			raise Http404

class CartTimeDisplayView(View):
	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			cart_id = self.request.session.get("cart_id")
			if cart_id == None:
				#cart_time = "0"
				cart_time = "pickup is easy and free"
			else:
				cart = Cart.objects.get(id=cart_id)
				try:
					cart_time_objects = cart.carttime_set.all()
					#print('carttime', cart_time_objects)
					# for x in cart_time_objects:
					# 	cart_time_obj = x.filter(active=True)
					# 	print(cart_time_obj)
					cart_time_obj = cart_time_objects.first()
					#print(cart_time_obj)
					#cart_time_obj = cart.carttime_set.filter(active=True)
					cart_time_date = cart_time_obj.pickup_time.pickup_date
					cart_time_time = cart_time_obj.pickup_time.timeslot
					formated_cart_time_date  = datetime.datetime.strftime(cart_time_date, '%a, %b-%d')
					#formated_cart_time_time  = str(cart_time_time)
					formated_cart_time_time  = datetime.time.strftime(cart_time_time, '%I %p')
					cart_time = formated_cart_time_date + " " + formated_cart_time_time
					#print(cart_time)
				except:
					cart_time = "Please select a pickup time"
			request.session["cart_time"] = cart_time
			return JsonResponse({"cart_time": cart_time})
		else:
			raise Http404


class CartView(SingleObjectMixin, View):
	model = Cart
	template_name = "carts/view.html"

	def get_object(self, *args, **kwargs):
		self.request.session.set_expiry(0) #5 minutes
		cart_id = self.request.session.get("cart_id")
		if cart_id == None:
			cart = Cart()
			cart.tax_percentage = 0.075
			cart.save()
			cart_id = cart.id
			self.request.session["cart_id"] = cart_id
		cart = Cart.objects.get(id=cart_id)
		if self.request.user.is_authenticated:
			cart.user = self.request.user
			cart.save()
		return cart

	def get(self, request, *args, **kwargs):
		cart = self.get_object()
		item_id = request.GET.get("item")
		delete_item = request.GET.get("delete", False)
		flash_message = ""
		item_added = False
		if item_id:
			item_instance = get_object_or_404(Variation, id=item_id)
			qty = request.GET.get("qty", 1)
			try:
				if int(qty) < 1:
					delete_item = True
			except:
				raise Http404
			cart_item, created = CartItem.objects.get_or_create(cart=cart, item=item_instance)
			if created:
				flash_message = "Successfully added item to your cart."
				item_added = True
			if delete_item:
				flash_message = "Item removed successfully."
				cart_item.delete()
			else:
				if not created:
					flash_message = "Quantity has been updated successfully."
				cart_item.quantity = qty
				cart_item.save()
			if not request.is_ajax():
				return HttpResponseRedirect(reverse("cart"))
				#return cart_item.cart.get_absolute_url()
		
		if request.is_ajax():
			try:
				total = cart_item.line_item_total
			except:
				total = None
			try:
				subtotal = cart_item.cart.subtotal
			except:
				subtotal = None

			try:
				cart_total = cart_item.cart.total
			except:
				cart_total = None

			try:
				tax_total = cart_item.cart.tax_total
			except:
				tax_total = None

			try:
				total_items = cart_item.cart.items.count()
			except:
				total_items = 0

			data = {
					"deleted": delete_item, 
					"item_added": item_added,
					"line_total": total,
					"subtotal": subtotal,
					"cart_total": cart_total,
					"tax_total": tax_total,
					"flash_message": flash_message,
					"total_items": total_items
					}

			return JsonResponse(data) 

		related_products = Product.objects.all().order_by("?")[:6]
		related_variations = Variation.objects.all().order_by("?")[:6]
		context = {
			"object": self.get_object(),
			"related_products": related_products,
			"related_variations": related_variations,
		}
		template = self.template_name
		return render(request, template, context)




class CheckoutView(CartOrderMixin, FormMixin, DetailView):
	model = Cart
	template_name = "carts/checkout_view.html"
	form_class = GuestCheckoutForm

	def get_object(self, *args, **kwargs):
		cart = self.get_cart()
		if cart == None:
			return None
		return cart

	def get_context_data(self, *args, **kwargs):
		context = super(CheckoutView, self).get_context_data(*args, **kwargs)
		user_can_continue = False
		user_check_id = self.request.session.get("user_checkout_id")
		request = self.request
		cart = self.get_cart()
		print(cart)
		#if cart.cart_time is not None:
		try:
			#print('trying to fetch already created and active cart time...')
			cart_time_qs = CartTime.objects.filter(cart=cart, active=True)
			#print(cart_time_qs)
			if cart_time_qs.exists():
				cart_time = cart_time_qs.first()
				print('active cart time exists', cart_time)
				context["cart_time_obj"] = cart_time.pickup_time.pickup_date
				context["cart_time_obj_time"] = cart_time.pickup_time.timeslot
			else:
				cart_time, created = CartTime.objects.new_or_get(cart=cart, active=True)
				context["cart_time_obj"] = cart_time.pickup_time.pickup_date
				context["cart_time_obj_time"] = cart_time.pickup_time.timeslot
			#cart_time = CartTime.objects.filter(cart=cart, active=True)
				if created == True:
					print("new cart time created.")
		except:
			pass

		if self.request.user.is_authenticated:
			user_can_continue = True
			user_checkout, created = UserCheckout.objects.get_or_create(email=self.request.user.email)
			user_checkout.user = self.request.user
			user_checkout.save()
			#print("user checkout created.")
			context["client_token"] = user_checkout.get_client_token()
			self.request.session["user_checkout_id"] = user_checkout.id

		elif not self.request.user.is_authenticated and user_check_id == None:
			#context["login_form"] = AuthenticationForm()
			context["login_form"] = LoginForm(request=request)
			context["register_form"] = RegisterForm(request=request)
			context["next_url"] = self.request.build_absolute_uri()
		else:
			pass

		if user_check_id != None:
			user_can_continue = True
			if not self.request.user.is_authenticated: #GUEST USER
				user_checkout_2 = UserCheckout.objects.get(id=user_check_id)
				context["client_token"] = user_checkout_2.get_client_token()

		context["order"] = self.get_order()
		context["user_can_continue"] = user_can_continue
		context["form"] = self.get_form()
		return context

	def post(self, request, *args, **kwargs):
		self.object = self.get_object()
		form = self.get_form()
		if form.is_valid():
			email = form.cleaned_data.get("email")
			user_checkout, created = UserCheckout.objects.get_or_create(email=email)
			request.session["user_checkout_id"] = user_checkout.id
			return self.form_valid(form)
		else:
			return self.form_invalid(form)

	def get_success_url(self):
		return reverse("checkout")


	def get(self, request, *args, **kwargs):
		get_data = super(CheckoutView, self).get(request, *args, **kwargs)
		cart = self.get_object()
		if cart == None:
			return redirect("cart")
		new_order = self.get_order()
		#print(new_order.user)
		user_checkout_id = request.session.get("user_checkout_id")
		if user_checkout_id != None:
			user_checkout = UserCheckout.objects.get(id=user_checkout_id)
			if new_order.billing_address == None or new_order.shipping_address == None:
				return redirect("order_address")
			new_order.user = user_checkout
			new_order.save()
			#print(new_order.user.user.full_name)
		return get_data


class CheckoutFinalView(CartOrderMixin, View):
	def post(self, request, *args, **kwargs):
		order = self.get_order()
		order_total = order.order_total
		nonce = request.POST.get("payment_method_nonce")
		#print(nonce)
		if nonce:
			result = gateway.transaction.sale({
				"amount": order_total,
				"payment_method_nonce": nonce,
				"billing": {
					"postal_code": "%s" %(order.billing_address.zipcode),
					"street_address": "%s" %(order.billing_address.street),
					"last_name": "%s" %(order.user.user.full_name),
					
				 },
				"options": {
					"submit_for_settlement": True
				}
			})
			if result.is_success:
				#result.transaction.id to order
				order.mark_completed(order_id=result.transaction.id)
				order.update_cartitems() # can update the product variation inventory value
				#order.send_order_id() #added send order email to buying user and support email
				messages.success(request, "Thank you for your order! An order receipt has been sent via email.")
				del request.session["cart_id"]
				del request.session["order_id"]
			else:
				#messages.success(request, "There was a problem with your order.")
				messages.success(request, "%s" %(result.message))
				return redirect("checkout")

		return redirect("order_detail", pk=order.pk)

	def get(self, request, *args, **kwargs):
		return redirect("checkout")



class PickupTimeView(FormView):
	template_name = "carts/form_view.html"
	#form_class = PickupTimeForm
	success_url = '/products/variations/'

	def form_valid(self):
		form.do_some_method()
		print("form_validating")
		return super().form_valid(form)


def pickup_time_select_view(request):
	if request.user.is_authenticated:
		context = {}
		next_ = request.GET.get('next')
		next_post = request.POST.get('next')
		redirect_path = next_ or next_post or None
		if request.method == "POST":
			# print(request.POST)
			pickup_time = request.POST.get('pickup_time', None)
			# address_type = request.POST.get('address_type', 'shipping')
			# user_checkout, created = UserCheckout.objects.get_or_create(email=self.request.user.email)
			# user_checkout.user = self.request.user
			# user_checkout.save()
			# billing_profile, billing_profile_created = BillingProfile.objects.new_or_get(request)
			user = self.request.user
			if pickup_time is not None:
				qs = PickupTime.objects.filter(user=user, id=pickup_time)
				if qs.exists():
					request.session[pickup_time + "_pickup_id"] = pickup_time

				if is_safe_url(redirect_path, request.get_host()):
					return redirect(redirect_path)


	return redirect("accounts:checkout") 


class PickupTimeListView(LoginRequiredMixin, ListView):
	template_name = 'carts/pickuptime_list.html'

	def get_queryset(self):
		request = self.request
		today = timezone.now().date()
		now = timezone.localtime().time()
		#print(now)
		#billing_profile, billing_profile_created = BillingProfile.objects.new_or_get(request)
		return PickupTime.objects.filter(pickup_date=today, timeslot__gte=now)

	def get_context_data(self, *args, **kwargs):
		context = super(PickupTimeListView, self).get_context_data(*args, **kwargs)
		#box_obj, new_obj = BoxSelection.objects.new_or_get(self.request)
		#delivery_day = DeliveryZipCode.objects.filter()
		tomorrow = timezone.now().date() + datetime.timedelta(hours=24)
		tomorrow_qs = PickupTime.objects.filter(pickup_date=tomorrow)
		context['tomorrow_qs'] = tomorrow_qs

		# user_check_id = self.request.session.get("user_checkout_id")
		# request = self.request

		# if self.request.user.is_authenticated:
		# 	user_can_continue = True
		# 	user_checkout, created = UserCheckout.objects.get_or_create(email=self.request.user.email)
		# 	user_checkout.user = self.request.user
		# 	user_checkout.save()
		# 	print("user checkout/braintree billing profile created.")
		# 	context["client_token"] = user_checkout.get_client_token()
		# 	self.request.session["user_checkout_id"] = user_checkout.id
		return context

	# def post(self, request, *args, **kwargs):
	# 	self.object = self.get_object()
	# 	form = self.get_form()
	# 	if form.is_valid():
	# 		email = form.cleaned_data.get("email")
	# 		user_checkout, created = UserCheckout.objects.get_or_create(email=email)
	# 		request.session["user_checkout_id"] = user_checkout.id
	# 		return self.form_valid(form)
	# 	else:
	# 		return self.form_invalid(form)


class CartPickupView(SingleObjectMixin, View):
	model = Cart
	template_name = "carts/pickup-view.html"

	def get_object(self, *args, **kwargs):
		self.request.session.set_expiry(0) #5 minutes
		cart_id = self.request.session.get("cart_id")
		if cart_id == None:
			cart = Cart()
			cart.tax_percentage = 0.075
			cart.save()
			cart_id = cart.id
			self.request.session["cart_id"] = cart_id
		cart = Cart.objects.get(id=cart_id)
		if self.request.user.is_authenticated:
			cart.user = self.request.user
			cart.save()
		return cart

	def get(self, request, *args, **kwargs):
		cart = self.get_object()
		pickup_date_time_id = request.GET.get("pickup-date-time")
		print('pickup_date_time', pickup_date_time_id)
		#delete_time = request.GET.get("delete", False)
		flash_message = ""
		time_added = False
		qs = CartTime.objects.carttime_exists(cart) 
		if qs.exists():
			print('a carttime object exists...shoudl delete the old one...creation...')
			""" this means a time has already been attached to the cart... you may
			want to delete the previous one.
			"""
			existing_carttime_obj = qs.last()
			print(existing_carttime_obj)
			existing_carttime_obj.active = False
			print(existing_carttime_obj.active)
			existing_carttime_obj.save()
		if pickup_date_time_id:
			print('firing')
			pickup_instance = get_object_or_404(PickupTime, id=pickup_date_time_id)
			#print(pickup_instance)
			#cart_item, created = CartItem.objects.get_or_create(cart=cart, item=item_instance)
			cart_time, created = CartTime.objects.get_or_create(cart=cart, pickup_time=pickup_instance)
			if created:
				# return email
				print('creating carttime fromcartpickupview...')
				#messages.success(request, "You have selected a pickup time! Now start browsing our selection!")
				flash_message = "Successfully added a pickup time to the cart!"
				time_added = True
				pickup_instance.count += 1 #when user selects a pickup time it created a cart time and adds +1 to pickup time count
				pickup_instance.save()
				cart_time.save()
			# if delete_time:
			# 	flash_message = "Pickup time removed successfully!"
			# 	cart_time.delete()
			else:
				# qs = CartTime.objects.carttime_exists(cart) 
				# if qs.exists():
				# 	print('a carttime object exists...shoudl delete the old one...')
				# 	""" this means a time has already been attached to the cart... you may
				# 	want to delete the previous one.
				# 	"""
				# 	existing_carttime_obj = qs.first()
				# 	print(existing_carttime_obj)
				# 	existing_carttime_obj.active = False
				# 	print(existing_carttime_obj.active)
				# 	existing_carttime_obj.save()
				print('saving...')
				flash_message = "Successfully added a pickup time to the cart!"
				#messages.success(request, "You have selected a pickup time! Now start browsing our selection!")
				cart_time.save()
			if not request.is_ajax():
				print('not created and not saving...')
				messages.success(request, "You have selected a pickup time! Now start browsing our selection!")
				return HttpResponseRedirect(reverse("products:product-variations-list"))
		
		if request.is_ajax():
			print('ajax request occuring...')
			try:
				pickup_date = cart_time.pickup_time.pickup_date
				print(pickup_date)
			except:
				pickup_date = None
				print(pickup_date)
			try:
				pickup_time = cart_time.pickup_time.timeslot
				print(pickup_time)
			except:
				pickup_time = None
				print(pickup_time)

			data = {
					#"deleted": delete_time,
					"pickup_date": pickup_date,
					"pickup_time": pickup_time,
					"time_added": time_added,
					"flash_message": flash_message,
					}

			return JsonResponse(data) 

		context = {
			"object": self.get_object(),
		}
		template = self.template_name
		return render(request, template, context)


def pickuptime_create(request):
	if not request.user.is_staff or not request.user.is_admin:
		raise Http404
		
	form = PickupTimeForm(request.POST or None)
	if form.is_valid():
		instance = form.save(commit=False)
		instance.user = request.user
		instance.save()
		# message success
		messages.success(request, "Successfully Created New Pickup Time.")
		#return HttpResponseRedirect(instance.get_absolute_url())
		return redirect("pickup_time_select")
	context = {
		"form": form,
	}
	return render(request, "carts/pickuptime_create.html", context)