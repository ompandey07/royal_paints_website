from django.shortcuts import render , redirect , get_object_or_404
from django.http import HttpResponse
from backend.models import BlogModel



# Create your views here.
def index_page(request):
     #**  Render the index.html template     
    return render(request, 'index.html')


def blogs_page(request):
    #** Render the blogs.html template
    context = {
        'blogs': BlogModel.objects.all()  
    }
    return render(request, 'blogs.html' , context)

def blog_detail(request, slug):
    blog = get_object_or_404(BlogModel, slug=slug)
    context = {
        'blog': blog
    }
    return render(request, 'blog_detail.html', context)


def abuot_page(request):
    #** Render the about.html template
    return render(request, 'about.html')