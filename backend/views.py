from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
import os

from .models import BlogModel, ContactModel, CarrierModel


# ======================================================================
# ERROR HANDLING VIEWS
# ======================================================================

def unauthorized_acess(request):    
    """
    Renders unauthorized access error page for users without proper permissions
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered unauthorized access error template
    """
    return render(request, 'Errors/unauthorized_access.html')


# ======================================================================
# AUTHENTICATION VIEWS
# ======================================================================

def login_view(request):
    """
    Simple function-based login view with default admin user
    Default credentials are handled internally
    
    Features:
    - Creates default admin user if doesn't exist
    - Handles both admin and regular user authentication
    - Email-based login with username lookup
    - Proper error handling and user feedback
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Login template or redirect to dashboard
    """
    
    # Default admin credentials (hidden from template)
    DEFAULT_EMAIL = 'royalpaints@admin.com'
    DEFAULT_PASSWORD = 'admin@1200'
    DEFAULT_USERNAME = 'admin'
    DEFAULT_FIRST_NAME = 'Admin'
    DEFAULT_LAST_NAME = 'User'
    
    # ==================== Admin User Creation ====================
    # Ensure default admin user exists
    try:
        with transaction.atomic():
            admin_user, created = User.objects.get_or_create(
                username=DEFAULT_USERNAME,
                defaults={
                    'email': DEFAULT_EMAIL,
                    'first_name': DEFAULT_FIRST_NAME,
                    'last_name': DEFAULT_LAST_NAME,
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True,
                }
            )
            
            # Set password for new user or update existing user's password
            if created or not admin_user.check_password(DEFAULT_PASSWORD):
                admin_user.set_password(DEFAULT_PASSWORD)
                admin_user.email = DEFAULT_EMAIL  # Ensure email is correct
                admin_user.save()
                
    except Exception as e:
        messages.error(request, 'System error occurred. Please try again.')
        return render(request, 'Admin/login.html')
    
    # ==================== Authentication Check ====================
    # Check if user is already authenticated
    if request.user.is_authenticated:
        messages.success(request, 'You are already logged in!')
        return redirect('admin_dashboard')
    
    # ==================== POST Request Handling ====================
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        
        # Basic validation
        if not email or not password:
            messages.error(request, 'Please enter both email and password')
            return render(request, 'Admin/login.html')
        
        # Handle default admin login
        if email == DEFAULT_EMAIL.lower() and password == DEFAULT_PASSWORD:
            user = authenticate(request, username=DEFAULT_USERNAME, password=DEFAULT_PASSWORD)
            if user is not None and user.is_active:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('admin_dashboard')
        
        # For other users, find by email
        try:
            user_obj = User.objects.get(email__iexact=email)
            username = user_obj.username
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password')
            return render(request, 'Admin/login.html')
        
        # Authenticate using username and password
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Your account has been deactivated')
        else:
            messages.error(request, 'Invalid email or password')
    
    # ==================== GET Request Handling ====================
    # Render login page for GET requests or failed login attempts
    return render(request, 'Admin/login.html')


def logout_view(request):
    """
    Handles user logout and redirects to login page
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponseRedirect: Redirect to login view
    """
    logout(request)
    return redirect('login_view')


# ======================================================================
# ADMIN DASHBOARD VIEWS
# ======================================================================

@login_required(login_url='unauthorized_acess')
def admin_dashboard(request):
    """
    Simple admin dashboard view
    
    Features:
    - Requires user authentication
    - Displays basic dashboard information
    - Provides user context for template
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered admin dashboard template
    """
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to access the admin dashboard')
        return redirect('login_view')
    
    # Counts Of Data 
    total_carriers = CarrierModel.objects.count()
    total_blogs = BlogModel.objects.count()
    total_contacts = ContactModel.objects.count()
    context = {
        'user': request.user,
        'dashboard_title': 'Admin Dashboard',
        'total_carriers': total_carriers,
        'total_blogs': total_blogs,
        'total_contacts': total_contacts,
    }
    return render(request, 'Admin/AdminDashboard.html', context)


# ======================================================================
# BLOG MANAGEMENT VIEWS
# ======================================================================

