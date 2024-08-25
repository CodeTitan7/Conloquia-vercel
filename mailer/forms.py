from django import forms
from .models import Email, UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class EmailForm(forms.ModelForm):
    sender_email = forms.EmailField(required=True)
    recipient = forms.EmailField(required=True)
    attachment = forms.FileField(required=False)

    class Meta:
        model = Email
        fields = ['recipient', 'subject', 'message', 'sender_email', 'attachment']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Extract 'user' if provided
        super().__init__(*args, **kwargs)
        if user:
            self.fields['sender_email'].initial = user.email
        self.user = user

    def save(self, commit=True):
        email = super().save(commit=False)
        if self.user:
            email.user = self.user  # Associate the email with the user
        if commit:
            email.save()
        return email        

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture']     