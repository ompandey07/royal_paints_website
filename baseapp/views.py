from django.shortcuts import render , redirect
from django.http import HttpResponse




# Create your views here.
def index_page(request):
     #**  Render the index.html template     
    return render(request, 'index.html')