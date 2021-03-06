{% extends "mail_templated/base.tpl" %}

{% block subject %}
Willkommen beim SPARDA Versicherungsportal!
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
<p>Herzlich willkommen beim Kundenportal vom SPARDA Versicherungsservice. Danke, dass Du Dich bei uns registriert hast.</p>
<p>Um zu bestätigen, dass Du Zugriff auf diese E-Mail Adresse hast, klicke bitte auf folgenden Link:</p>

<table width="100%" cellspacing="0" cellpadding="0">
    <tr>
        <td>
            <table cellspacing="0" cellpadding="0">
                <tr>
                    <td class="button" bgcolor="#E87405">
                        <a class="link" href="https://app.spardaplus.at/verify/{{ token }}">E-Mail Adresse bestätigen</a>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<p>Du wirst in Deinem E-Mail Postfach gelegentlich über Nachrichten zu Deinen Versicherungen und über Neuigkeiten zu Deinem SPARDA-Account informiert.<br>
    Weiters kannst Du Dein Passwort mit deiner E-Mail Adresse zurücksetzen, solltest Du es mal vergessen.</p>

<p>Mit freundlichen Grüßen<br>
Dein SPARDA Team</p>
{% endblock %}