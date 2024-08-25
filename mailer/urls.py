# urls.py

from django.urls import path
from .views import (
    home, send_email, track_email, email_analytics, export_emails_csv,edit_profile,
    track_click, inbox, sent_emails, draft_emails, trash_emails, starred_emails, success,
    move_to_trash, move_to_inbox, star_email, delete_forever, signup, profile_view, logout_view, custom_login 
)

urlpatterns = [
    path('', home, name='home'),
    path('signup/', signup, name='signup'),
    path('login/', custom_login, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('edit-profile/', edit_profile, name='edit_profile'),
    path('send-email/', send_email, name='send_email'),
    path('success/', success, name='success'), 
    path('track-email/<str:tracking_id>/', track_email, name='track_email'),
    path('email-analytics/', email_analytics, name='email_analytics'),
    path('export-emails/', export_emails_csv, name='export_emails_csv'),
    path('track-click/<str:tracking_id>/<path:url>/', track_click, name='track_click'),
    path('inbox/', inbox, name='inbox'),
    path('sent/', sent_emails, name='sent_emails'),
    path('drafts/', draft_emails, name='draft_emails'),
    path('trash/', trash_emails, name='trash_emails'),
    path('starred/', starred_emails, name='starred_emails'),
    path('move-to-trash/<int:email_id>/', move_to_trash, name='move_to_trash'),
    path('move-to-inbox/<int:email_id>/', move_to_inbox, name='move_to_inbox'),
    path('star-email/<int:email_id>/', star_email, name='star_email'),
    path('trash/delete_forever/<int:email_id>/', delete_forever, name='delete_forever'),
]

