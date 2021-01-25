from django.contrib.auth import get_user_model, authenticate, login, logout
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from rest_framework import serializers

from products.models import Product, Variation, Category, Size, Type, Availability


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'title',
            'description',
            'active',
            'slug',
            'id'
        ]

class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = [
            'title',
            'description',
            'active',
            'slug',
            'id'
        ]

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = [
            'title',
            'description',
            'active',
            'slug',
            'id'
        ]

class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = [
            'title',
            'description',
            'active',
            'slug',
            'id'
        ]

class ProductSerializer(serializers.ModelSerializer):
    # url             = serializers.HyperlinkedIdentityField(
    #                         view_name='posts-api:detail',
    #                         lookup_field='slug'
    #                         )
    #user            = UserPublicSerializer(read_only=True)
    #publish_date    = serializers.DateField(default=timezone.now())
    image_url       = serializers.SerializerMethodField()
    #owner           = serializers.SerializerMethodField(read_only=True)
    categories      = CategorySerializer(many=True, read_only=True)
    default         = CategorySerializer(read_only=True)
    type            = TypeSerializer(read_only=True)
    #game            = serializers.SerializerMethodField(read_only=True)
    #video           = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            #'url',
            'slug',
            #'user',
            'title',
            'description',
            'price',
            'type',
            #'make_published',
            #'publish_date',
            #'featured',
            #'feature_color',
            #'game',
            #'video',
            'categories',
            'default',
            'image_url',
            #'updated',
            #'owner',
            #'timestamp',
        ]
    # def get_owner(self, obj):
    #     #print(self.context)
    #     request = self.context['request']
    #     if request.user.is_authenticated:
    #         if obj.user == request.user:
    #             return True
    #     return False


    def get_image_url(self, obj):
        img = obj.productimage_set.first()
        #print(img)
        if img:
            image_url =  img.image.url
            return image_url
        return "No Image Provided"


class ProductInlineSerializer(serializers.ModelSerializer):
    # url             = serializers.HyperlinkedIdentityField(
    #                         view_name='products-api:detail',
    #                         #lookup_field='slug'
    #                         lookup_field='id'
    #                         )
    image_url       = serializers.SerializerMethodField()
    categories      = CategorySerializer(many=True, read_only=True)
    default         = CategorySerializer(read_only=True)
    type            = TypeSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            #'url',
            'id',
            'title',
            'slug',
            'image_url',
            'description',
            'price',
            'categories',
            'default',
            'type',
        ]
        #read_only_fields = ['user'] # GET
    
    def get_image_url(self, obj):
        img = obj.productimage_set.first()
        #print(img)
        if img:
            image_url =  img.image.url
            return image_url
        return "No Image Provided"

class VariationSerializer(serializers.ModelSerializer):
    url             = serializers.HyperlinkedIdentityField(
                            view_name='products-api:variation-detail',
                            lookup_field='pk'
                            )
    image_url         = serializers.SerializerMethodField()
    product           = serializers.SerializerMethodField(read_only=True)
    size              = SizeSerializer(read_only=True)
    availability      = AvailabilitySerializer(read_only=True)

    class Meta:
        model = Variation
        fields = [
            'url',
            'pk',
            'id',
            'active',
            'featured',
            'title',
            'slug',
            'image_url',
            'inventory',
            'size',
            'availability',
            'price',
            'sale_price',
            'product',
        ]

    def get_image_url(self, obj):
        if obj.image:
            image_url =  obj.image.url
            return image_url
        return "No Image Provided"

    def get_product(self, obj):
        request = self.context.get('request')
        limit = 10
        if request:
            limit_query = request.GET.get('limit')
            try:
                limit = int(limit_query)
            except:
                pass
        #qs = obj.product.active().order_by("title") #[:10]
        prod_obj = obj.product
        data = {
            #'uri': self.get_uri(obj) + "status/",
            'product_set': ProductInlineSerializer(prod_obj, context={'request': request}).data
        }
        return data