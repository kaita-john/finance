import uuid

from django.db import models
from django.db.models import DO_NOTHING

from school_categories.models import SchoolCategory
from school_types.models import SchoolType


class DatingModel(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# Create your models here.
class School(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phonenumber = models.CharField(max_length=20, blank=False)
    location = models.CharField(max_length=255, blank=True, default="None")
    city = models.CharField(max_length=255, blank=False, default="None")
    country = models.CharField(max_length=255, blank=False, default="Kenya")

    first_name = models.CharField(max_length=255, default="None")
    last_name = models.CharField(max_length=255, default="None")
    contact_fullname = models.CharField(max_length=255, default="None", blank=True)
    contact_mobile = models.CharField(max_length=255, default="None")
    contact_lastname = models.CharField(max_length=255, default="None")
    contact_workphone = models.CharField(max_length=255, default="None")
    postal_address = models.CharField(max_length=255, default="None")
    postal_code = models.CharField(max_length=255, default="None")

    schoolcode = models.CharField(max_length=255, default="None")
    schoolgender = models.CharField(max_length=255, default="MIXED")
    boardingstatus = models.CharField(max_length=255, default="MIXED")

    school_type = models.ForeignKey(SchoolType, on_delete=DO_NOTHING, related_name="schools", null=True)
    school_category = models.ForeignKey(SchoolCategory, on_delete=DO_NOTHING, related_name="schools", null=True)

    def __str__(self):
        return f"{self.name} - {self.id}"