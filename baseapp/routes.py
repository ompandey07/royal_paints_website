from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
urlpatterns = [

     # Home page    
     path('', views.index_page, name='index_page'),

     # Blog URLs
     path('blogs/', views.blogs_page, name='blogs_page'),
     path('blogs/<slug:slug>/', views.blog_detail, name='blog_detail'),

     # Other pages
     path('about/', views.abuot_page, name='about_page'),
               
]

# Serve static and media files during development (when DEBUG is True)
if settings.DEBUG:
    # Serve media files
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serve static files
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)