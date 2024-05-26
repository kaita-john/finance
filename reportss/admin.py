from django.contrib import admin

from reportss.models import BalanceTracker, OpeningClosingBalances

admin.site.register(BalanceTracker)
admin.site.register(OpeningClosingBalances)