from django.contrib import admin

from .models import Candidate, Election, Voter

admin.site.register(Voter)
admin.site.register(Election)
admin.site.register(Candidate)
