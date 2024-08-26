import uuid
import os
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from .storage import SupabaseStorage
from supabase import create_client, Client

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

class Email(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emails', default=1)
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    tracking_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    category = models.CharField(
        max_length=20,
        choices=[
            ('inbox', 'Inbox'),
            ('sent', 'Sent'),
            ('draft', 'Draft'),
            ('trash', 'Trash'),
        ],
        default='draft'
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    starred = models.BooleanField(default=False)
    sender_email = models.EmailField(default=settings.DEFAULT_EMAIL)
    attachment = models.FileField(upload_to='attachments/', blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['recipient']),
            models.Index(fields=['sent_at']),
        ]

    def __str__(self):
        return self.subject


class EmailTracking(models.Model):
    email = models.OneToOneField(Email, on_delete=models.CASCADE)
    opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Tracking for {self.email.subject}"

class EmailUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    emails_sent_today = models.IntegerField(default=0)
    last_reset_date = models.DateField(auto_now_add=True)

    def reset_daily_limit(self):
        if self.last_reset_date < timezone.now().date():
            self.emails_sent_today = 0
            self.last_reset_date = timezone.now().date()
            self.save()

    def increment_emails_sent(self):
        self.emails_sent_today += 1
        self.save()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True, default='profile_pics/default.png')
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.username    
    
    def save(self, *args, **kwargs):
        # Check if the profile already exists (not a new instance)
        if self.pk:
            old_profile = UserProfile.objects.get(pk=self.pk)
            if old_profile.profile_picture and old_profile.profile_picture.name != 'profile_pics/default.png':
                old_image_name = old_profile.profile_picture.name
                # Delete the old image if a new image is uploaded
                if old_image_name != self.profile_picture.name:
                    self.delete_old_image_from_supabase(old_image_name)

        super().save(*args, **kwargs)

    def delete_old_image_from_supabase(self, old_image_name):
        # Initialize Supabase client
        url = SUPABASE_URL
        key = SUPABASE_KEY
        supabase: Client = create_client(url, key)

        # Delete the old image from Supabase
        bucket_name = 'user-profile-pictures'
        try:
            supabase.storage.from_(bucket_name).remove([old_image_name])
        except Exception as e:
            print(f"Error deleting old profile picture from Supabase: {e}")