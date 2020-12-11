#
# Created on Mon Nov 02 2020
#
# Copyright (c) 2020 - Simon Prast
#

import os
import phonenumbers
import uuid

from django.conf import settings
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.db import models


class UserManager(BaseUserManager):
    def create_user(
        self,
        username=None,
        email=None,
        first_name=None,
        last_name=None,
        phone=None,
        password=None,
        **kwargs
    ):

        serializers = kwargs.get('serializers', None)
        email = self.normalize_email(
            email) if email is not None else None
        utype = kwargs.get("utype", 1)

        if User.objects.filter(email=email).count() > 0:
            if serializers:
                return False
                # raise serializers.ValidationError(
                #     {'DuplicateEmail': ['User with this E-Mail already exists.']})
            else:
                raise ValueError('User with this E-Mail already exists.')

        if not email:
            raise ValueError('User must have set an E-Mail')

        if not username:
            username = email

        validated_phone = None
        if phone:
            phone_number = check_phone_number(phone)
            if not phone_number:
                raise ValueError("Phone number is not valid")
            else:
                validated_phone = phone_number

        user = self.model(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=validated_phone,
            utype=utype,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        username=None,
        email=None,
        password=None
    ):

        user = self.create_user(
            username=username,
            password=password,
            email=email,
            utype=9
        )

        user.is_admin = True
        user.save(using=self._db)
        return user


def create_path(instance, filename):
    folder = 'pictures/' + str(uuid.uuid4())
    os.makedirs(os.path.join(settings.MEDIA_ROOT, folder))
    return os.path.join(folder, filename)


class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=40, unique=True)
    email = models.EmailField(
        verbose_name="Email Address", max_length=320, unique=True)
    utype = models.IntegerField(verbose_name="User Type", default=0)
    is_admin = models.BooleanField(default=False)

    advisor = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True)
    picture = models.ImageField(
        upload_to=create_path, null=True, blank=True
    )

    first_name = models.CharField(max_length=128, null=True)
    last_name = models.CharField(max_length=128, null=True)
    # customer_id = models.CharField(max_length=128, null=True)

    # Contact info
    phone = models.CharField(max_length=20, null=True)

    # ID verification
    verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"

    REQUIRED_FIELDS = []

    def __str__(self):
        string = ''
        string += self.first_name + ' ' if self.first_name else ''
        string += self.last_name if self.last_name else ''
        if string == '':
            string = self.username
        return string

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


def create_admin_user():
    # This is called within the root URLs file at francy.urls, because, at this point, all modules / the user module is
    # already loaded. This function ensures that a default administrative user account exists.
    # Username and password are set according to environment variables ADMIN_USER and ADMIN_PASSWORD.
    # CAUTION! When changing ADMIN_USER at runtime, the old ADMIN_USER account is not automatically deleted.

    if User.objects.filter(username=settings.ADMIN_USER).exists():
        user = User.objects.get(username=settings.ADMIN_USER)
        user.set_password(settings.ADMIN_PASSWORD)
        user.email = settings.ADMIN_MAIL
        if not settings.DEBUG:
            user.save()
        print("EXISTING ADMIN ACCOUNT (SET ADMIN PASSWORD): " + settings.ADMIN_USER)
    else:
        User.objects.create_superuser(
            settings.ADMIN_USER, settings.ADMIN_MAIL, settings.ADMIN_PASSWORD)
        print("CREATE NEW ADMIN ACCOUNT: " + settings.ADMIN_USER)


def check_phone_number(number):
    # Try to parse the phone number string, if this is not possible it will return False
    try:
        n = phonenumbers.parse(number, 'AT')
    except phonenumbers.phonenumberutil.NumberParseException:
        return False

    if not phonenumbers.is_valid_number(n):
        return False

    # e.g. +436641234567
    return '+' + str(n.country_code) + str(n.national_number)
