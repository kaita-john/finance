import uuid
from django.db import models


class Mpesaconfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(max_length=255, blank=True, null=True)
    is_saved = models.BooleanField(default=False, null=True, blank=True)
    shortcode = models.CharField(max_length=255)
    paybill_number = models.CharField(max_length=255, blank=True, null=True, default="0000")
    consumer_key = models.CharField(max_length=255)
    passkey = models.CharField(max_length=255)
    consumer_secret = models.CharField(max_length=255)
    access_token_url = models.CharField(max_length=255, blank=True, null=True, default='https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials')
    checkout_url = models.CharField(max_length=255, blank=True, null=True, default='https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest')
    callback_url = models.CharField(max_length=255, blank=True, null=True, default='https://tafatalk.co.ke/api/v1/payments/callback')
    registration_url = models.CharField(max_length=255, blank=True, null=True, default='https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl')
    token_url = models.CharField(max_length=255, blank=True, null=True, default='https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials')

    def save(self, *args, **kwargs):
        super(Mpesaconfig, self).save(*args, **kwargs)
        self.is_saved = True
        super(Mpesaconfig, self).save(update_fields=['is_saved'])

    def __str__(self):
        return f"{self.id}"


