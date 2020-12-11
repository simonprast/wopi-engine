#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django import forms
from django.contrib import admin

from .models import IDSubmission


class IDSubmissionCreationForm(forms.ModelForm):
    # A form for creating new id submission.
    class Meta:
        model = IDSubmission
        exclude = ()


class IDSubmissionChangeForm(forms.ModelForm):
    # A form for updating id submission.
    class Meta:
        model = IDSubmission
        exclude = ()


class IDSubmissionAdmin(admin.ModelAdmin):
    # The forms to add and change submission
    form = IDSubmissionChangeForm
    add_form = IDSubmissionCreationForm

    list_display = ("id", "submitter", "latest", "verified", "denied")
    list_filter = ("submitter", "latest", "verified")
    fieldsets = (
        (None, {"fields": ("submitter",
                           "document", "latest", "verified", "denied")}),
        # ("Data", {"fields": ("data",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("submitter", "document", "verified", "denied")}
         ),
    )
    search_fields = ("submitter",)
    ordering = ("id", "submitter", "latest", "verified")
    filter_horizontal = ()


admin.site.register(IDSubmission, IDSubmissionAdmin)