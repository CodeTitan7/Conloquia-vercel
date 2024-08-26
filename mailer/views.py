import uuid
import csv
import base64
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import EmailMessage
from django.utils.html import escape
from django.urls import reverse
from django.utils.timezone import now
from django.conf import settings
from .forms import EmailForm, SignUpForm, UserProfileForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Email, EmailTracking, EmailUsage, UserProfile
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import send_mail
from django.utils import timezone
from .storage import SupabaseStorage

DAILY_EMAIL_LIMIT = 10

@login_required
def home(request):
    return render(request, 'mailer/home.html')

@login_required
def inbox(request):
    emails = Email.objects.filter(user=request.user, category='inbox').order_by('-sent_at')
    return render(request, 'mailer/inbox.html', {'emails': emails})

@login_required
def sent_emails(request):
    emails = Email.objects.filter(user=request.user, category='sent').order_by('-sent_at')
    return render(request, 'mailer/sent.html', {'emails': emails})

@login_required
def draft_emails(request):
    emails = Email.objects.filter(user=request.user, category='draft').order_by('-sent_at')
    return render(request, 'mailer/drafts.html', {'emails': emails})

@login_required
def trash_emails(request):
    emails = Email.objects.filter(user=request.user, category='trash').order_by('-sent_at')
    return render(request, 'mailer/trash.html', {'emails': emails})

@login_required
def send_email(request):
    if request.method == 'POST':
        # Check rate limit
        usage, created = EmailUsage.objects.get_or_create(user=request.user)
        usage.reset_daily_limit()

        if usage.emails_sent_today >= DAILY_EMAIL_LIMIT:
            messages.error(request, "Daily email limit reached.")
            return redirect('send_email')

        form = EmailForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            recipient = form.cleaned_data['recipient']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            sender_email = form.cleaned_data['sender_email']
            attachment = form.cleaned_data.get('attachment')

            # Content filtering: Check for spammy content
            if "spam" in message.lower():
                messages.error(request, "Email contains inappropriate content.")
                return redirect('send_email')

            # Prepare the email
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=sender_email,
                to=[recipient],
            )

            # Attach file if present
            if attachment:
                email.attach(attachment.name, attachment.read(), attachment.content_type)

            # Send the email
            email.send()

            # Increment email usage
            usage.increment_emails_sent()

            # Log email sending
            Email.objects.create(
                user=request.user,
                recipient=recipient,
                subject=subject,
                message=message,
                sender_email=sender_email,
                sent_at=timezone.now(),
                category='sent'
            )

            return redirect('success')
    else:
        form = EmailForm(user=request.user)

    return render(request, 'mailer/send_email.html', {'form': form})

@login_required
def save_draft(request):
    if request.method == 'POST':
        form = EmailForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            email = form.save(commit=False)
            email.user = request.user
            email.category = 'draft'
            email.save()
            messages.success(request, "Draft saved successfully.")
            return redirect('draft_emails')
    else:
        form = EmailForm(user=request.user)

    return render(request, 'mailer/send_email.html', {'form': form})

@login_required
def starred_emails(request):
    emails = Email.objects.filter(user=request.user, starred=True).order_by('-sent_at')
    return render(request, 'mailer/starred.html', {'emails': emails})

@login_required
def move_to_trash(request, email_id):
    email = get_object_or_404(Email, id=email_id, user=request.user)
    email.category = 'trash'
    email.save()
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def move_to_inbox(request, email_id):
    email = get_object_or_404(Email, id=email_id, user=request.user)
    email.category = 'inbox'
    email.save()
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def star_email(request, email_id):
    email = get_object_or_404(Email, id=email_id, user=request.user)
    email.starred = not email.starred
    email.save()
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def track_email(request, tracking_id):
    email = get_object_or_404(Email, tracking_id=tracking_id, user=request.user)
    tracking, created = EmailTracking.objects.get_or_create(email=email)
    if not tracking.opened:
        tracking.opened = True
        tracking.opened_at = now()
        tracking.save()

    response = HttpResponse(content_type="image/png")
    response.write(base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/wcAAwAB/IX+lwQAAAABJRU5ErkJggg=="
    ))
    return response

