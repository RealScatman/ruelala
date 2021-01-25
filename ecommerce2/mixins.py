from django.utils.http import is_safe_url
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404

class RequestFormAttachMixin(object):
	def get_form_kwargs(self):
		kwargs = super(RequestFormAttachMixin, self).get_form_kwargs()
		#print(kwargs)
		kwargs['request'] = self.request
		return kwargs

	
class NextUrlMixin(object):
	default_next = "/"
	def get_next_url(self):
		request = self.request
		print(request)
		next_ = request.GET.get('next')
		next_post = request.POST.get('next')
		print(next_)
		print(next_post)
		redirect_path = next_ or next_post or None
		print(redirect_path)
		if is_safe_url(redirect_path, request.get_host()):
			print("getting hit")
			return redirect_path
		return self.default_next


class LoginRequiredMixin(object):
	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class StatffRequiredMixin(object):
	@method_decorator(staff_member_required)
	def dispatch(self, request, *args, **kwargs):
		return super(StatffRequiredMixin, self).dispatch(request, *args, **kwargs)