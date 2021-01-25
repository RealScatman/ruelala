import datetime
from django.conf import settings
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
#from django.core.urlresolvers import reverse, reverse_lazy
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, FormView, DetailView, View, UpdateView, ListView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormMixin
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import is_safe_url
from django.utils.safestring import mark_safe


from ecommerce2.mixins import NextUrlMixin, RequestFormAttachMixin
from .models import GuestEmail, BoxSelection, Subscription #, EmailActivation,
from .forms import LoginForm, RegisterForm, GuestForm, RegisterLiteForm, UserDetailChangeForm #, DeliveryFrequencyForm #, ReactivateEmailForm, UserDetailChangeForm, UserSubscriptionForm

from addresses.models import Address, DeliveryFrequency
from addresses.forms import AddressForm, DeliveryFrequencyForm
from billing.models import BillingProfile
from orders.models import StripeOrder
from carts.models import Cart, CartItem ## added to allow a cart to be updated on the my accoutn user home screen...

from .signals import user_logged_in

from products.models import ProductFeatured, Variation
from accounts.models import User
# Create your views here.

import stripe
STRIPE_SECRET_KEY = getattr(settings, "STRIPE_SECRET_KEY", "sk_test_JFjBn2uw3wddd628ufbiJXcK")

STRIPE_PUB_KEY = getattr(settings, "STRIPE_PUB_KEY", 'pk_test_ps9Y4To7EPxSBEd6PkaUbiki')

stripe.api_key = STRIPE_SECRET_KEY

def box_detail_api_view(request):
    box_obj, new_obj = BoxSelection.objects.new_or_get(request)
    if box_obj.subscription is None:
        box_data = {"subscription": '', "subtotal": box_obj.subtotal, "total": box_obj.total}
    else:
        subscription = [{
                "id": box_obj.subscription.id,
                #"url": box_obj.subscription.get_absolute_url(),
                "image": box_obj.subscription.image.url,
                "title": box_obj.subscription.title,
                "price": box_obj.subscription.price
                }
                ] # [<object>, <object>]
        box_data = {"subscription": subscription, "subtotal": box_obj.subscription.price, "total": box_obj.total}
    return JsonResponse(box_data)

def box_update(request):
    subscription_id = request.POST.get('subscription_id')
    print(subscription_id)

    if subscription_id is not None:
        try:
            sub_obj = Subscription.objects.get(id=subscription_id)
            print(sub_obj)
        except Subscription.DoesNotExist:
            print("Show message to user, subscription box is gone?")
            return redirect("account:subscription-list")
        box_obj, new_obj = BoxSelection.objects.new_or_get(request)
        print(box_obj, new_obj)
        #print(box_obj)
        if box_obj.subscription is not None:
            box_obj.subscription = None
            added = False
            box_count = 0
            box_obj.subtotal = 0
            box_obj.save()
            request.session['box_items'] = 0
            request.session['box_subtotal'] = 0
        else:
            box_obj.subscription = sub_obj # cart_obj.products.add(product_id)
            added = True
            box_count = 1
            box_obj.subtotal = int(box_obj.subscription.price)
            box_obj.save()
            request.session['box_items'] = 1
            request.session['box_subtotal'] = int(box_obj.subscription.price)
        if request.is_ajax(): # asynchronous JavaScript and XML / JSON
            # print("Ajax request")
            json_data = {
                "added": added,
                "removed": not added,
                "boxItemCount": box_count,
                "boxSubtotal": box_obj.subtotal,
            }
            return JsonResponse(json_data) # default status is 200; # HttpResponse status_code=400
            # return JsonResponse({"message": "Error 400"}, status=400) # Django Rest Framework

    return redirect("account:subscription-list")

