from django.db import models

from utils import ParentModel


class Classes(ParentModel):
    classname = models.CharField(max_length=255)
    graduation_year = models.CharField(max_length=255)
    graduation_month = models.CharField(max_length=255)
    school_id = models.UUIDField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.classname} - {self.graduation_month} {self.graduation_year}"
