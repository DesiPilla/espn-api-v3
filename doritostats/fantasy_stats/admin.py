from django.contrib import admin

from .models import Question, LeagueInfo

# Register your models here.
admin.site.register(Question)
admin.site.register(LeagueInfo)