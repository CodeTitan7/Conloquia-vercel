import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User

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
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.user.username        