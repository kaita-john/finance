from django.db import models

from bursaries.models import Bursary
from classes.models import Classes
from models import ParentModel
from students.models import Student


class Item(ParentModel):
    item_date = models.DateField(auto_now_add=True, null=True)
    student = models.ForeignKey(Student, default=None, on_delete=models.CASCADE, related_name="items")
    bursary = models.ForeignKey(Bursary, null=True, default=None, on_delete=models.CASCADE, related_name="items")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    school_id = models.UUIDField(null=True, blank=True, default=None, max_length=255)
    student_class = models.ForeignKey(Classes, null=True, on_delete=models.CASCADE, related_name="items")

    def __str__(self):
        return f"{self.id}"



