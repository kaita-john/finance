import uuid

from django.core.exceptions import ValidationError
from django.db import models


# Create your models here.
class ParentModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Meta:
        abstract = True

class AcademicYear(ParentModel):
    academic_year = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False, null = True)
    school_id = models.UUIDField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.academic_year:
            self.academic_year = self.academic_year.upper()

        existing_academic_year = AcademicYear.objects.filter(
            academic_year=self.academic_year,
            school_id=self.school_id
        ).exclude(pk=self.pk)

        if existing_academic_year.exists():
            raise ValidationError('Academic years must be unique for the same school.')

        if self.is_current:
            AcademicYear.objects.filter(school_id=self.school_id).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.academic_year