@login_required(login_url='unauthorized_acess')
def manage_blogs(request):
    """
    Comprehensive blog management view for CRUD operations
    
    Features:
    - Create new blogs with title, content, and image
    - Update existing blogs
    - Delete blogs with file cleanup
    - Search functionality across title and content
    - Image file management (upload/delete)
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Blog management template with blog list
    """
    search_query = request.GET.get('search', '')
    
    # ==================== POST Request Handling ====================
    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        
        # ========== Delete Blog ==========
        if action == 'delete':
            # Delete blog
            blog_id = request.POST.get('blog_id')
            try:
                blog = get_object_or_404(BlogModel, id=blog_id)
                blog_title = blog.title
                
                # Delete image file if exists
                if blog.image and os.path.isfile(blog.image.path):
                    os.remove(blog.image.path)
                
                blog.delete()
                messages.success(request, f'Blog "{blog_title}" has been deleted successfully.')
            except Exception as e:
                messages.error(request, f'Error deleting blog: {str(e)}')
        
        # ========== Create/Update Blog ==========
        else:
            # Create or Update blog
            blog_id = request.POST.get('blog_id')
            title = request.POST.get('title', '').strip()
            content = request.POST.get('content', '').strip()
            image = request.FILES.get('image')
            
            # Basic validation
            if not title:
                messages.error(request, 'Blog title is required.')
                return redirect('manage_blogs')
            
            try:
                if blog_id:  # Update existing blog
                    blog = get_object_or_404(BlogModel, id=blog_id)
                    old_image = blog.image
                    
                    blog.title = title
                    blog.content = content
                    
                    if image:
                        # Delete old image if exists
                        if old_image and os.path.isfile(old_image.path):
                            os.remove(old_image.path)
                        blog.image = image
                    
                    blog.save()  # This will auto-update the slug
                    messages.success(request, f'Blog "{title}" has been updated successfully.')
                
                else:  # Create new blog
                    blog = BlogModel.objects.create(
                        title=title,
                        content=content,
                        image=image
                    )
                    messages.success(request, f'Blog "{title}" has been published successfully.')
            
            except Exception as e:
                messages.error(request, f'Error saving blog: {str(e)}')
        
        return redirect('manage_blogs')
    
    # ==================== GET Request Handling ====================
    # GET request - Display blogs
    blogs = BlogModel.objects.all()
    
    # Search functionality
    if search_query:
        blogs = blogs.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query)
        )
    
    context = {
        'blogs': blogs,
        'search_query': search_query,
    }
    
    return render(request, 'Admin/ManageBlogs.html', context)



# ======================================================================
# CUSTOMER CONTACT VIEWS
# ======================================================================
@login_required(login_url='unauthorized_acess')
def customer_contact_view(request):
    search_query = request.GET.get('search', '')
    CustomerContacts = ContactModel.objects.all()
    if search_query:
        CustomerContacts = CustomerContacts.filter(
            Q(your_name__icontains=search_query) | 
            Q(your_email__icontains=search_query)
        )
    context = {
        'CustomerContacts': CustomerContacts,
        'search_query': search_query
    }
    return render(request, 'Admin/ManageContacts.html', context)





# ======================================================================
# CARRIER MANAGEMENT VIEWS
# ======================================================================

@login_required(login_url='unauthorized_acess')
def manage_carriers(request):
    """
    Comprehensive carrier management view for CRUD operations
    
    Features:
    - Create new carriers with title, description, deadline, and image
    - Update existing carriers
    - Delete carriers with file cleanup
    - Search functionality across title and description
    - Image file management (upload/delete)
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Carrier management template with carrier list
    """
    search_query = request.GET.get('search', '')
    
    # ==================== POST Request Handling ====================
    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        
        # ========== Delete Carrier ==========
        if action == 'delete':
            carrier_id = request.POST.get('carrier_id')
            try:
                carrier = get_object_or_404(CarrierModel, id=carrier_id)
                carrier_title = carrier.carrier_title
                
                # Delete image file if exists
                if carrier.carrier_image and os.path.isfile(carrier.carrier_image.path):
                    os.remove(carrier.carrier_image.path)
                
                carrier.delete()
                messages.success(request, f'Carrier "{carrier_title}" has been deleted successfully.')
            except Exception as e:
                messages.error(request, f'Error deleting carrier: {str(e)}')
        
        # ========== Create/Update Carrier ==========
        else:
            carrier_id = request.POST.get('carrier_id')
            carrier_title = request.POST.get('carrier_title', '').strip()
            description = request.POST.get('description', '').strip()
            deadline_date = request.POST.get('deadline_date', '').strip()
            carrier_image = request.FILES.get('carrier_image')
            
            # Basic validation
            if not carrier_title:
                messages.error(request, 'Carrier title is required.')
                return redirect('manage_carriers')
            
            if not deadline_date:
                messages.error(request, 'Deadline date is required.')
                return redirect('manage_carriers')
            
            try:
                if carrier_id:  # Update existing carrier
                    carrier = get_object_or_404(CarrierModel, id=carrier_id)
                    old_image = carrier.carrier_image
                    
                    carrier.carrier_title = carrier_title
                    carrier.description = description
                    carrier.deadline_date = deadline_date
                    
                    if carrier_image:
                        # Delete old image if exists
                        if old_image and os.path.isfile(old_image.path):
                            os.remove(old_image.path)
                        carrier.carrier_image = carrier_image
                    
                    carrier.save()
                    messages.success(request, f'Carrier "{carrier_title}" has been updated successfully.')
                
                else:  # Create new carrier
                    carrier = CarrierModel.objects.create(
                        carrier_title=carrier_title,
                        description=description,
                        deadline_date=deadline_date,
                        carrier_image=carrier_image
                    )
                    messages.success(request, f'Carrier "{carrier_title}" has been created successfully.')
            
            except Exception as e:
                messages.error(request, f'Error saving carrier: {str(e)}')
        
        return redirect('manage_carriers')
    
    # ==================== GET Request Handling ====================
    # GET request - Display carriers
    carriers = CarrierModel.objects.all().order_by('-created_at')
    
    # Search functionality
    if search_query:
        carriers = carriers.filter(
            Q(carrier_title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    context = {
        'carriers': carriers,
        'search_query': search_query,
    }
    
    return render(request, 'Admin/ManageCarriers.html', context)