# src/pages/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

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