@login_required
def track_click(request, tracking_id, url):
    email = get_object_or_404(Email, tracking_id=tracking_id, user=request.user)
    tracking, created = EmailTracking.objects.get_or_create(email=email)
    if not tracking.clicked:
        tracking.clicked = True
        tracking.clicked_at = now()
        tracking.save()
    return redirect(url)

@login_required
def email_analytics(request):
    emails = Email.objects.filter(user=request.user).select_related('emailtracking')
    return render(request, 'mailer/email_analytics.html', {'emails': emails})

@login_required
def export_emails_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="email_analytics.csv"'

    writer = csv.writer(response)
    writer.writerow(['Recipient', 'Subject', 'Opened', 'Opened At', 'Clicked', 'Clicked At'])

    emails = Email.objects.filter(user=request.user)
    for email in emails:
        tracking = getattr(email, 'tracking', None)
        if tracking:
            writer.writerow([
                email.recipient, email.subject, tracking.opened, tracking.opened_at,
                tracking.clicked, tracking.clicked_at
            ])
        else:
            writer.writerow([
                email.recipient, email.subject, 'No', '', 'No', ''
            ])

    return response

@login_required
def delete_forever(request, email_id):
    email = get_object_or_404(Email, id=email_id, user=request.user, category='trash')
    email.delete()
    return redirect('trash_emails')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return HttpResponse(status=405) 

def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def success(request):
    return render(request, 'mailer/success.html')

@login_required
def profile_view(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Generate the profile picture URL
    default_image_url = 'https://bhyccgfpceivprheoqen.supabase.co/storage/v1/object/sign/user-profile-pictures/profile_pics/default.png?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJ1c2VyLXByb2ZpbGUtcGljdHVyZXMvcHJvZmlsZV9waWNzL2RlZmF1bHQucG5nIiwiaWF0IjoxNzI0NjU0NDMxLCJleHAiOjE3MjQ4MjcyMzF9.qZK2qPjZZfcpcbl6boUp29oq5yoEBJg51tDOtj5f5OQ&t=2024-08-26T06%3A43%3A40.665Z'
    
    profile_picture_url = default_image_url
    if user_profile.profile_picture and user_profile.profile_picture.name != 'profile_pics/default.png':
        try:
            profile_picture_path = user_profile.profile_picture.name
            profile_picture_url = SupabaseStorage().generate_signed_url(profile_picture_path, expires_in=10800)
        except Exception as e:
            print(f"Error generating profile picture URL: {e}")
            # Fallback to the default image
            profile_picture_url = default_image_url

    return render(request, 'mailer/profile.html', {'profile': user_profile, 'profile_picture_url': profile_picture_url})

@login_required
def edit_profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Make sure 'profile' URL name is correctly defined
    else:
        form = UserProfileForm(instance=user_profile)

    default_image_url = 'https://bhyccgfpceivprheoqen.supabase.co/storage/v1/object/sign/user-profile-pictures/profile_pics/default.png?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJ1c2VyLXByb2ZpbGUtcGljdHVyZXMvcHJvZmlsZV9waWNzL2RlZmF1bHQucG5nIiwiaWF0IjoxNzI0NjU0NDMxLCJleHAiOjE3MjQ4MjcyMzF9.qZK2qPjZZfcpcbl6boUp29oq5yoEBJg51tDOtj5f5OQ&t=2024-08-26T06%3A43%3A40.665Z'

    profile_picture_url = default_image_url
    if user_profile.profile_picture and user_profile.profile_picture.name != 'profile_pics/default.png':
        try:
            profile_picture_path = user_profile.profile_picture.name
            profile_picture_url = SupabaseStorage().generate_signed_url(profile_picture_path, expires_in=10800)
        except Exception as e:
            print(f"Error generating profile picture URL: {e}")
            # Ensure that any exceptions revert to the default image
            profile_picture_url = default_image_url

    return render(request, 'mailer/edit_profile.html',{'form': form,'profile_picture_url': profile_picture_url})