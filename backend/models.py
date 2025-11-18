from django.db import models
from django.utils.text import slugify 
from django.utils import timezone
import os


class BlogModel(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to="BlogImages/", blank=True, null=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while BlogModel.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    


class ContactModel(models.Model):
    your_name = models.CharField(max_length=255)
    your_email = models.EmailField()
    your_message = models.TextField()
    sended_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.your_name} - {self.your_email}"
    



class CarrierModel(models.Model):
    carrier_title = models.CharField(max_length=255)
    carrier_image = models.ImageField(upload_to="Admin/CarrierImages/", blank=True, null=True)
    deadline_date = models.DateField()
    description = models.TextField()
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.carrier_title)
            slug = base_slug
            counter = 1
            while CarrierModel.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.carrier_title
