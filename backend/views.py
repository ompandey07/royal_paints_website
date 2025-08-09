from django.shortcuts import render , get_object_or_404, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.conf import settings
from .models import BlogModel , MailModel
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q
import os

# Create your views here.
def login_view(request):
     return render (request, 'Admin/login.html')






def logout_view(request):
    logout(request)
    return redirect('login_view')




def admin_dashboard(request):
    return render(request, 'Admin/AdminDashboard.html')




def manage_blogs(request):
    search_query = request.GET.get('search', '')
    
    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        
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





def sms_settings(request):
    search_query = request.GET.get('search', '')
    
    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        
        if action == 'delete':
            # Delete mail
            mail_id = request.POST.get('mail_id')
            try:
                mail = get_object_or_404(MailModel, id=mail_id)
                mail_subject = mail.subject
                
                # Delete template file if exists
                if mail.template and os.path.isfile(mail.template.path):
                    os.remove(mail.template.path)
                
                mail.delete()
                messages.success(request, f'SMS "{mail_subject}" has been deleted successfully.')
            except Exception as e:
                messages.error(request, f'Error deleting SMS: {str(e)}')
        
        elif action == 'toggle_selected':
            # Toggle selected status with single selection logic (AJAX request)
            mail_id = request.POST.get('mail_id')
            selected = request.POST.get('selected') == 'true'
            
            try:
                if selected:
                    # Check if another SMS is already selected
                    currently_selected = MailModel.objects.filter(selected_for=True).first()
                    if currently_selected and currently_selected.id != int(mail_id):
                        # Return info about currently selected SMS for confirmation
                        return JsonResponse({
                            'success': False,
                            'already_selected': True,
                            'current_sms': {
                                'id': currently_selected.id,
                                'subject': currently_selected.subject
                            }
                        })
                    
                    # Select this SMS and unselect all others
                    MailModel.objects.all().update(selected_for=False)
                    mail = get_object_or_404(MailModel, id=mail_id)
                    mail.selected_for = True
                    mail.save()
                    
                    return JsonResponse({'success': True, 'action': 'selected'})
                else:
                    # Unselect this SMS
                    mail = get_object_or_404(MailModel, id=mail_id)
                    mail.selected_for = False
                    mail.save()
                    
                    return JsonResponse({'success': True, 'action': 'unselected'})
                    
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        elif action == 'confirm_switch':
            # Force switch to new SMS (AJAX request)
            new_mail_id = request.POST.get('new_mail_id')
            
            try:
                # Unselect all SMS
                MailModel.objects.all().update(selected_for=False)
                
                # Select the new SMS
                mail = get_object_or_404(MailModel, id=new_mail_id)
                mail.selected_for = True
                mail.save()
                
                return JsonResponse({'success': True, 'switched': True})
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        else:
            # Create or Update mail
            mail_id = request.POST.get('mail_id')
            subject = request.POST.get('subject', '').strip()
            content = request.POST.get('content', '').strip()
            signature = request.POST.get('signature', '').strip()
            template = request.FILES.get('template')
            
            # Basic validation
            if not subject:
                messages.error(request, 'SMS subject is required.')
                return redirect('sms_settings')
            
            if not content:
                messages.error(request, 'SMS content is required.')
                return redirect('sms_settings')
            
            try:
                if mail_id:  # Update existing mail
                    mail = get_object_or_404(MailModel, id=mail_id)
                    old_template = mail.template
                    
                    mail.subject = subject
                    mail.content = content
                    mail.signature = signature
                    
                    if template:
                        # Delete old template if exists
                        if old_template and os.path.isfile(old_template.path):
                            os.remove(old_template.path)
                        mail.template = template
                    
                    mail.save()
                    messages.success(request, f'SMS "{subject}" has been updated successfully.')
                
                else:  # Create new mail
                    mail = MailModel.objects.create(
                        subject=subject,
                        content=content,
                        signature=signature,
                        template=template
                    )
                    messages.success(request, f'SMS "{subject}" has been saved successfully.')
            
            except Exception as e:
                messages.error(request, f'Error saving SMS: {str(e)}')
        
        return redirect('sms_settings')
    
    # GET request - Display mails
    mails = MailModel.objects.all()
    
    # Search functionality
    if search_query:
        mails = mails.filter(
            Q(subject__icontains=search_query) | 
            Q(content__icontains=search_query) |
            Q(signature__icontains=search_query)
        )
    
    # Pagination - 5 mails per page
    paginator = Paginator(mails, 5)
    page_number = request.GET.get('page')
    mails = paginator.get_page(page_number)
    
    context = {
        'mails': mails,
        'search_query': search_query,
    }
    
    return render(request, 'Admin/SmsSettings.html', context)