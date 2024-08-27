from django.contrib.auth.forms import (PasswordChangeForm, UserChangeForm,
                                       UserCreationForm)

from .models import GTUser


class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = GTUser
        fields = ('email',)


class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = GTUser
        fields = ('email',)


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = 'Current Password'
        self.fields['new_password1'].label = 'New Password'
        self.fields['new_password2'].label = 'Confirm New Password'
        self.fields['old_password'].help_text = 'Enter your current password'
        self.fields['new_password1'].help_text = 'Enter your new password'
        self.fields['new_password2'].help_text = 'Confirm your new password'
        self.fields['old_password'].widget.attrs.update({'autofocus': True})

        # placeholder
        self.fields['old_password'].widget.attrs.update(
            {'placeholder': 'Current Password'})
        self.fields['new_password1'].widget.attrs.update(
            {'placeholder': 'New Password'})
        self.fields['new_password2'].widget.attrs.update(
            {'placeholder': 'Confirm New Password'})
