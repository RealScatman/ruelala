import datetime
import calendar
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, UpdateView, CreateView, FormView, DetailView
#from django.core.urlresolvers import reverse
from django.urls import reverse
from django.shortcuts import render, redirect
from django.utils.http import is_safe_url
from django.http import Http404

#from calendar import HTMLCalendar
from django.utils.safestring import mark_safe
# Create your views here.

from delivery.models import DeliveryZipCode
from billing.models import BillingProfile
from .forms import AddressCheckoutForm, AddressForm, DeliveryFrequencyForm #added address checkoutform
from .models import Address, DeliveryFrequency

from .utils import Calendar, MyCalendar


class AddressListView(LoginRequiredMixin, ListView):
    template_name = 'addresses/list.html'

    def get_queryset(self):
        request = self.request
        billing_profile, billing_profile_created = BillingProfile.objects.new_or_get(request)
        return Address.objects.filter(billing_profile=billing_profile)


class AddressUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'addresses/update.html'
    form_class = AddressForm
    success_url = '/addresses'

    def get_queryset(self):
        request = self.request
        billing_profile, billing_profile_created = BillingProfile.objects.new_or_get(request)
        return Address.objects.filter(billing_profile=billing_profile)


class AddressCreateView(LoginRequiredMixin, CreateView):
    template_name = 'addresses/update.html'
    form_class = AddressForm
    success_url = '/addresses'

    def form_valid(self, form):
        request = self.request
        billing_profile, billing_profile_created = BillingProfile.objects.new_or_get(request)
        instance = form.save(commit=False)
        instance.billing_profile = billing_profile
        instance.save()
        return super(AddressCreateView, self).form_valid(form)


# Old code below

def checkout_address_create_view(request):
    form = AddressForm(request.POST or None)
    context = {
        "form": form
    }
    next_ = request.GET.get('next')
    next_post = request.POST.get('next')
    redirect_path = next_ or next_post or None

    if form.is_valid():
        zipcode = request.POST.get('postal_code')
        delivery_obj = DeliveryZipCode.objects.zipcode_exists(zipcode).first()
        print(delivery_obj)
        # if delivery_obj is not None:
        # 	delivery_day = delivery_obj.delivery_day
        print(request.POST)
        instance = form.save(commit=False)
        billing_profile, billing_profile_created = BillingProfile.objects.new_or_get(request)
        if billing_profile is not None:
            address_type = request.POST.get('address_type', 'shipping')
            instance.billing_profile = billing_profile
            instance.address_type = address_type
            if delivery_obj is not None:
                instance.delivery_day = delivery_obj
            else:
                pass
            instance.save()
            request.session[address_type + "_address_id"] = instance.id
            
            print(address_type + "_address_id")
            #billing_address_id = request.session.get("billing_address_id", None)
            #shipping_address_id = request.session.get("shipping_address_id", None)
        else:
            print("Error Message")
            return redirect("box:checkout")

        if is_safe_url(redirect_path, request.get_host()):
            return redirect(redirect_path)


    return redirect("accounts:checkout") 


def checkout_address_reuse_view(request):
    if request.user.is_authenticated():
        context = {}
        next_ = request.GET.get('next')
        next_post = request.POST.get('next')
        redirect_path = next_ or next_post or None
        if request.method == "POST":
            #print(request.POST)
            shipping_address = request.POST.get('shipping_address', None)
            address_type = request.POST.get('address_type', 'shipping')
            billing_profile, billing_profile_created = BillingProfile.objects.new_or_get(request)
            if shipping_address is not None:
                qs = Address.objects.filter(billing_profile=billing_profile, id=shipping_address)
                if qs.exists():
                    request.session[address_type + "_address_id"] = shipping_address

                if is_safe_url(redirect_path, request.get_host()):
                    return redirect(redirect_path)


    return redirect("accounts:checkout") 



