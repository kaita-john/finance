from django.contrib import admin

from payment_methods.models import PaymentMethod

# Register your models here.
admin.site.register(PaymentMethod)