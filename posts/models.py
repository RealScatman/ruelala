from django.conf import settings
#from django.core.urlresolvers import reverse
from django.urls import reverse
from django.db.models import Q
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.utils import timezone
from datetime import datetime, timedelta

from django.utils.text import slugify

#from tags.models import Tag

# Create your models here.

class PostQuerySet(models.query.QuerySet):
    def not_draft(self):
        return self.filter(draft=False)
    
    def published(self):
        return self.filter(publish__lte=timezone.now()).not_draft()

    def search(self, query):

        lookups = (Q(title__icontains=query) | 
                    Q(content__icontains=query) |
                    Q(tag__title__icontains=query)
                    )

        return self.filter(lookups).distinct()

class PostManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return PostQuerySet(self.model, using=self._db)
            
    def active(self, *args, **kwargs):
        # Post.objects.all() = super(PostManager, self).all()
        return self.get_queryset().published()

    def search(self, query):
        return self.get_queryset().published().search(query)

    def add_views(self, title):
        obj = self.model.objects.get(title=title)
        obj.views += 1
        obj.save()
        return obj

def upload_location(instance, filename):
    #filebase, extension = filename.split(".")
    #return "%s/%s.%s" %(instance.id, instance.id, extension)
    PostModel = instance.__class__
    new_id = PostModel.objects.order_by("id").last().id + 1
    #new_id = 2
    """
    instance.__class__ gets the model Post. We must use this method because the model is defined below.
    Then create a queryset ordered by the "id"s of each object, 
    Then we get the last object in the queryset with `.last()`
    Which will give us the most recently created Model instance
    We add 1 to it, so we get what should be the same id as the the post we are creating.
    """
    return "posts/%s/%s" %(new_id, filename)

def image_upload_to(instance, filename):
	title = instance.title
	slug = slugify(title)
	basename, file_extension = filename.split(".")
	new_filename = "%s-%s.%s" %(slug, instance.id, file_extension)
	return "posts/%s/%s" %(slug, new_filename)


class Post(models.Model):
    user 			= models.ForeignKey(settings.AUTH_USER_MODEL, default=1, on_delete=models.CASCADE)
    title 			= models.CharField(max_length=255)
    slug 			= models.SlugField(max_length=255, blank=True, unique=True)
    image 			= models.ImageField(upload_to=image_upload_to, 
            			null=True, 
            			blank=True, 
            			width_field="width_field", 
            			height_field="height_field")
    height_field 	= models.IntegerField(default=0)
    width_field 	= models.IntegerField(default=0)
    content 		= models.TextField()
    views           = models.IntegerField(default=0)
    draft 			= models.BooleanField(default=False)
    publish 		= models.DateField(auto_now=False, auto_now_add=False)
    updated 		= models.DateTimeField(auto_now=True, auto_now_add=False)
    timestamp 		= models.DateTimeField(auto_now=False, auto_now_add=True)
    featured        = models.BooleanField(default=False)

    objects = PostManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("posts:detail", kwargs={"slug": self.slug})
    
    def get_amp_url(self):
        return ('/news/amp/%s/' % (self.slug))
        
    # def get_date(self):
    #     fmt = '%Y-%m-%d'
    #     new_date = datetime.strptime(self.publish[:10], fmt)
    #     return new_date

    class Meta:
        ordering = ["-timestamp", "-updated"]

    # def get_image_url(self):
    #     img = self.image
    #     if img:
    #         return img.image.url
    #     return img #None


from ecommerce2.utils import unique_slug_generator

def pre_save_post_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        # instance.slug = create_slug(instance)
        instance.slug = unique_slug_generator(instance)


pre_save.connect(pre_save_post_receiver, sender=Post)