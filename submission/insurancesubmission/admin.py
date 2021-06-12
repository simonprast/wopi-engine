#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django import forms
from django.contrib import admin

from .models import InsuranceSubmission, Document, DocumentToken


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

    list_display = ("id", "policy_id", "insurance",
                    "submitter", "active", "denied")
    list_filter = ("insurance", "submitter", "active", "denied")
    fieldsets = (
        (
            None, {
                "classes": ("wide",),
                "fields": (
                    "status",
                    "insurance",
                    "submitter",
                    "policy_document",
                    "active",
                    "denied",
                    "policy_id"
                )
            }
        ),
        (
            "Data", {
                "fields": (
                    "data",
                )
            }
        ),
    )

    add_fieldsets = fieldsets
    search_fields = ("id", "policy_id", "insurance", "submitter")
    ordering = ("id", "policy_id", "insurance", "submitter")
    filter_horizontal = ()


class DocumentTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "document", "token", "expired", "called", "signed")

    search_fields = ("user",)


admin.site.register(InsuranceSubmission, InsuranceSubmissionAdmin)
admin.site.register(Document)
admin.site.register(DocumentToken, DocumentTokenAdmin)
