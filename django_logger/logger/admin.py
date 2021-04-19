from django.conf.urls import url
from django.contrib import admin
from django.http.response import HttpResponse, HttpResponseRedirect
from django.urls import path
from django.urls.base import reverse
from .models import LoggerFile
from djongo.admin import ModelAdmin


class BaseListFilter(admin.SimpleListFilter):
    def lookups(self, request, model_admin):
        fields = set(model_admin.model.objects.values_list(self.parameter_name, flat=True))
        return tuple(zip(fields, fields))

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(**{self.parameter_name: self.value()})
        return queryset


class MethodListFilter(BaseListFilter):
    """
        HTTP Method filter for django-admin
    """
    title = 'method name'
    parameter_name = 'method'


@admin.register(LoggerFile)
class LoggerFileAdmin(ModelAdmin):
    change_list_template = 'logger/admin/admin.html'
    date_hierarchy = 'date'
    list_display = ('date', 'ip_address', 'additional_ip_info', 'method', 'uri')
    list_filter = (
        MethodListFilter, 
    )
    search_fields = ('ip_address', 'method', 'uri', 'referer_from')

    def get_readonly_fields(self, request, obj):
        return [field.name for field in obj._meta.fields]

    def has_add_permission(self, request) -> bool:
        return False

    def get_urls(self):
        urls = super().get_urls()
        urls_custom = [
            path('clear/', self.clear_logs, name='clear_logs'),
        ]
        return urls_custom + urls

    def clear_logs(self, request):  
        """ View for clear logs. Will DELETE ALL logs """
        if request.method == 'POST':
            LoggerFile.objects.all().delete()
        return HttpResponseRedirect(reverse('admin:{}_{}_changelist'.format(LoggerFile._meta.app_label, str(LoggerFile._meta.model_name))))