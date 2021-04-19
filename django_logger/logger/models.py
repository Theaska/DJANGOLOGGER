from re import T
from django.db import models
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _


class LoggerFile(models.Model):
    ip_address = models.GenericIPAddressField(_('ip address'))
    additional_ip_info = models.CharField(
        _('additional ip address info'), 
        max_length=255, 
        blank=True, 
        null=True
    )
    date = models.DateTimeField()
    method = models.CharField(_('http method'), max_length=10)
    uri = models.TextField(_('uri'))
    http_version = models.CharField(_('http version'), max_length=10)
    status = models.PositiveIntegerField(_('status code'))
    body_length = models.PositiveIntegerField(_('body length'), default=0)
    referer_from = models.TextField(_('referer'), blank=True, null=True)
    user_agent = models.TextField(_('user-agent'), blank=True, null=True)


    def __str__(self) -> str:
        return f'[{self.ip_address}]: {self.method} "{self.uri}"'

    class Meta:
        ordering = ('-date', )
        verbose_name = _('Logger File')
        verbose_name_plural = _('Logger Files')