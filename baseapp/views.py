from django.shortcuts import render , redirect , get_object_or_404
from django.http import HttpResponse
from backend.models import BlogModel


# ======================================================================
# FRONTEND PUBLIC VIEWS
# ======================================================================

def index_page(request):
    """
    Homepage view - renders the main landing page
    
    Features:
    - Static homepage rendering
    - No authentication required
    - Main entry point for visitors
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered index.html template
    """
     #**  Render the index.html template     
    return render(request, 'index.html')


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
    return render(request, 'blogs.html' , context)


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
    return render(request, 'blog_detail.html', context)


# ======================================================================
# STATIC PAGES
# ======================================================================

def abuot_page(request):
    """
    About page view - renders company/organization information
    
    Features:
    - Static about page rendering
    - Company information display
    - No authentication required
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered about.html template
    """
    #** Render the about.html template
    return render(request, 'about.html')