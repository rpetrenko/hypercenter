from django.contrib import admin
from .models import HyperManager


class HyperManagerAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'url', 'online')


admin.site.register(HyperManager, HyperManagerAdmin)
