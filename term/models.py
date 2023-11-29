from django.db import models

from utils import ParentModel


class Term(ParentModel):
    term_name = models.CharField(max_length=255)
    year = models.CharField(max_length=255, blank=False)
    begin_date = models.DateField()
    end_date = models.DateField()
    school_id = models.UUIDField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.term_name
