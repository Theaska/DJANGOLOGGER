import asyncio
from os import wait
import re
from typing import Any
from django.core.management import BaseCommand
from ._helper import ImportLogs
from logger.models import LoggerFile


class Command(BaseCommand):
    help = 'Download logger file from url and parse it into django DB'

    def add_arguments(self, parser):
        parser.add_argument('url', type=str)
        parser.add_argument(
            '--save',
            action='store_true',
            help='Save logger file',
        )

    def handle(self, *args, **options):
        url = options.get('url')
        self.stdout.write('Start downloading log file .....')
        importer = ImportLogs()
        asyncio.run(importer.import_from_url(url, output_model=LoggerFile, save=options.get('save', False)))