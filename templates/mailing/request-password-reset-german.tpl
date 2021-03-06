{% extends "mail_templated/base.tpl" %}

{% block subject %}
Zurücksetzen Deines SPARDA-Passworts
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
<p>Wir haben eine Anfrage darüber erhalten, Dein Passwort für das SPARDA-Kundenportal zurückzusetzen.</p>
<p>Unter diesem Link kannst Du ein neues Passwort festlegen:</p>


<table width="100%" cellspacing="0" cellpadding="0">
    <tr>
        <td>
            <table cellspacing="0" cellpadding="0">
                <tr>
                    <td class="button" bgcolor="#E87405">
                        <a class="link" href="https://app.spardaplus.at/reset/{{ token }}/{{ email }}">Passwort zurücksetzen</a>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<p>
    Falls du nicht um die Zurücksetzung Deines Passworts gebeten hast, kannst Du diese Mail ignorieren.<br>
    Sollte Dich diese Nachricht öfters erreichen, wende Dich bitte an deinen Betreuer.
</p>

<p>Mit freundlichen Grüßen<br>
Dein SPARDA Team</p>
{% endblock %}