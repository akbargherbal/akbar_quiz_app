# src/pages/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

# Import UserCollection model
from .models import UserCollection  # <<< ADD THIS IMPORT

# Get the custom user model if you ever define one, otherwise the default User
User = get_user_model()


class SignUpForm(UserCreationForm):
    # You can add extra fields here if needed (e.g., email)
    # By default, UserCreationForm includes username, password1, password2
    email = forms.EmailField(
        max_length=254, help_text="Required. Inform a valid email address."
    )

    class Meta(UserCreationForm.Meta):
        model = User
        # Specify fields to include, adding email
        fields = (
            "username",
            "email",
        )  # Add other fields like 'first_name', 'last_name' if desired

    # You could add custom validation here if required
    # def clean_email(self):
    #     ...


# --- Existing EditProfileForm ---
class EditProfileForm(forms.ModelForm):
    email = forms.EmailField(
        max_length=254,
        help_text="Required. Please enter a valid email address.",
        widget=forms.EmailInput(
            attrs={
                "class": "appearance-none relative block w-full px-3 py-3 border border-border placeholder-text-muted text-text-primary bg-tag-bg/40 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent focus:z-10 text-sm sm:text-base"
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "email",
        )  # Add 'first_name', 'last_name' here if you want to edit them too

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # You can add custom initialization here if needed,
        # e.g., making fields not required if they are optional
        # For now, email is required by default based on the User model.

    def clean_email(self):
        email = self.cleaned_data.get("email")
        # Optional: Add custom email validation if needed,
        # e.g., checking if the email is already in use by another user (excluding the current user)
        # For simplicity, we'll rely on Django's default unique check for email if it's set on the User model.
        # If User model doesn't enforce unique email, you might want to add a check here:
        # if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
        #     raise forms.ValidationError("This email address is already in use.")
        return email


# --- NEW FORM FOR UserCollection ---
class UserCollectionForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100,
        help_text="Enter a name for your collection (e.g., 'My Study Set', 'Weak Areas').",
        widget=forms.TextInput(
            attrs={
                "class": "appearance-none relative block w-full px-3 py-3 border border-border placeholder-text-muted text-text-primary bg-tag-bg/40 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent focus:z-10 text-sm sm:text-base",
                "placeholder": "Collection Name",
            }
        ),
    )
    description = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "class": "appearance-none relative block w-full px-3 py-3 border border-border placeholder-text-muted text-text-primary bg-tag-bg/40 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent focus:z-10 text-sm sm:text-base",
                "placeholder": "Optional: A brief description of what this collection is for.",
            }
        ),
        required=False,
        help_text="Optional: Describe what this collection is for.",
    )

    class Meta:
        model = UserCollection
        fields = ["name", "description"]
        # We don't include 'user' here because it will be set automatically in the view.
        # We don't include 'quizzes' as they will be managed separately.
