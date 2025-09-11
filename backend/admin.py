from django.contrib import admin
from .models import BlogModel , ContactModel
# Register your models here.

admin.site.register(BlogModel)
admin.site.register(ContactModel)