def checkout_deliveryfrequency_create_view(request):
    form = DeliveryFrequencyForm(request.POST or None)
    context = {
        "form": form
    }
    next_ = request.GET.get('next')
    next_post = request.POST.get('next')
    redirect_path = next_ or next_post or None
    print("delivery frequency getting hit")

    if form.is_valid():
        print(request.POST)
        instance = form.save(commit=False)
        billing_profile, billing_profile_created = BillingProfile.objects.new_or_get(request)
        if billing_profile is not None:
            #address_type = request.POST.get('address_type', 'shipping')
            delivery_start = request.POST.get('delivery_start')
            instance.billing_profile = billing_profile
            #instance.address_type = address_type
            instance.delivery_start = delivery_start
            instance.save()
            #request.session[address_type + "_address_id"] = instance.id
            request.session["delivery_start" + "_delivery_id"] = instance.id
            
            #print(address_type + "_address_id")
            print("delivery_start" + "_delivery_id")
            #billing_address_id = request.session.get("billing_address_id", None)
            #shipping_address_id = request.session.get("shipping_address_id", None)
        else:
            print("Error Message")
            return redirect("accounts:checkout")

        if is_safe_url(redirect_path, request.get_host()):
            return redirect(redirect_path)
    else:
        print("form isnt valid...")


    return redirect("accounts:checkout") 

class DeliveryFrequencyDetailView(LoginRequiredMixin, DetailView):
    template_name = 'addresses/delivery-detail.html'
    #form_class = DeliveryFrequencyForm
    success_url = '/account/subscriptions/home'

    # def get_queryset(self):
    # 	request = self.request
    # 	billing_profile, billing_profile_created = BillingProfile.objects.new_or_get(request)
    # 	return DeliveryFrequency.objects.filter(billing_profile=billing_profile)

    def get_object(self):
        request = self.request
        billing_profile, billing_profile_created = BillingProfile.objects.new_or_get(request)
        #qs = Order.objects.by_request(self.request).filter(order_id = self.kwargs.get('order_id'))
        qs = DeliveryFrequency.objects.filter(billing_profile=billing_profile)
        return qs.first()
        # if qs.count() == 1:
        #     return qs.first()
        # raise Http404

    def get_context_data(self, *args, **kwargs):
        context = super(DeliveryFrequencyDetailView, self).get_context_data(*args, **kwargs)
        # cal = HTMLCalendar()
        request = self.request
        billing_profile, billing_profile_created = BillingProfile.objects.new_or_get(request)
        print(billing_profile)
        qs = DeliveryFrequency.objects.filter(billing_profile=billing_profile)
        # if qs.count() == 1:
        #     del_obj = qs.first()
        del_obj = qs.first()
        #d = datetime.date.today()
        d = del_obj.delivery_start

        after_day = request.GET.get('day__gte', None)
        #extra_context = extra_context or {}
    
        if not after_day:
            #d = datetime.date.today()
            d = del_obj.delivery_start
        else:
            try:
                split_after_day = after_day.split('-')
                d = datetime.date(year=int(split_after_day[0]), month=int(split_after_day[1]), day=1)
                print(d)
            except:
                d = datetime.date.today()
                print(d)
        '''
        USE THIS Query as URL to switch months: http://127.0.0.1:8000/delivery/detail/?day__gte=2020-03
        '''
        previous_month = datetime.date(year=d.year, month=d.month, day=1)  # find first day of current month
        previous_month = previous_month - datetime.timedelta(days=1)  # backs up a single day
        previous_month = datetime.date(year=previous_month.year, month=previous_month.month,
                                       day=1)  # find first day of previous month
 
        last_day = calendar.monthrange(d.year, d.month)
        next_month = datetime.date(year=d.year, month=d.month, day=last_day[1])  # find last day of current month
        next_month = next_month + datetime.timedelta(days=1)  # forward a single day
        next_month = datetime.date(year=next_month.year, month=next_month.month,
                                   day=1)  # find first day of next month
 
        context['previous_month'] = reverse('delivery-detail') + '?day__gte=' + str(previous_month)
        context['next_month'] = reverse('delivery-detail') + '?day__gte=' + str(next_month)

        # qs = DeliveryFrequency.objects.filter(billing_profile=billing_profile)
        # if qs.count() == 1:
        #     del_obj = qs.first()
        # html_calendar = cal.formatmonth(d.year, d.month, withyear=True)
        # html_calendar = html_calendar.replace('<td ', '<td  width="150" height="150"')
        # context['calendar'] = mark_safe(html_calendar)
        # return context
        #d = get_date(self.request.GET.get('month', None))
        #cal = Calendar(d.year, d.month) # Master Cal for Admins
        #html_cal = cal.formatmonth(withyear=True) # Master Cal for Admins
        #context['calendar'] = mark_safe(html_cal) # Master Cal for Admins
        mycal = MyCalendar(billing_profile, d.year, d.month) #Singular Cal for users
        html_mycal = mycal.formatmonth(withyear=True)
        context['mycalendar'] = mark_safe(html_mycal)
        # context['prev_month'] = prev_month(d)
        # context['next_month'] = next_month(d)
        return context