def checkout_home(request):
    #cart_obj, cart_created = Cart.objects.new_or_get(request)
    box_obj, box_created = BoxSelection.objects.new_or_get(request)
    register_email_id = request.session.get('register_email_id', None)
    register_email_obj = User.objects.get(id=register_email_id)
    #print(register_email_id)
    #print(register_email_obj)
    if register_email_obj is not None:
        #box_update = BoxSelection.objects.update(user=register_email_obj)
        box_obj.user = register_email_obj
        box_obj.save()
        #return box_obj
        #box_obj, box_created = BoxSelection.objects.new_or_get(request)
        # updated = True
        # print(updated)
        # return updated
    order_obj = None
    if box_created or box_obj.subscription is None:
        return redirect("account:subscription-list")
        

    #login_form = LoginForm(request=request)
    #guest_form = GuestForm(request=request)
    #register_form = RegisterForm(request=request)
    del_freq_form = DeliveryFrequencyForm()
    address_form = AddressForm()

    delivery_start_delivery_id = request.session.get("delivery_start_delivery_id", None)
    print(delivery_start_delivery_id)
    
    billing_address_id = request.session.get("billing_address_id", None)

    #shipping_address_required = not cart_obj.is_digital

    shipping_address_id = request.session.get("shipping_address_id", None)

    billing_profile, billing_profile_created = BillingProfile.objects.new_or_get(request)

    address_qs = None
    has_card = False
    if billing_profile is not None:
        print('getting hit...')
        # if request.user.is_authenticated:
        # 	address_qs = Address.objects.filter(billing_profile=billing_profile)
        if box_obj.user is not None:
            address_qs = Address.objects.filter(billing_profile=billing_profile)
        #order_obj, order_obj_created = Order.objects.new_or_get(billing_profile, cart_obj)
        order_obj, order_obj_created = StripeOrder.objects.new_or_get(billing_profile, box_obj)
        if shipping_address_id:
            order_obj.shipping_address = Address.objects.get(id=shipping_address_id)
            del request.session["shipping_address_id"]
        if billing_address_id:
            order_obj.billing_address = Address.objects.get(id=billing_address_id)
            del request.session["billing_address_id"]
        if delivery_start_delivery_id:
            order_obj.delivery_frequency = DeliveryFrequency.objects.get(id=delivery_start_delivery_id)
            print(delivery_start_delivery_id)
            del request.session["delivery_start_delivery_id"]
            order_obj.save()
        if billing_address_id or shipping_address_id:
            order_obj.save()
        has_card = billing_profile.has_card


    #New Code
    # if cart_obj.is_digital:
    # 	if request.method == "POST":
    # 		is_prepared = order_obj.check_done()
    # 		if is_prepared:
    # 			#did_charge, crg_msg = billing_profile.charge(order_obj)
    # 			did_charge, crg_msg = billing_profile.subscribe(order_obj) # new subscribe function to create subscribe object
    # 			if did_charge:
    # 				order_obj.mark_paid() # sort of a signal for us
    # 				#order_obj.send_order_id() # trigger the send email method on orders
    # 				billing_profile.user.set_paid_member() # mark the user as subscription member
    # 				#print(billing_profile.user.set_paid_member)
    # 				request.session['cart_items'] = 0
    # 				del request.session['cart_id']
    # 				if not billing_profile.user:
    # 					# is this this best place for this
    # 					billing_profile.set_cards_inactive()
    # 				return redirect("cart:success")
    # 			else:
    # 				print(crg_msg)
    # 				return redirect("cart:checkout")


    if request.method == "POST":
        is_prepared = order_obj.check_done()
        print(is_prepared)
        if is_prepared:
            #did_charge, crg_msg = billing_profile.charge(order_obj) switch to subscribe create
            did_charge, crg_msg = billing_profile.subscribe(order_obj)
            if did_charge:
                order_obj.mark_paid() # sor of a signal for us
                #order_obj.send_order_id() # trigger the send email method on orders
                billing_profile.user.set_paid_member() # mark the user as subscription member
                request.session['box_items'] = 0
                del request.session['box_id']
                if not billing_profile.user:
                    # is this this best place for this
                    billing_profile.set_cards_inactive()
                return redirect("accounts:success")
            else:
                print(crg_msg)
                return redirect("accounts:checkout")

    context = {
        "object": order_obj,
        "box": box_obj,
        "billing_profile": billing_profile,
        "del_freq_form": del_freq_form,
        #"login_form": login_form,
        #"guest_form": guest_form,
        #"register_form": register_form,
        "address_form": address_form,
        "address_qs": address_qs,
        "has_card": has_card,
        "publish_key": STRIPE_PUB_KEY,
        #"shipping_address_required": shipping_address_required,


    }
    return render(request, "accounts/box-checkout.html", context)

# def box_home(request):
# 	box_obj, new_obj = BoxSelection.objects.new_or_get(request)
# 	title = "Beaker.Life"
# 	print(box_obj)
# 	#quantity_form = QuantityForm(request.POST or None)
# 	return render(request, "accounts/box-home.html", {"box": box_obj, "title": title })

def checkout_done_view(request):
    queryset = StripeOrder.objects.all().first()
    context = {
        'object_list': queryset,
    }
    #print(queryset)	
    #print(context)
    #qs2 = Subscription.objects.all()

    # for p in qs2:
    # 	if p.quantity != 1:
    # 		p.quantity = 1
    # 		p.save()
    # 	else:
    # 		p.quantity = p.quantity
    #return qs2

    return render(request, "accounts/checkout-done.html", context)

