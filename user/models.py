#
# Created on Mon Nov 02 2020
#
# Copyright (c) 2020 - Simon Prast
#


import phonenumbers

from django.conf import settings
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, username, password, **kwargs):
        email_raw = kwargs.get("email", None)
        email = self.normalize_email(
            email_raw) if email_raw is not None else None
        utype = kwargs.get("utype", 1)
        # is_staff = kwargs.get("is_staff", False)

        if not username:
            raise ValueError("Users must have an username")

        user = self.model(
            username=username,
            email=email,
            utype=utype,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None):
        user = self.create_user(
            username=username,
            password=password,
            utype=9
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    username = models.CharField(max_length=40, unique=True)
    email = models.EmailField(
        verbose_name="Email Address", null=True, max_length=320, unique=True)
    utype = models.IntegerField(verbose_name="User Type", default=0)
    is_admin = models.BooleanField(default=False)

    first_name = models.CharField(max_length=128, null=True)
    last_name = models.CharField(max_length=128, null=True)
    # customer_id = models.CharField(max_length=128, null=True)

    # Contact info
    phone = models.CharField(max_length=15, null=True)

    # ID verification
    verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "username"
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
        User.objects.get(username=settings.ADMIN_USER) \
            .set_password(settings.ADMIN_PASSWORD)
        print("EXISTING ADMIN ACCOUNT (SET ADMIN PASSWORD): " + settings.ADMIN_USER)
    else:
        User.objects.create_superuser(
            settings.ADMIN_USER, settings.ADMIN_PASSWORD)
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
