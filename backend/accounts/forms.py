from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, KYCVerification


class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email address'
        })
    )
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your phone number'
        })
    )
    referral_code_input = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter referral code if you have one'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Bootstrap classes to all fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email

    def clean_referral_code_input(self):
        code = self.cleaned_data.get('referral_code_input')
        if code:
            if not User.objects.filter(referral_code=code).exists():
                raise forms.ValidationError('Invalid referral code.')
        return code

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data.get('phone', '')

        if commit:
            user.save()

            # Handle referral
            referral_code = self.cleaned_data.get('referral_code_input')
            if referral_code:
                try:
                    referrer = User.objects.get(referral_code=referral_code)
                    user.referred_by = referrer
                    user.save()
                except User.DoesNotExist:
                    pass

        return user


class UserLoginForm(AuthenticationForm):
    """Form for user login"""

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or Email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )


class KYCForm(forms.ModelForm):
    """ID-verification submission (personal details + address + documents)."""

    info_correct = forms.BooleanField(
        required=True,
        error_messages={'required': 'Please confirm your information is correct.'},
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='All the personal information I have entered is correct.',
    )
    is_individual = forms.BooleanField(
        required=True,
        error_messages={'required': 'Please confirm you are registering as an individual.'},
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=('I certify that I am registering as an individual (and beneficial owner) and not '
               'as an agent or representative of a third-party corporate entity.'),
    )

    class Meta:
        model = KYCVerification
        fields = [
            'first_name', 'last_name', 'phone', 'date_of_birth', 'gender', 'telegram_username',
            'country', 'state', 'city', 'postal_code', 'address_line_1', 'address_line_2',
            'document_type', 'document_image', 'selfie_image',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name*'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name*'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'telegram_username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telegram Username'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country*'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City*'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Zip / Postal Code*'}),
            'address_line_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 1*'}),
            'address_line_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 2'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'document_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'selfie_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    # Required fields (match the reference asterisks)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ['first_name', 'last_name', 'gender', 'country', 'city',
                     'postal_code', 'address_line_1', 'document_type',
                     'document_image', 'selfie_image']:
            self.fields[name].required = True
        for name in ['phone', 'date_of_birth', 'telegram_username', 'state', 'address_line_2']:
            self.fields[name].required = False
