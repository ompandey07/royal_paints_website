from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

# ======================================================================
# FRONTEND/PUBLIC URL PATTERNS
# ======================================================================

urlpatterns = [
    # ==================== HOMEPAGE URLS ====================
    # Home page - Main landing page for visitors    
    path('', views.index_page, name='index_page'),

    # ==================== BLOG URLS ====================
    # Blog listing page - Shows all published blogs
    path('blogs/', views.blogs_page, name='blogs_page'),
    
    # Example: /blogs/my-blog-post-title/
    path('blogs/<slug:slug>/', views.blog_detail, name='blog_detail'),


    path('careers/', views.carriers_page, name='carriers_page'),
    path('career/<slug:slug>/', views.carrier_detail, name='carrier_detail'),

    # ==================== STATIC PAGES URLS ====================
    # About page - Company/organization information
    path('about/', views.about_page, name='about_page'),

    # Services page - Company/organization services
    path('services/', views.services_page, name='services_page'),

    # Contacts page - Company/organization contact information
    path('contacts/', views.contacts_page, name='contacts_page'),
]

# ======================================================================
# STATIC AND MEDIA FILES CONFIGURATION
# ======================================================================

# Serve static and media files during development (when DEBUG is True)
if settings.DEBUG:
    # Serve media files (user uploads, blog images, documents)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serve static files (CSS, JS, fonts, static images)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)