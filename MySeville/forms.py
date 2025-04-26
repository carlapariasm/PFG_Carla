from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.contrib.auth.forms import SetPasswordForm

class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].help_text = ''
        self.fields['new_password2'].help_text = ''


class RegistroForm(UserCreationForm):
    
    NATIONALITY_CHOICES = CustomUser.NATIONALITY_CHOICES

    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    username = forms.CharField(max_length=150, required=True, )
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    address = forms.CharField(widget=forms.Textarea, required=True)
    nationality = forms.ChoiceField(
        choices=NATIONALITY_CHOICES,
        required=True,
        label="Nationality",
        widget=forms.Select(attrs={'class': 'nationality-input'})
    )
    email = forms.EmailField(required=True, label="Email", widget=forms.EmailInput) #(attrs={'class': 'form-control'})

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email', 'date_of_birth', 'address', 'nationality', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = ''  
        self.fields['password2'].help_text = ''


class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].help_text = ''
        self.fields['new_password2'].help_text = ''



class EditarPerfilForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email', 'date_of_birth', 'address', 'nationality']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'nationality': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True

