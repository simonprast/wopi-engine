from django.conf import settings


def send_code(number):
    # Import TWILIO_CLIENT from settings.
    client = settings.TWILIO_CLIENT

    # Send an SMS message to the specified number.
    verification = client.verify \
        .services(settings.TWILIO_SERVICE_ID) \
        .verifications \
        .create(to=number, channel='sms')

    print(verification)


def verify_code(number, code):
    # Import TWILIO_CLIENT from settings.
    client = settings.TWILIO_CLIENT

    # Check a given verification code for a phone number.
    verification_check = client.verify \
        .services(settings.TWILIO_SERVICE_ID) \
        .verification_checks \
        .create(to=number, code=code)

    return verification_check.status