def checkout_delivery_frequency_create_view(request):
    form = DeliveryFrequencyForm(request.POST or None)
    context = {
        "form": form
    }
    next_ = request.GET.get('next')
    next_post = request.POST.get('next')
    redirect_path = next_ or next_post or None
    print("delivery_frequency getting triggered...")
    print(request.POST)

    instance = form.save(commit=False)
    billing_profile, billing_profile_created = BillingProfile.objects.new_or_get(request)
    print(billing_profile)
    print(billing_profile_created)
    if billing_profile is not None:
        delivery_frequency = request.POST.get('delivery_frequency')
        #address_type = request.POST.get('address_type', 'shipping')
        instance.billing_profile = billing_profile
        print("also getting hit...")
        print(instance.billing_profile)
        instance.delivery_frequency = delivery_frequency
        #instance.address_type = address_type
        instance.save()
        #request.session[address_type + "_address_id"] = instance.id
        request.session[delivery_frequency + "_id"] = instance.id
        
        print(delivery_frequency + "_address_id")

        if is_safe_url(redirect_path, request.get_host()):
            return redirect(redirect_path)

    # if form.is_valid():
    # 	print(request.POST)
    # 	instance = form.save(commit=False)
    # 	billing_profile, billing_profile_created = BillingProfile.objects.new_or_get(request)
    # 	if billing_profile is not None:
    # 		delivery_frequency = request.POST.get('delivery_frequency')
    # 		#address_type = request.POST.get('address_type', 'shipping')
    # 		instance.billing_profile = billing_profile
    # 		print("also getting hit...")
    # 		print(instance.billing_profile)
    # 		instance.delivery_frequency = delivery_frequency
    # 		#instance.address_type = address_type
    # 		instance.save()
    # 		#request.session[address_type + "_address_id"] = instance.id
    # 		request.session[delivery_frequency + "_id"] = instance.id
            
    # 		print(delivery_frequency + "_address_id")
    # 		#print(address_type + "_address_id")
    # 		#billing_address_id = request.session.get("billing_address_id", None)
    # 		#shipping_address_id = request.session.get("shipping_address_id", None)
    # 	else:
    # 		print("Error Message")
    # 		return redirect("accounts:checkout")

    # 	if is_safe_url(redirect_path, request.get_host()):
    # 		return redirect(redirect_path)


    return redirect("accounts:checkout") 

class BoxHomeView(NextUrlMixin, RequestFormAttachMixin, CreateView):
    form_class = RegisterLiteForm
    default_next = '/account/checkout/'
    template_name = 'accounts/box-home.html'

    def get_success_url(self):
        request = self.request
        messages.success(request, "You have created an account successfully! Now provide your delivery address and select your delivery frequency!")
        return self.get_next_url()

    def get_context_data(self, *args, **kwargs):
        context = super(BoxHomeView, self).get_context_data(*args, **kwargs)
        title = "Beaker.Life"
        box_obj, new_obj = BoxSelection.objects.new_or_get(self.request)
        context['box'] = box_obj
        context['title'] = title
        return context


class GuestRegisterView(NextUrlMixin, RequestFormAttachMixin, CreateView):
    form_class = GuestForm
    default_next = '/register/'

    def get_success_url(self):
        return self.get_next_url()

    def form_invalid(self, form):
        return redirect(self.default_next)

    def form_valid(self, form):
        request 		= self.request
        email	 		= form.cleaned_data.get("email")
        new_guest_email = GuestEmail.objects.create(email=email)

        request.session['guest_email_id'] = new_guest_email.id
        return redirect(self.get_next_url())

class SubscriptionListView(ListView):
    queryset = Subscription.objects.all()
    #default_next = '/account/subscriptions/setup/'
    template_name = "accounts/subscription_list.html"

    def get_context_data(self, *args, **kwargs):
        context = super(SubscriptionListView, self).get_context_data(*args, **kwargs)
        box_obj, new_obj = BoxSelection.objects.new_or_get(self.request)
        context['box'] = box_obj
        return context

    def get_queryset(self, *args, **kwargs):
        qs = super(SubscriptionListView, self).get_queryset(*args, **kwargs)
        return qs

    # def get_success_url(self):
    # 	request = self.request
    # 	messages.success(request, "Great Selection!")
    # 	return self.get_next_url()


