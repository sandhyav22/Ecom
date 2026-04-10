from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import UserProfile


class PersonalInfoForm(forms.ModelForm):
    """Updates Django User + UserProfile together."""
    first_name = forms.CharField(max_length=50,  widget=forms.TextInput(attrs={'placeholder': 'Ex.john'}))
    last_name  = forms.CharField(max_length=50,  widget=forms.TextInput(attrs={'placeholder': 'Ex.Doe'}))
    email      = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Enter E-Mail Id'}))
    phone      = forms.CharField(max_length=15,  widget=forms.TextInput(attrs={'placeholder': 'Enter Phone Number'}), required=False)
    gender     = forms.ChoiceField(choices=[('', 'Select Gender'), ('M', 'Male'), ('F', 'Female'), ('O', 'Other')], required=False)
    address    = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Enter your address', 'rows': 3}), required=False)
    avatar     = forms.ImageField(required=False)

    class Meta:
        model  = UserProfile
        fields = ['phone', 'gender', 'address', 'avatar']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial  = self.user.last_name
            self.fields['email'].initial      = self.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name  = self.cleaned_data['last_name']
            self.user.email      = self.cleaned_data['email']
            self.user.save()
        if commit:
            profile.save()
        return profile


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter current password'})
    )
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter new password'})
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm new password'})
    )
