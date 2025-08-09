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
import pandas as pd
from io import BytesIO
from django.utils.decorators import method_decorator
from django.views import View
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from django.db import transaction

from .models import Customer
import os


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
    DEFAULT_EMAIL = 'admin@tvs.com'
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
    
    context = {
        'user': request.user,
        'dashboard_title': 'Admin Dashboard',
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
# SMS/MAIL MANAGEMENT VIEWS
# ======================================================================

@login_required(login_url='unauthorized_acess')
def sms_settings(request):
    """
    Comprehensive SMS/Mail settings management view
    
    Features:
    - Create and update SMS templates
    - Delete SMS templates with file cleanup
    - Single selection logic for active SMS template
    - Search functionality across multiple fields
    - AJAX support for template selection
    - Pagination support (5 items per page)
    - Template file management
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: SMS settings template or JsonResponse for AJAX
    """
    search_query = request.GET.get('search', '')
    
    # ==================== POST Request Handling ====================
    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        
        # ========== Delete Mail ==========
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
        
        # ========== Toggle Selected Status (AJAX) ==========
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
        
        # ========== Confirm Switch (AJAX) ==========
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
        
        # ========== Create/Update Mail ==========
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
    
    # ==================== GET Request Handling ====================
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


# ======================================================================
# CUSTOMER SMS MANAGEMENT CLASS-BASED VIEW
# ======================================================================

@method_decorator([
    csrf_exempt,
    login_required(login_url='unauthorized_acess')
], name='dispatch')
class ManageCustomerSMSView(View):
    """
    Single comprehensive view for managing SMS customers with all functionality
    
    Features:
    - Customer list display with search and pagination
    - Excel template export for data import
    - Customer data export to Excel
    - Bulk customer data import from Excel
    - Duplicate detection and resolution
    - Progress tracking for import operations
    - AJAX support for file operations
    - Login required for all operations
    
    Methods:
        get: Handles GET requests (list, export operations)
        post: Handles POST requests (import operations)
        show_customers_list: Display paginated customer list
        export_format_template: Generate Excel import template
        export_customers_data: Export current customers to Excel
        import_customers_data: Process Excel file import
        handle_duplicates: Manage duplicate resolution
        process_import: Execute actual import with progress tracking
    """
    
    # ==================== HTTP Method Handlers ====================
    
    def get(self, request):
        """
        Handle GET requests for customer management
        
        Supported actions:
        - Default: Show customers list
        - export_format: Download Excel import template
        - export_data: Download current customers data
        
        Args:
            request: HTTP request object
            
        Returns:
            HttpResponse: Template render or Excel file download
        """
        # Handle different actions
        action = request.GET.get('action')
        
        if action == 'export_format':
            return self.export_format_template()
        elif action == 'export_data':
            return self.export_customers_data()
        
        # Default: Show customers list
        return self.show_customers_list(request)
    
    def post(self, request):
        """
        Handle POST requests for data import operations
        
        Supported actions:
        - import_data: Process Excel file upload
        - handle_duplicates: Resolve duplicate entries
        
        Args:
            request: HTTP request object
            
        Returns:
            JsonResponse: Operation result with status and data
        """
        # Handle import data
        action = request.POST.get('action')
        
        print("=== POST REQUEST DEBUG ===")
        print("Action:", action)
        print("User:", request.user.username if request.user.is_authenticated else 'Anonymous')
        print("Is Authenticated:", request.user.is_authenticated)
        print("Content-Type:", request.content_type)
        print("POST keys:", list(request.POST.keys()))
        print("FILES keys:", list(request.FILES.keys()))
        
        if action == 'import_data':
            return self.import_customers_data(request)
        elif action == 'handle_duplicates':
            return self.handle_duplicates(request)
        
        return JsonResponse({'success': False, 'error': 'Invalid action: ' + str(action)})
    
    # ==================== Customer List Management ====================
    
    def show_customers_list(self, request):
        """
        Display customers list with search and pagination
        
        Features:
        - Search across name, contact, email, address
        - Pagination (15 customers per page)
        - Statistics display (total, sent, pending)
        - User context for template
        
        Args:
            request: HTTP request object
            
        Returns:
            HttpResponse: Rendered customer management template
        """
        
        # Search functionality
        search_query = request.GET.get('search', '')
        customers = Customer.objects.all()
        
        if search_query:
            customers = customers.filter(
                Q(full_name__icontains=search_query) |
                Q(contact_number__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(address__icontains=search_query)
            )
        
        # Pagination
        paginator = Paginator(customers, 15)
        page_number = request.GET.get('page')
        customers_page = paginator.get_page(page_number)
        
        context = {
            'customers': customers_page,
            'search_query': search_query,
            'total_customers': Customer.objects.count(),
            'sms_sent_count': Customer.objects.filter(sms_status=True).count(),
            'sms_pending_count': Customer.objects.filter(sms_status=False).count(),
            'current_user': request.user,  # Add user info to context
        }
        
        return render(request, 'Admin/ManageSMS.html', context)
    
    # ==================== Excel Export Operations ====================
    
    def export_format_template(self):
        """
        Export Excel format template with green headers
        
        Features:
        - Pre-formatted Excel template for import
        - Green header styling with white text
        - Sample data for reference
        - Proper column widths
        - Required column structure
        
        Returns:
            HttpResponse: Excel file download with template
        """
        
        # Create workbook and worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = "Customer Data Template"
        
        # Define headers
        headers = ['FULL NAME', 'CONTACT NUMBER', 'ADDRESS', 'EMAIL']
        
        # Add headers to first row
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            
            # Style the header cells
            cell.fill = PatternFill(start_color="00B050", end_color="00B050", fill_type="solid")  # Green background
            cell.font = Font(color="FFFFFF", bold=True, size=12)  # White text, bold
            cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Add sample data for reference
        sample_data = [
            ['John Doe', '1234567890', '123 Main St, City, State', 'john.doe@example.com'],
            ['Jane Smith', '0987654321', '456 Oak Ave, Town, State', 'jane.smith@example.com'],
            ['Mike Johnson', '1122334455', '789 Pine Rd, Village, State', 'mike.johnson@example.com'],
        ]
        
        for row_idx, row_data in enumerate(sample_data, 2):
            for col_idx, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.font = Font(color="666666")  # Gray text for samples
        
        # Adjust column widths
        column_widths = [25, 20, 35, 30]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = width
        
        # Create response
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="Customer_Import_Template.xlsx"'
        
        # Save workbook to response
        wb.save(response)
        return response
    
    def export_customers_data(self):
        """
        Export current customers data to Excel
        
        Features:
        - All customer data export
        - Formatted Excel with green headers
        - Timestamp-based filename
        - Complete customer information including SMS status
        - Proper column formatting and widths
        
        Returns:
            HttpResponse: Excel file download with customer data
        """
        
        # Get all customers
        customers = Customer.objects.all().order_by('-created_at')
        
        # Create workbook and worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = "Customers Data"
        
        # Define headers
        headers = ['FULL NAME', 'CONTACT NUMBER', 'ADDRESS', 'EMAIL', 'SMS STATUS', 'CREATED AT', 'UPDATED AT', 'SENT SMS AT']
        
        # Add headers to first row
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            
            # Style the header cells
            cell.fill = PatternFill(start_color="00B050", end_color="00B050", fill_type="solid")  # Green background
            cell.font = Font(color="FFFFFF", bold=True, size=12)  # White text, bold
            cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Add customer data
        for row_idx, customer in enumerate(customers, 2):
            ws.cell(row=row_idx, column=1, value=customer.full_name)
            ws.cell(row=row_idx, column=2, value=customer.contact_number)
            ws.cell(row=row_idx, column=3, value=customer.address)
            ws.cell(row=row_idx, column=4, value=customer.email)
            ws.cell(row=row_idx, column=5, value="Sent" if customer.sms_status else "Pending")
            ws.cell(row=row_idx, column=6, value=customer.created_at.strftime('%Y-%m-%d %H:%M:%S') if customer.created_at else '')
            ws.cell(row=row_idx, column=7, value=customer.updated_at.strftime('%Y-%m-%d %H:%M:%S') if customer.updated_at else '')
            ws.cell(row=row_idx, column=8, value=customer.sent_sms_at.strftime('%Y-%m-%d %H:%M:%S') if customer.sent_sms_at else '')
        
        # Adjust column widths
        column_widths = [25, 20, 35, 30, 15, 20, 20, 20]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = width
        
        # Create response
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="Customers_Data_{timestamp}.xlsx"'
        
        # Save workbook to response
        wb.save(response)
        return response
    
    # ==================== Excel Import Operations ====================
    
    def import_customers_data(self, request):
        """
        Import customers data from Excel with duplicate checking and progress tracking
        
        Features:
        - Excel file validation and parsing
        - Required column validation
        - Empty row handling
        - Duplicate detection by contact number
        - Session-based data storage for multi-step process
        - Comprehensive error handling and logging
        
        Args:
            request: HTTP request object with uploaded Excel file
            
        Returns:
            JsonResponse: Import status, duplicate info, or error details
        """
        
        print("=== IMPORT DEBUG ===")
        print("Authenticated User:", request.user.username if request.user.is_authenticated else 'Anonymous')
        print("POST data keys:", request.POST.keys())
        print("FILES data keys:", request.FILES.keys())
        print("Content type:", request.content_type)
        
        if not request.FILES.get('excel_file'):
            print("ERROR: No excel_file in request.FILES")
            print("Available files:", list(request.FILES.keys()))
            return JsonResponse({
                'success': False,
                'error': 'No Excel file provided. Available files: ' + str(list(request.FILES.keys()))
            })
        
        excel_file = request.FILES['excel_file']
        print(f"File received: {excel_file.name}, size: {excel_file.size}")
        
        try:
            # Read Excel file
            df = pd.read_excel(excel_file)
            print(f"Excel read successfully. Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            
            # Validate required columns
            required_columns = ['FULL NAME', 'CONTACT NUMBER', 'ADDRESS', 'EMAIL']
            df.columns = df.columns.str.upper().str.strip()  # Normalize column names
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required columns: {", ".join(missing_columns)}. Found columns: {", ".join(df.columns)}'
                })
            
            # Remove empty rows
            df = df.dropna(subset=required_columns, how='all')
            
            if df.empty:
                return JsonResponse({
                    'success': False,
                    'error': 'No valid data found in the Excel file'
                })
            
            print(f"Valid rows after cleanup: {len(df)}")
            
            # Check for duplicates first
            duplicates = []
            valid_rows = []
            
            for index, row in df.iterrows():
                try:
                    # Clean data
                    full_name = str(row['FULL NAME']).strip()
                    contact_number = str(row['CONTACT NUMBER']).strip()
                    address = str(row['ADDRESS']).strip()
                    email = str(row['EMAIL']).strip()
                    
                    # Validate required fields
                    if not all([full_name, contact_number, address, email]) or any(val == 'nan' for val in [full_name, contact_number, address, email]):
                        print(f"Skipping row {index + 2}: Missing data")
                        continue
                    
                    # Check for duplicate contact number
                    existing_customer = Customer.objects.filter(contact_number=contact_number).first()
                    
                    row_data = {
                        'row_number': index + 2,
                        'full_name': full_name,
                        'contact_number': contact_number,
                        'address': address,
                        'email': email
                    }
                    
                    if existing_customer:
                        duplicates.append({
                            **row_data,
                            'existing_name': existing_customer.full_name,
                            'existing_email': existing_customer.email,
                            'existing_id': existing_customer.id
                        })
                    else:
                        valid_rows.append(row_data)
                        
                except Exception as e:
                    print(f"Error processing row {index + 2}: {str(e)}")
                    continue
            
            print(f"Processing complete. Valid: {len(valid_rows)}, Duplicates: {len(duplicates)}")
            
            # Store data in session for later processing
            request.session['import_data'] = {
                'valid_rows': valid_rows,
                'duplicates': duplicates,
                'total_rows': len(df),
                'imported_by': request.user.username if request.user.is_authenticated else 'Unknown'
            }
            
            if duplicates:
                return JsonResponse({
                    'success': True,
                    'has_duplicates': True,
                    'duplicates': duplicates,
                    'valid_count': len(valid_rows),
                    'duplicate_count': len(duplicates),
                    'total_rows': len(df)
                })
            else:
                # No duplicates, proceed with import
                return self.process_import(request, valid_rows, [])
                
        except Exception as e:
            print(f"Exception in import_customers_data: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'Error reading Excel file: {str(e)}'
            })
    
    def handle_duplicates(self, request):
        """
        Handle duplicate resolution and process import
        
        Features:
        - Multiple resolution strategies (replace, ignore, cancel)
        - Session data management
        - Delegation to import processor
        
        Args:
            request: HTTP request object with duplicate action
            
        Returns:
            JsonResponse: Resolution result or error status
        """
        
        action = request.POST.get('duplicate_action')  # 'replace', 'ignore', or 'cancel'
        
        if action == 'cancel':
            if 'import_data' in request.session:
                del request.session['import_data']
            return JsonResponse({'success': True, 'action': 'cancelled'})
        
        import_data = request.session.get('import_data')
        if not import_data:
            return JsonResponse({'success': False, 'error': 'No import data found'})
        
        valid_rows = import_data['valid_rows']
        duplicates = import_data['duplicates']
        
        # Process based on action
        if action == 'replace':
            # Include duplicates for replacement
            return self.process_import(request, valid_rows, duplicates, replace=True)
        elif action == 'ignore':
            # Process only valid rows, ignore duplicates
            return self.process_import(request, valid_rows, [])
        
        return JsonResponse({'success': False, 'error': 'Invalid action'})
    
    def process_import(self, request, valid_rows, duplicates, replace=False):
        """
        Process the actual import with progress tracking
        
        Features:
        - Batch customer creation
        - Duplicate replacement logic
        - Progress tracking and statistics
        - Error collection and reporting
        - Session cleanup
        - Comprehensive logging
        
        Args:
            request: HTTP request object
            valid_rows: List of new customer data
            duplicates: List of duplicate customer data
            replace: Boolean flag for duplicate replacement
            
        Returns:
            JsonResponse: Import results with statistics and errors
        """
        
        total_operations = len(valid_rows) + (len(duplicates) if replace else 0)
        processed = 0
        created_count = 0
        updated_count = 0
        errors = []
        
        try:
            # Process valid rows (new customers)
            for row_data in valid_rows:
                try:
                    Customer.objects.create(
                        full_name=row_data['full_name'],
                        contact_number=row_data['contact_number'],
                        address=row_data['address'],
                        email=row_data['email']
                    )
                    created_count += 1
                except Exception as e:
                    errors.append(f"Row {row_data['row_number']}: {str(e)}")
                
                processed += 1
            
            # Process duplicates if replacing
            if replace and duplicates:
                for dup_data in duplicates:
                    try:
                        Customer.objects.filter(id=dup_data['existing_id']).update(
                            full_name=dup_data['full_name'],
                            address=dup_data['address'],
                            email=dup_data['email'],
                            # Keep the original contact_number
                        )
                        updated_count += 1
                    except Exception as e:
                        errors.append(f"Row {dup_data['row_number']}: {str(e)}")
                    
                    processed += 1
            
            # Clean up session
            if 'import_data' in request.session:
                del request.session['import_data']
            
            return JsonResponse({
                'success': True,
                'created_count': created_count,
                'updated_count': updated_count,
                'total_processed': processed,
                'errors': errors,
                'message': f'Successfully processed {processed} records. Created: {created_count}, Updated: {updated_count}',
                'imported_by': request.user.username if request.user.is_authenticated else 'Unknown'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error during import: {str(e)}'
            })
        






# ======================================================================
# FULL DOCUMENTATION ALL 
# ======================================================================
@login_required(login_url='unauthorized_acess')
def full_documentation(request):
    """
    Render the full documentation page for the admin dashboard.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered documentation template
    """
    return render(request, 'Admin/FullDocumentation.html')
