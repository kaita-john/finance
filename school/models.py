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

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.upper()
        if self.location:
            self.location = self.location.upper()
        if self.city:
            self.city = self.city.upper()
        if self.country:
            self.country = self.country.upper()
        if self.first_name:
            self.first_name = self.first_name.upper()
        if self.last_name:
            self.last_name = self.last_name.upper()
        if self.contact_fullname:
            self.contact_fullname = self.contact_fullname.upper()
        if self.contact_lastname:
            self.contact_lastname = self.contact_lastname.upper()
        if self.postal_address:
            self.postal_address = self.postal_address.upper()
        if self.postal_code:
            self.postal_code = self.postal_code.upper()
        if self.schoolcode:
            self.schoolcode = self.schoolcode.upper()
        if self.schoolgender:
            self.schoolgender = self.schoolgender.upper()
        if self.boardingstatus:
            self.boardingstatus = self.boardingstatus.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.id}"