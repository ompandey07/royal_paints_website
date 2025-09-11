from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

# ======================================================================
# BACKEND/ADMIN URL PATTERNS
# ======================================================================

urlpatterns = [
    
    # ==================== AUTHENTICATION URLS ====================
    # Root URL - Login page (main entry point)
    path('login/', views.login_view, name='login_view'),
    
    # User logout functionality
    path('logout/', views.logout_view, name='logout_view'),
    
    # Unauthorized access error page
    path('unauthorized/', views.unauthorized_acess, name='unauthorized_acess'),

    # ==================== ADMIN DASHBOARD URLS ====================
    # Main admin dashboard after login
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # ==================== CONTENT MANAGEMENT URLS ====================
    # Blog posts creation, editing, and management
    path('manage-blogs/', views.manage_blogs, name='manage_blogs'),


               
]

# ======================================================================
# STATIC AND MEDIA FILES CONFIGURATION
# ======================================================================

# Serve static and media files during development (when DEBUG is True)
if settings.DEBUG:
    # Serve media files (user uploads, images, documents)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serve static files (CSS, JS, images, etc.)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)