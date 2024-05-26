from django.contrib import admin

from voteheads.models import VoteHead, VoteheadConfiguration

# Register your models here.
admin.site.register(VoteHead)
admin.site.register(VoteheadConfiguration)