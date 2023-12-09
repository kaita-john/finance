from django.db import models

from academic_year.models import AcademicYear
from models import ParentModel


class Term(ParentModel):
    term_name = models.CharField(max_length=255)
    begin_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False, null = True)
    school_id = models.UUIDField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.is_current:
            Term.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.term_name
