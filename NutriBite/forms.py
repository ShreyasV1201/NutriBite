from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User 
from .models import Recipe
  # Import your custom User model

class SignInForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password',
    }))

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User  # Use your custom User model
        fields = ['username', 'password1', 'password2']

class RecipeSearchForm(forms.Form):
    query = forms.CharField(
        label="Search recipes",
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "e.g. chicken curry"
        })
    )

class AddRecipeForm(forms.Form):
    title = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control rounded-3',
            'placeholder': 'Enter recipe name…'
        }),
        label='Title'
    )
    ingredients = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control rounded-3',
            'rows': 3,
            'placeholder': 'List your ingredients, one per line…'
        }),
        label='Ingredients'
    )
    preparation = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control rounded-3',
            'rows': 4,
            'placeholder': 'Describe the preparation steps…'
        }),
        label='Preparation'
    )

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['title', 'ingredients', 'preparation']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control rounded-3',
                'placeholder': 'Enter recipe name…'
            }),
            'ingredients': forms.Textarea(attrs={
                'class': 'form-control rounded-3',
                'rows': 4,
                'placeholder': 'List your ingredients, one per line…'
            }),
            'preparation': forms.Textarea(attrs={
                'class': 'form-control rounded-3',
                'rows': 6,
                'placeholder': 'Describe the preparation steps…'
            }),
        }