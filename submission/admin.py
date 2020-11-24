#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django import forms
from django.contrib import admin

from .models import Submission


class SubmissionCreationForm(forms.ModelForm):
    # A form for creating new submission.
    class Meta:
        model = Submission
        exclude = ()


class SubmissionChangeForm(forms.ModelForm):
    # A form for updating submission.
    class Meta:
        model = Submission
        exclude = ()


class SubmissionAdmin(admin.ModelAdmin):
    # The forms to add and change submission
    form = SubmissionChangeForm
    add_form = SubmissionCreationForm

    list_display = ("submission_insurance", "submission_submitter")
    list_filter = ("submission_insurance", "submission_submitter")
    fieldsets = (
        (None, {"fields": ("submission_insurance", "submission_submitter")}),
        ("Data", {"fields": ("submission_data",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("submission_insurance", "submission_submitter", "submission_data")}
         ),
    )
    search_fields = ("submission_insurance", "submission_submitter")
    ordering = ("submission_insurance", "submission_submitter")
    filter_horizontal = ()


admin.site.register(Submission, SubmissionAdmin)
