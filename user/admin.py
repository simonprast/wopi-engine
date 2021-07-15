#
# Created on Mon Nov 02 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from .models import ResetPasswordToken, User, VerifyEmailToken


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("username",)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin"s
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ()

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ("email", "first_name", "last_name",
                    "advisor", "get_insurance")
    list_filter = ()
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "verified",
                    "password"
                )
            }
        ),
        (
            "Personal Information", {
                "fields": (
                    "first_name",
                    "last_name",
                    "sex",
                    "birthdate",
                    "phone",
                    "phone_verified"
                )
            }
        ),
        (
            "Permissions", {
                "fields": (
                    "utype",
                    "devices"
                )
            }
        ),
        (
            "Advisor", {
                "fields": (
                    "advisor",
                    "picture"
                )
            }
        )
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "verified"
                )
            }
        ),
        (
            "Personal Information", {
                "fields": (
                    "first_name",
                    "last_name",
                    "sex",
                    "birthdate",
                    "phone"
                )
            }
        ),
        (
            "Permissions", {
                "fields": (
                    "utype",
                )
            }
        ),
        (
            "Advisor", {
                "fields": (
                    "advisor",
                    "picture"
                )
            }
        )
    )

    search_fields = ("username", "email")
    ordering = ("username", "email")
    filter_horizontal = ()

    def get_insurance(self, obj):
        submissions = obj.insurancesubmission_set.all()
        policies = []
        for submission in submissions:
            print(submission)
            policy_string = str(submission.insurance)
            if submission.policy_id:
                policy_string += ' (' + submission.policy_id + ')'
            policies.append(policy_string)
        return policies
    get_insurance.short_description = 'Insurance Submissions'


# Now register the new UserAdmin...
admin.site.register(User, UserAdmin)
# ... and, since we"re not using Django"s built-in permissions,
# unregister the Group model from admin.
admin.site.unregister(Group)


class EmailTokenAdmin(BaseUserAdmin):
    # form = EmailTokenChangeForm
    # add_form = UserCreationForm

    list_display = ("user", "token")
    list_filter = ()
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "token"
                )
            }
        ),
    )

    search_fields = ("user", "token")
    ordering = ("user", "token")
    filter_horizontal = ()


admin.site.register(VerifyEmailToken, EmailTokenAdmin)


class PasswordTokenAdmin(BaseUserAdmin):
    # form = EmailTokenChangeForm
    # add_form = UserCreationForm

    list_display = ("user", "token")
    list_filter = ()
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "token"
                )
            }
        ),
    )

    search_fields = ("user", "token")
    ordering = ("user", "token")
    filter_horizontal = ()


admin.site.register(ResetPasswordToken, PasswordTokenAdmin)