class LoginView(NextUrlMixin, RequestFormAttachMixin, FormView): 
    form_class = LoginForm
    success_url = '/products/variations/'
    template_name = 'accounts/login.html'
    default_next = '/products/variations/'

    # def get_form_kwargs(self):
    # 	kwargs = super(LoginView, self).get_form_kwargs()
    # 	# print(kwargs)
    # 	kwargs['request'] = self.request
    # 	return kwargs

    # def get_next_url(self):
    # 	request = self.request
    # 	next_ = request.GET.get('next')
    # 	next_post = request.POST.get('next')
    # 	redirect_path = next_ or next_post or None
    # 	if is_safe_url(redirect_path, request.get_host()):
    # 			return redirect_path
    # 	return "/"

    def form_valid(self, form):
        #request = self.request
        #email = form.cleaned_data.get("email")
        #password = form.cleaned_data.get("password")
        #user = authenticate(request, username=email, password=password)
        next_path = self.get_next_url()
        return redirect(next_path)


class RegisterView(NextUrlMixin, RequestFormAttachMixin, CreateView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = '/login/'
    default_next = '/login/'

    # def form_valid(self, form):   
    #     next_path = self.get_next_url()
    #     return redirect(next_path)

    def get_success_url(self):
        #next_path = self.get_next_url()
        request = self.request
        #print(next_path)
        #return redirect(next_path)
        messages.success(request, "You have registered an account successfully! Please login below to continue your order.")
        return self.get_next_url()
        #return HttpResponseRedirect(next_path)


class MyHomeDetailView(SingleObjectMixin, LoginRequiredMixin, View):
    model = Cart #BillingProfile
    #queryset = BillingProfile.objects.filter(user=request.user)
    #default_next = '/account/subscriptions/setup/'
    template_name = "accounts/user-home.html"

    # def get_queryset(self, *args, **kwargs):
    #     qs = super(MyHomeDetailView, self).get_queryset(*args, **kwargs)
    #     qs = qs.filter(user=self.request.user)
    #     #print(qs)
    #     #print(qs.first())
    #     #obj = qs.first()
    #     #print(obj.deliveryfrequency_set)
    #     return qs.first()

    # def get_context_data(self, *args, **kwargs):
    #     context = super(MyHomeDetailView, self).get_context_data(*args, **kwargs)
    #     #box_obj, new_obj = BoxSelection.objects.new_or_get(self.request)
    #     upcoming_order_qs = StripeOrder.objects.by_request(self.request).not_created()
    #     billing_qs = BillingProfile.objects.filter(user=self.request.user)
    #     print(billing_qs)
    #     billing_obj = billing_qs.first()
    #     #context['box'] = box_obj
    #     upcoming_order_obj = upcoming_order_qs.first()
    #     #print(upcoming_order_obj)
    #     #print(upcoming_order_obj.box.subscription.products.all())
    #     my_order_products = upcoming_order_obj.box.subscription.products.all()
    #     context['object_list'] = billing_qs
    #     context['object'] = self.get_object()
    #     context['upcoming_order'] = upcoming_order_obj
    #     context['my_order_products'] = my_order_products
    #     return context

    def get_object(self, *args, **kwargs):
        self.request.session.set_expiry(0) #5 minutes
        cart_id = self.request.session.get("cart_id")
        if cart_id == None:
            print("cart is none...")
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
                flash_message = "Successfully added to the cart"
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
                print("error here...")
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
        upcoming_order_qs = StripeOrder.objects.by_request(self.request).not_created()
        billing_qs = BillingProfile.objects.filter(user=self.request.user)
        box_obj, new_obj = BoxSelection.objects.new_or_get(self.request)
        print(box_obj)
        print(billing_qs)
        billing_obj = billing_qs.first()
        #context['box'] = box_obj
        upcoming_order_obj = upcoming_order_qs.first()
        #print(upcoming_order_obj)
        #print(upcoming_order_obj.box.subscription.products.all())
        my_order_products = upcoming_order_obj.box.subscription.products.all()

        context = {
            "object": self.get_object(),
            "object_list":  billing_obj,
            "box": box_obj,
            "upcoming_order":  upcoming_order_obj,
            "my_order_products":  my_order_products,
        }
        
        template = self.template_name
        
        return render(request, template, context)


class UserDetailUpdateView(LoginRequiredMixin, UpdateView):
    form_class = UserDetailChangeForm
    template_name = 'accounts/detail-update-view.html'

    def get_object(self):
        return self.request.user

    def get_context_data(self, *args, **kwargs):
        context = super(UserDetailUpdateView, self).get_context_data(*args, **kwargs)
        context['title'] = 'Change Account User Details'
        return context

    def get_success_url(self):
        request = self.request
        messages.success(request, "You have updated your account successfully!")
        return reverse("home")