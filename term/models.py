from django.db import models

from models import ParentModel


class Term(ParentModel):
    term_name = models.CharField(max_length=255)
    begin_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False, null = True)
    school_id = models.UUIDField(max_length=255, blank=True, null=True)
    academic_year = models.CharField(max_length=255, default="2023", null=True)

    def save(self, *args, **kwargs):
        if self.term_name:
            self.term_name = self.term_name.upper()
        if self.academic_year:
            self.academic_year = self.academic_year.upper()
        if self.is_current:
            Term.objects.filter(school_id=self.school_id).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.term_name} - {self.id}"
