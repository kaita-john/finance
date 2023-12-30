from datetime import datetime, timedelta

from django.db import models

from models import ParentModel


# Create your models here.
class FinancialYear(ParentModel):
    financial_year_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    school = models.UUIDField(max_length=255, blank=True, null=True)
    previous_financial_year = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True)
    is_current = models.BooleanField(default=False, null=True)

    def __str__(self):
        return self.financial_year_name

    @staticmethod
    def get_month_info(financial_year):
        start_month = financial_year.start_date.month
        start_year = financial_year.start_date.year
        end_year = financial_year.end_date.year

        month_info_list = []

        for month_number in range(1, 13):
            start_date = datetime(start_year, month_number, 1)
            end_date = (datetime(end_year, month_number % 12 + 1, 1) - timedelta(days=1)).replace(hour=23, minute=59,second=59)

            month_info = {
                'start_date': start_date,
                'end_date': end_date,
                'month_number': month_number
            }

            month_info_list.append(month_info)

        return month_info_list



