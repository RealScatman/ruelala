from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.generic import View, ListView
from django.shortcuts import render, redirect
from django.utils.http import is_safe_url
from django.template.loader import get_template

import datetime
import stripe

STRIPE_SECRET_KEY = getattr(settings, "STRIPE_SECRET_KEY", "XXX")
STRIPE_PUB_KEY = getattr(settings, "STRIPE_PUB_KEY", 'XXX')

stripe.api_key = STRIPE_SECRET_KEY

from .models import BillingProfile, Card

#from .utils import render_to_pdf #created in step 4

# class GeneratePdf(View):
# 	def get(self, request, *args, **kwargs):
# 		data = {
# 		'today': 'Today', 
# 		'amount': 39.99,
# 		'customer_name': 'Cooper Mann',
# 		'order_id': 1233434,
# 		}
# 		#print("get happening")
# 		pdf = render_to_pdf('pdf/invoice.html', data)
# 		print(data)
# 		return HttpResponse(pdf, content_type='application/pdf')

        # context = {
        #     "invoice_id": 117,
        #     "customer_name": "John J. Smith",
        #     "customer_email": "john.john.smith@gmail.com",
        #     "invoice_amount": "9,000.00",
        #     "invoice_time": datetime.date.today(),
        #     "invoice_memo": "Bill of Sale.",
        #     'download': True,
        # }


# class GeneratePDF(View):
#     def get(self, request, *args, **kwargs):
#         template = get_template('pdf/invoice.html')
#         #InvoicePDF.objects.get(id=self.id)
#         #kwargs={'order_id': self.order_id}
#         context = {
#             "invoice_id": 118,
#         }
#         html = template.render(context)
#         pdf = render_to_pdf('pdf/invoice.html', context)
#         if pdf:
#             response = HttpResponse(pdf, content_type='application/pdf')
#             filename = "Invoice_%s.pdf" %("BL118_04072019")
#             content = "inline; filename=%s" %(filename)
#             download = request.GET.get("download")
#             #print(download)
#             if download:
#                 content = "attachment; filename=%s" %(filename)
#             response['Content-Disposition'] = content
#             return response
#         return HttpResponse("Not found")



def payment_method_view(request):
	# if request.user.is_authenticated:
	# 	billing_profile = request.user.billingprofile
	# 	my_customer_id = billing_profile.customer_id

	billing_profile, billing_profile_created = BillingProfile.objects.new_or_get(request)
	if not billing_profile:
		return redirect("/account/checkout")
	next_url = None
	next_ = request.GET.get('next')
	if is_safe_url(next_, request.get_host()):
		next_url = next_
	return render(request, 'billing/payment-method.html', {"publish_key": STRIPE_PUB_KEY, "next_url": next_url})


def payment_method_createview(request):
	if request.method == "POST" and request.is_ajax():
		billing_profile, billing_profile_created = BillingProfile.objects.new_or_get(request)
		if not billing_profile:
			return HttpResponse({"message": "Cannot find this user"}, status_code=401)
		#print(request.POST)
		token = request.POST.get("token")
		if token is not None:
			#customer = stripe.Customer.retrieve(billing_profile.customer_id)
			#card_response = customer.sources.create(source=token)
			#new_card_obj = Card.objects.add_new(billing_profile, card_response)
			new_card_obj = Card.objects.add_new(billing_profile, token)
			# print(new_card_obj) # start saving our cards too!
		return JsonResponse({"message": "Success! Your card was added."})
	return HttpResponse("error", status_code=401)

# class InvoiceListView(LoginRequiredMixin, ListView):
# 	def get_queryset(self):
# 		return InvoicePDF.objects.all()