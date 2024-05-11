# study/admin.py

from django.contrib import admin
from .models import Category, StudyLog

admin.site.register(Category)
admin.site.register(StudyLog)