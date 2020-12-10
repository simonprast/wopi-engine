#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django import forms
from django.contrib import admin

from .models import DamageReport, Message


class DamageReportCreationForm(forms.ModelForm):
    # A form for creating new id submission.
    class Meta:
        model = DamageReport
        exclude = ()


class DamageReportChangeForm(forms.ModelForm):
    # A form for updating id submission.
    class Meta:
        model = DamageReport
        exclude = ()


class DamageReportAdmin(admin.ModelAdmin):
    # The forms to add and change submission
    form = DamageReportChangeForm
    add_form = DamageReportCreationForm

    list_display = ("id", "status", "get_policyid", "submitter", "denied")
    list_filter = ("status", "policy", "submitter")
    fieldsets = (
        (None, {"fields": ("policy", "submitter", "status", "denied")}),
        # ("Data", {"fields": ("submission_data",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("policy", "submitter", "status", "denied")}
         ),
    )
    search_fields = ("policy", "policy_id", "submitter", "status")
    ordering = ("id", "status", "policy", "policy_id", "submitter")
    filter_horizontal = ()

    def get_policyid(self, obj):
        return str(obj.policy.insurance) + ", " + str(obj.policy.policy_id)
    get_policyid.admin_order_field = 'policy_id'
    get_policyid.short_description = 'Policy'


admin.site.register(DamageReport, DamageReportAdmin)


class MessageCreationForm(forms.ModelForm):
    # A form for creating new id submission.
    class Meta:
        model = Message
        exclude = ()


class MessageChangeForm(forms.ModelForm):
    # A form for updating id submission.
    class Meta:
        model = Message
        exclude = ()


class MessageAdmin(admin.ModelAdmin):
    # The forms to add and change submission
    form = MessageChangeForm
    add_form = MessageCreationForm

    list_display = ("id", "get_reportid", "datetime", "sender", "message_body")
    list_filter = ("report", "sender")
    fieldsets = (
        (None, {"fields": ("report", "sender", "datetime", "message_body")}),
        # ("Data", {"fields": ("submission_data",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("report", "sender", "datetime", "message_body")}
         ),
    )
    search_fields = ("report", "sender", "message_body")
    ordering = ("id", "datetime", "report", "sender")
    filter_horizontal = ()

    def get_reportid(self, obj):
        return str(obj.report.id) + \
            " (" + str(obj.report.policy.insurance) + \
            ", " + str(obj.report.policy.policy_id) + ")"
    get_reportid.short_description = 'Damage Report'


admin.site.register(Message, MessageAdmin)
