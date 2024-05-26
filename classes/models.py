from django.db import models

from models import ParentModel


class Classes(ParentModel):
    classname = models.CharField(max_length=255)
    graduation_year = models.CharField(max_length=255)
    graduation_month = models.CharField(max_length=255)
    school_id = models.UUIDField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.classname:
            self.classname = self.classname.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.classname} - {self.graduation_month} {self.graduation_year}"
