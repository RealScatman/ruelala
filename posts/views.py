try:
    from urllib.parse import quote_plus #python 3
except: 
    pass

from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.utils import timezone

from .forms import PostForm
from newsletter.forms import SignUpForm
from .models import Post

def post_create(request, type):
	if not request.user.is_staff or not request.user.is_admin:
		raise Http404
		
	form = PostForm(request.POST or None, request.FILES or None)
	if form.is_valid():
		instance = form.save(commit=False)
		instance.user = request.user
		instance.save()
		# message success
		messages.success(request, "Successfully Created")
		return HttpResponseRedirect(instance.get_absolute_url())
	context = {
		"form": form,
	}
	return render(request, "posts/post_form.html", context)

def post_list(request, type):
	featured_posts = Post.objects.filter(featured=True)
	today = timezone.now().date()
	queryset_list = Post.objects.active() #.order_by("-timestamp")
	try:
		if request.user.is_staff or request.user.is_admin:
			queryset_list = Post.objects.all()
	except:
		pass
	query = request.GET.get("q")
	if query:
		queryset_list = queryset_list.filter(
				Q(title__icontains=query)|
				Q(content__icontains=query)|
				Q(user__email__icontains=query)
				).distinct()
	paginator = Paginator(queryset_list, 8) # Show 25 contacts per page
	page_request_var = "page"
	page = request.GET.get(page_request_var)
	try:
		queryset = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer, deliver first page.
		queryset = paginator.page(1)
	except EmptyPage:
		# If page is out of range (e.g. 9999), deliver last page of results.
		queryset = paginator.page(paginator.num_pages)
	
	form = SignUpForm(request.POST or None)

	context = {
		"signup_title": "Signup for our Newsletter!",
		"object_list": queryset,
		"featured_posts": featured_posts, 
		"title": "Latest News & Events",
		"page_request_var": page_request_var,
		"today": today,
		"form": form,
	}

	if form.is_valid():
		instance = form.save(commit=False)
		full_name = form.cleaned_data.get("full_name")
		if not full_name:
			full_name = "New full name"
		instance.full_name = full_name
		instance.save()
		context = {
			"signup_title": "Thank you for signing up.",
			"signed_up": True,
			"object_list": queryset,
			"featured_posts": featured_posts, 
			"title": "Latest News",
			"page_request_var": page_request_var,
			"today": today,
		}

	return render(request, "posts/post_list.html", context)

def post_update(request, type, slug=None):
	if not request.user.is_staff or not request.user.is_admin:
		raise Http404
	instance = get_object_or_404(Post, slug=slug)
	form = PostForm(request.POST or None, request.FILES or None, instance=instance)
	if form.is_valid():
		instance = form.save(commit=False)
		instance.save()
		messages.success(request, "<a href='#'>Item</a> Saved", extra_tags='html_safe')
		return HttpResponseRedirect(instance.get_absolute_url())

	context = {
		"title": instance.title,
		"instance": instance,
		"form": form,
	}
	return render(request, "posts/post_form.html", context)

class PostDetailView(DetailView):
	template_name = 'posts/post_detail.html'

	def get_template_names(self, *args, **kwargs):
		#request = self.request
		#print(self.kwargs)
		template_type = self.kwargs.get("type")
		if template_type=="amp":
			template_name = 'posts/amp/post_detail.html'
		else:
			template_name = 'posts/post_detail.html'
		return template_name

	def dispatch(self, *args, **kwargs):
		type = self.kwargs.get("type")
		# if type=="amp":
		# 	template_name = ''
		# else:
		# 	template_name = 'posts/post_detail.html'
		return super(PostDetailView, self).dispatch(*args, **kwargs)

	def get_object(self, *args, **kwargs):
		slug = self.kwargs.get("slug")
		instance = get_object_or_404(Post, slug=slug)
		if instance.publish > timezone.now().date() or instance.draft:
			if not self.request.user.is_staff or not self.request.user.is_admin:
				raise Http404
		return instance
	
	def get_context_data(self, *args, **kwargs):
		context = super(PostDetailView, self).get_context_data(*args, **kwargs)
		request = self.request
		instance = self.get_object()
		if not request.user.is_staff or not request.user.is_admin:
			new_views = Post.objects.add_views(title=instance.title)
		else:
			new_views = instance.views
		top_posts = Post.objects.all()[:3]
		context["view_count"] = new_views
		context['share_string'] = quote_plus(instance.content)
		context["BASE_URL"] = "https://www.sample.link"
		context['top_posts'] = top_posts
		user = None
		if request.user.is_authenticated:
			user = request.user
		instance = context['object'] # is this needed??
		#print(context)
		return context