#
# Created on Mon Nov 02 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django import forms
from django.contrib import admin

from .models import Insurance


class InsuranceCreationForm(forms.ModelForm):
    # A form for creating new insurances.
    class Meta:
        model = Insurance
        exclude = ()


class InsuranceChangeForm(forms.ModelForm):
    # A form for updating insurances.
    class Meta:
        model = Insurance
        exclude = ()


class InsuranceAdmin(admin.ModelAdmin):
    # The forms to add and change insurances
    form = InsuranceChangeForm
    add_form = InsuranceCreationForm

    list_display = ("insurance_name", "insurance_key")
    list_filter = ()
    fieldsets = (
        (None, {"fields": ("insurance_name", "insurance_key", "insurance_subtitle")}),
        ("Fields", {"fields": ("insurance_fields",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("insurance_name", "insurance_key", "insurance_subtitle", "insurance_fields")}
         ),
    )
    search_fields = ("insurance_name", "insurance_key")
    ordering = ("insurance_name", "insurance_key")
    filter_horizontal = ()


admin.site.register(Insurance, InsuranceAdmin)
