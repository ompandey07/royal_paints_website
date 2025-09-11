from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from backend.models import BlogModel, ContactModel
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

# ======================================================================
# FRONTEND PUBLIC VIEWS
# ======================================================================

def index_page(request):
    """
    Homepage view - renders the main landing page with quote form
    """
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('your_name', '').strip()
        email = request.POST.get('your_email', '').strip()
        message = request.POST.get('your_message', '').strip()
        
        # Simple validation
        errors = {}
        if not name:
            errors['name'] = 'Name is required.'
        if not email:
            errors['email'] = 'Email is required.'
        elif '@' not in email:
            errors['email'] = 'Please enter a valid email.'
        if not message:
            errors['message'] = 'Message is required.'
        
        # If no errors, save to database
        if not errors:
            try:
                ContactModel.objects.create(
                    your_name=name,
                    your_email=email,
                    your_message=message
                )
                # Get recent blogs and return with success
                recent_blogs = BlogModel.objects.all().order_by('-created_at')[:3]
                return render(request, 'Client/index.html', {
                    'success': True,
                    'recent_blogs': recent_blogs
                })
            except:
                errors['general'] = 'Error saving message. Please try again.'
        
        # If errors, return form with errors
        recent_blogs = BlogModel.objects.all().order_by('-created_at')[:3]
        return render(request, 'Client/index.html', {
            'errors': errors,
            'form_data': {
                'name': name,
                'email': email,
                'message': message
            },
            'recent_blogs': recent_blogs
        })
    
    # GET request - just show the page with recent blogs
    recent_blogs = BlogModel.objects.all().order_by('-created_at')[:3]
    context = {
        'recent_blogs': recent_blogs
    }
    return render(request, 'Client/index.html', context)
# ======================================================================
# BLOG VIEWS
# ======================================================================

def blogs_page(request):
    """
    Blog listing page - displays all published blogs
    
    Features:
    - Fetches all blog posts from database
    - Public access to blog content
    - Blog overview and navigation
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered blogs.html template with blog list
    """
    #** Render the blogs.html template
    context = {
        'blogs': BlogModel.objects.all()  
    }
    return render(request, 'Client/blogs.html', context)

def blog_detail(request, slug):
    """
    Individual blog post detail view
    
    Features:
    - Displays single blog post by slug
    - 404 error handling for non-existent blogs
    - SEO-friendly URL structure using slugs
    
    Args:
        request: HTTP request object
        slug: URL slug parameter for blog identification
        
    Returns:
        HttpResponse: Rendered blog_detail.html template with blog data
        
    Raises:
        Http404: If blog with given slug doesn't exist
    """
    blog = get_object_or_404(BlogModel, slug=slug)
    context = {
        'blog': blog
    }
    return render(request, 'Client/blog_detail.html', context)

# ======================================================================
# About Us Page
# ======================================================================

def about_page(request):
    """
    About page view - renders company information and handles quote form submission
    """
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('your_name', '').strip()
        email = request.POST.get('your_email', '').strip()
        message = request.POST.get('your_message', '').strip()
        
        # Simple validation
        errors = {}
        if not name:
            errors['name'] = 'Name is required.'
        if not email:
            errors['email'] = 'Email is required.'
        elif '@' not in email:
            errors['email'] = 'Please enter a valid email.'
        if not message:
            errors['message'] = 'Message is required.'
        
        # If no errors, save to database
        if not errors:
            try:
                ContactModel.objects.create(
                    your_name=name,
                    your_email=email,
                    your_message=message
                )
                return render(request, 'Client/about.html', {'success': True})
            except:
                errors['general'] = 'Error saving message. Please try again.'
        
        # If errors, return form with errors
        return render(request, 'Client/about.html', {
            'errors': errors,
            'form_data': {
                'name': name,
                'email': email,
                'message': message
            }
        })
    
    # GET request - just show the page
    return render(request, 'Client/about.html')

# ======================================================================
# Services Page
# ======================================================================

def services_page(request):
    """
    Services page view - renders company/organization information
    
    Features:
    - Static services page rendering
    - Company information display
    - No authentication required
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered services.html template
    """
    #** Render the services.html template
    return render(request, 'Client/services.html')

# ======================================================================
# Contacts Us Page
# ======================================================================

def contacts_page(request):
    """
    Simple contacts page view - handles GET and POST requests
    """
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('your_name', '').strip()
        email = request.POST.get('your_email', '').strip()
        message = request.POST.get('your_message', '').strip()
        
        # Simple validation
        errors = {}
        if not name:
            errors['name'] = 'Name is required.'
        if not email:
            errors['email'] = 'Email is required.'
        elif '@' not in email:
            errors['email'] = 'Please enter a valid email.'
        if not message:
            errors['message'] = 'Message is required.'
        
        # If no errors, save to database
        if not errors:
            try:
                ContactModel.objects.create(
                    your_name=name,
                    your_email=email,
                    your_message=message
                )
                return render(request, 'Client/contacts.html', {'success': True})
            except:
                errors['general'] = 'Error saving message. Please try again.'
        
        # If errors, return form with errors
        return render(request, 'Client/contacts.html', {
            'errors': errors,
            'form_data': {
                'name': name,
                'email': email,
                'message': message
            }
        })
    
    # GET request - just show the page
    return render(request, 'Client/contacts.html')