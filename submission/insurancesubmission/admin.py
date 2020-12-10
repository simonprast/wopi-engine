#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django import forms
from django.contrib import admin

from .models import InsuranceSubmission


class InsuranceSubmissionCreationForm(forms.ModelForm):
    # A form for creating new submission.
    class Meta:
        model = InsuranceSubmission
        exclude = ()


class InsuranceSubmissionChangeForm(forms.ModelForm):
    # A form for updating submission.
    class Meta:
        model = InsuranceSubmission
        exclude = ()


class InsuranceSubmissionAdmin(admin.ModelAdmin):
    # The forms to add and change submission
    form = InsuranceSubmissionChangeForm
    add_form = InsuranceSubmissionCreationForm

    list_display = ("id", "insurance", "submitter", "active")
    list_filter = ("insurance", "submitter", "active")
    fieldsets = (
        (None, {"fields": ("insurance", "submitter", "active", "denied", "policy_id")}),
        ("Data", {"fields": ("data",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("insurance", "submitter", "data")}
         ),
    )
    search_fields = ("insurance", "submitter")
    ordering = ("insurance", "submitter")
    filter_horizontal = ()


admin.site.register(InsuranceSubmission, InsuranceSubmissionAdmin)
