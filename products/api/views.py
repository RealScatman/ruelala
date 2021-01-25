#from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework import generics, permissions, pagination, filters
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
#from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters

from products.models import Product, Variation
from .permissions import IsOwnerOrReadOnly
from .serializers import ProductSerializer, VariationSerializer


class ProductPageNumberPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'size'
    max_page_size = 20

    def get_paginated_response(self, data):
        author = False
        user = self.request.user
        if user.is_authenticated:
            author = True
        context = {
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'author': author,
            'results': data,
        }
        return Response(context)

class VariationPageNumberPagination(pagination.PageNumberPagination):
    page_size = 12
    page_size_query_param = 'size'
    max_page_size = 20

    def get_paginated_response(self, data):
        author = False
        user = self.request.user
        if user.is_authenticated:
            author = True
        context = {
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'author': author,
            'results': data,
        }
        return Response(context)

class VariationFilter(filters.FilterSet):
	search = filters.CharFilter(field_name='product__title', lookup_expr='icontains', distinct=True)
	category = filters.CharFilter(field_name='product__categories__title', lookup_expr='icontains', distinct=True)
	category_id = filters.CharFilter(field_name='product__categories__id', lookup_expr='icontains', distinct=True)
	min_price = filters.NumberFilter(field_name='price', lookup_expr='gte', distinct=True) # (some_price__gte=somequery)
	max_price = filters.NumberFilter(field_name='price', lookup_expr='lte', distinct=True)
	size = filters.CharFilter(field_name='size__slug', lookup_expr='icontains', distinct=True)
	type = filters.CharFilter(field_name='product__type__id', lookup_expr='icontains', distinct=True)
	availability = filters.CharFilter(field_name='availability', lookup_expr='exact', distinct=True)

	class Meta:
		model = Variation
		fields = [
			'min_price',
			'max_price',
			'category',
			'type',
			'availability',
			'title',
			'search',
			'size',
		]

class ProductListCreateAPIView(generics.ListCreateAPIView):
    queryset                = Product.objects.all()
    serializer_class        = ProductSerializer
    #authentication_classes  = [JSONWebTokenAuthentication]
    #permission_classes      = [permissions.IsAuthenticated]
    permission_classes      = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class        = ProductPageNumberPagination
    filter_backends         = [filters.OrderingFilter]
    #ordering_fields         = ['views']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # def get_queryset(self, *args, **kwargs):
    #     featured = self.request.GET.get("featured")
    #     if featured and self.request.user.is_authenticated():
    #         return Post.objects.filter(featured=True)
    #     return Post.objects.none()

    def get_queryset(self):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        #queryset = Post.objects.all()
        queryset = Product.objects.all() #includes active filter (see ProductManager)
        # featured = self.request.query_params.get('featured', None)
        # if featured is not None and featured == 'true':
        #     queryset = queryset.filter(featured=True)

        # id  = self.request.query_params.get('id', None)
        # if id is not None:
        #     print('post API fetch by game id')
        #     queryset = queryset.filter(games=id)
        
        # slug  = self.request.query_params.get('slug', None)
        # if slug is not None:
        #     print('post API fetch by game slug')
        #     queryset = queryset.filter(games__slug=slug)

        # default = self.request.query_params.get('default', None)
        # if default is not None and default == '1':
        #     # print("getting hit")
        #     queryset = queryset.filter(default=1)
        # elif default is not None and default == '2':
        #     # print("also getting hit")
        #     queryset = queryset.filter(default=2)
        # category = self.request.query_params.get('category', None)
        # if category is not None and category == 'article':
        #     # print("getting hit")
        #     queryset = queryset.filter(default__slug='article')
        # elif category is not None and category == 'video':
        #     # print("also getting hit")
        #     queryset = queryset.filter(default__slug="video")
        return queryset

class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset            = Product.objects.all()
    serializer_class    = ProductSerializer
    lookup_field        = 'id'
    permission_classes  = [IsOwnerOrReadOnly]


    def get_serializer_context(self):
        context = super().get_serializer_context()
        instance = self.get_object()
        request = self.request
        context['request'] = self.request
        # if not request.user.is_authenticated:
        #     new_views = Post.objects.add_views(title=instance.title)
        #     print(new_views)
        # else:
        #     new_views = instance.views

        # context["view_count"] = new_views
        # if instance:
        #     if request.user.is_authenticated:
        #         if request.user.is_admin:
        #             pass
        #         else:
        #             object_viewed_signal.send(instance.__class__, instance=instance, request=request)
        #     else:
        #         object_viewed_signal.send(instance.__class__, instance=instance, request=request)
        return context


