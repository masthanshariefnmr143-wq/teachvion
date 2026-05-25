from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser


class RegisterForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    role = forms.ChoiceField(choices=[
        ('student', 'Student'),
        ('trainer', 'Trainer'),
        ('admin', 'Admin'),
    ])
    password1 = forms.CharField(widget=forms.PasswordInput, min_length=6)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned

    def save(self):
        data = self.cleaned_data
        user = CustomUser.objects.create_user(
            username=data['email'],
            email=data['email'],
            password=data['password1'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data['role'],
        )
        return user


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if not CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("No account found with this email.")
        return email


class OTPVerifyForm(forms.Form):
    email = forms.EmailField(widget=forms.HiddenInput)
    otp = forms.CharField(max_length=6, min_length=6)


class ResetPasswordForm(forms.Form):
    email = forms.EmailField(widget=forms.HiddenInput)
    otp = forms.CharField(widget=forms.HiddenInput)
    password1 = forms.CharField(widget=forms.PasswordInput, min_length=6)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password1') != cleaned.get('password2'):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone', 'bio', 'profile_pic']

