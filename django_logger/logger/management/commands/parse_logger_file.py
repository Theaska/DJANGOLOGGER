from django.core.management import BaseCommand
import aiofiles
import asyncio
from ._helper import ImportLogs
from logger.models import LoggerFile
from multiprocessing.dummy import Pool as ThreadPool


class Command(BaseCommand):
    help = 'Parse existing logger file into DB model'

    def add_arguments(self, parser):
        parser.add_argument('filepath', type=str)
    
    async def read_file(self, filepath: str):
        async with aiofiles.open(filepath, 'r+') as file:
            return await file.read()

    def handle(self, *args, **options):
        """
            Read logs from existing file and pack it into DB Model
        """
        filepath = options['filepath']

        importer = ImportLogs()
        asyncio.run(importer.import_from_file(filepath, output_model=LoggerFile))
        