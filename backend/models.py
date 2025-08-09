from django.db import models
from django.utils.text import slugify
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
    


class MailModel(models.Model):
    subject = models.CharField(max_length=200)
    content = models.TextField()
    signature = models.TextField(blank=True, null=True)
    template = models.FileField(upload_to="MailTemplates/", blank=True, null=True)
    selected_for = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.subject

    def delete(self, *args, **kwargs):
        # Delete the template file when deleting the mail
        if self.template:
            if os.path.isfile(self.template.path):
                os.remove(self.template.path)
        super().delete(*args, **kwargs)


