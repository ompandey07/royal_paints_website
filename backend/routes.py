from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
urlpatterns = [
         
     path('', views.login_view, name='login_view'),

     path('logout/', views.logout_view, name='logout_view'),

     path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

     path('manage-blogs/', views.manage_blogs, name='manage_blogs'),

     path('sms-settings/', views.sms_settings, name='sms_settings'),
               
]

# Serve static and media files during development (when DEBUG is True)
if settings.DEBUG:
    # Serve media files
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serve static files
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)