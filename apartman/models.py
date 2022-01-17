from django.db import models
import jwt

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin
)
from django.db import models

class Apartman(models.Model):
    url = models.CharField(db_index=True, max_length=255, unique=True, null=True)

    USERNAME_FIELD = 'url'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.url

    def get_url(self):
        return self.url

    def get_first_date(self):
        return self.first_date

    def get_url(self):
        return self.last_date

class Customer(AbstractBaseUser):
    uid = models.CharField(primary_key=True, db_index=True, max_length=255, unique=True)
    name = models.CharField(db_index=True, max_length=255)
    apartman = models.ForeignKey(Apartman, on_delete=models.CASCADE)
    begin_date = models.DateField()
    end_date = models.DateField()
    password = None
    last_login = None

    USERNAME_FIELD = 'name'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.name

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_apartman(self):
        return self.apartman

    def get_begin_date(self):
        return self.begin_date

    def get_end_date(self):
        return self.end_date
