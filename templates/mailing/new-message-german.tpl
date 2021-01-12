{% extends "mail_templated/base.tpl" %}

{% block subject %}
Dein Ausweis wurde bestätigt - SPARDA Versicherungen
{% endblock %}

{% block html %}

<style>
    .button {
        border-radius: 2px;
    }

    .button a {
        padding: 8px 12px;
        border: 1px solid #E87405;
        border-radius: 2px;
        font-family: Helvetica, Arial, sans-serif;
        font-size: 14px;
        color: #ffffff;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
}

</style>

Hallo {{ user.first_name }}!
<p>
    Du hast einen neue Nachricht in deinem SPARDA-Postfach.
</p>

<table width="100%" cellspacing="0" cellpadding="0">
    <tr>
        <td>
            <table cellspacing="0" cellpadding="0">
                <tr>
                    <td class="button" bgcolor="#E87405">
                        <a class="link" href="https://app.spardaplus.at/">Zum SPARDA-Portal</a>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<p>Mit freundlichen Grüßen<br>
Dein SPARDA Team</p>
{% endblock %}