import asyncio
from os import wait
import re
from typing import Any
from django.core.management import BaseCommand
from ._helper import ImportLoggerFile, LoggerTextParser, pack_apache_logline
from logger.models import LoggerFile
import multiprocessing


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

        importer_loggs = ImportLoggerFile(url)
        self.stdout.write('Start downloading log file .....')
        result = asyncio.run(importer_loggs.import_logs())

        parser = LoggerTextParser()
        if options.get('save'):
            self.stdout.write('Start saving log file .....')
            asyncio.run(parser.save(text=result))

        self.stdout.write('Start parsing log file .....')

        lines = tuple(pack_apache_logline(line) for line in parser.parse(result))

        from multiprocessing.dummy import Pool as ThreadPool
        pool = ThreadPool(4)
        pool.map(self.create_model_object, lines)
        pool.close()
        pool.join()

    def create_model_object(self, line_dict):
        try:
            LoggerFile.objects.create(**line_dict)
        except Exception as exc:
            self.stderr.write(str(exc) + str(line_dict))