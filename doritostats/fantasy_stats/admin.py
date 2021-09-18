from django.contrib import admin

from .models import Question, League

# Register your models here.
admin.site.register(Question)
admin.site.register(League)