class VariationListCreateAPIView(generics.ListCreateAPIView):
    queryset                = Variation.objects.all()
    serializer_class        = VariationSerializer
    #authentication_classes  = [JSONWebTokenAuthentication]
    #permission_classes      = [permissions.IsAuthenticated]
    permission_classes      = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class        = VariationPageNumberPagination
    #filter_backends         = [filters.OrderingFilter]
    #filter_backends         = [DjangoFilterBackend]
    #filterset_fields        = ['product__category__icontains', 'featured']
    filter_backends         = (filters.DjangoFilterBackend,)
    filterset_class         = VariationFilter
    #ordering_fields         = ['views']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # def get_queryset(self, *args, **kwargs):
    #     featured = self.request.GET.get("featured")
    #     if featured and self.request.user.is_authenticated():
    #         return Post.objects.filter(featured=True)
    #     return Post.objects.none()

    def get_queryset(self):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        #queryset = Post.objects.all()
        queryset = Variation.objects.all() #includes active filter (see ProductManager)
        featured = self.request.query_params.get('featured', None)
        if featured is not None and featured == 'true':
            queryset = queryset.filter(featured=True)

        # id  = self.request.query_params.get('id', None)
        # if id is not None:
        #     print('post API fetch by game id')
        #     queryset = queryset.filter(games=id)
        
        slug  = self.request.query_params.get('slug', None)
        if slug is not None:
            #print('post API fetch by game slug')
            queryset = queryset.filter(product__slug__icontains=slug)

        # default = self.request.query_params.get('default', None)
        # if default is not None and default == '1':
        #     # print("getting hit")
        #     queryset = queryset.filter(default=1)
        # elif default is not None and default == '2':
        #     # print("also getting hit")
        #     queryset = queryset.filter(default=2)
        category = self.request.query_params.get('category', None)
        if category is not None and category == 'lagers':
            # print("getting hit")
            queryset = queryset.filter(product__default__slug='lagers')
        elif category is not None and category == 'ales':
            # print("also getting hit")
            queryset = queryset.filter(product__default__slug="ales")
        return queryset


class VariationDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset            = Variation.objects.all()
    serializer_class    = VariationSerializer
    lookup_field        = 'pk'
    #permission_classes  = [IsOwnerOrReadOnly]


    def get_serializer_context(self):
        context = super().get_serializer_context()
        instance = self.get_object()
        request = self.request
        context['request'] = self.request
        # if not request.user.is_authenticated:
        #     new_views = Post.objects.add_views(title=instance.title)
        #     print(new_views)
        # else:
        #     new_views = instance.views

        # context["view_count"] = new_views
        # if instance:
        #     if request.user.is_authenticated:
        #         if request.user.is_admin:
        #             pass
        #         else:
        #             object_viewed_signal.send(instance.__class__, instance=instance, request=request)
        #     else:
        #         object_viewed_signal.send(instance.__class__, instance=instance, request=request)
        return context



# class VariationListView2(generics.RetrieveAPIView):
#     """
#     A view that returns a templated HTML representation of a given user.
#     """
#     queryset = Variation.objects.all()
#     renderer_classes = [TemplateHTMLRenderer]

#     def get(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         return Response({'user': self.object}, template_name='user_detail.html')

class VariationListCreateAPIView2(generics.ListAPIView):
    queryset                = Variation.objects.all()
    serializer_class        = VariationSerializer
    #authentication_classes  = [JSONWebTokenAuthentication]
    #permission_classes      = [permissions.IsAuthenticated]
    renderer_classes        = [TemplateHTMLRenderer]
    permission_classes      = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class        = VariationPageNumberPagination
    #filter_backends         = [filters.OrderingFilter]
    #filter_backends         = [DjangoFilterBackend]
    #filterset_fields        = ['product__category__icontains', 'featured']
    filter_backends         = (filters.DjangoFilterBackend,)
    filterset_class         = VariationFilter
    #ordering_fields         = ['views']

    # def perform_create(self, serializer):
    #     serializer.save(user=self.request.user)

    # def get_queryset(self, *args, **kwargs):
    #     featured = self.request.GET.get("featured")
    #     if featured and self.request.user.is_authenticated():
    #         return Post.objects.filter(featured=True)
    #     return Post.objects.none()

    def get_queryset(self):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        #queryset = Post.objects.all()
        queryset = Variation.objects.all() #includes active filter (see ProductManager)
        featured = self.request.query_params.get('featured', None)
        if featured is not None and featured == 'true':
            queryset = queryset.filter(featured=True)

        # id  = self.request.query_params.get('id', None)
        # if id is not None:
        #     print('post API fetch by game id')
        #     queryset = queryset.filter(games=id)
        
        slug  = self.request.query_params.get('slug', None)
        if slug is not None:
            #print('post API fetch by game slug')
            queryset = queryset.filter(product__slug__icontains=slug)

        # default = self.request.query_params.get('default', None)
        # if default is not None and default == '1':
        #     # print("getting hit")
        #     queryset = queryset.filter(default=1)
        # elif default is not None and default == '2':
        #     # print("also getting hit")
        #     queryset = queryset.filter(default=2)
        category = self.request.query_params.get('category', None)
        if category is not None and category == 'lagers':
            # print("getting hit")
            queryset = queryset.filter(product__default__slug='lagers')
        elif category is not None and category == 'ales':
            # print("also getting hit")
            queryset = queryset.filter(product__default__slug="ales")
        #return queryset
        return queryset
        #return Response(queryset, template_name='products/home.html')

    def get(self, request, *args, **kwargs):
        self.query_set = self.get_queryset()
        print(self.query_set)
        #print(self.query_set.results)
        return Response({'object_list': self.query_set}, template_name='products/home.html')