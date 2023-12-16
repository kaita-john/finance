from django.db import models

from constants import *
from models import ParentModel


class Staff(ParentModel):
    fname = models.CharField(max_length=255)
    lname = models.CharField(max_length=255)
    staffNo = models.CharField(max_length=255)
    phoneNo = models.CharField(max_length=255)
    gender = models.CharField(max_length=255)
    emailAddress = models.CharField(max_length=255, null=True, blank=True)
    idNumber = models.CharField(max_length=255)
    category = models.CharField(max_length=255, choices=TEACHINGCHOICES, default='TEACHING', )
    school = models.UUIDField(max_length=255, blank=True, null=True)

    def __str__(self):
        return str(self.id)
