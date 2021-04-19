from django.core.management import BaseCommand
import aiofiles
import asyncio
from ._helper import LoggerTextParser, pack_apache_logline
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
        text = asyncio.run(self.read_file(filepath))

        parser = LoggerTextParser()
        self.stdout.write('Start parsing log file .....')
        lines = tuple(pack_apache_logline(line) for line in parser.parse(text))
        
        pool = ThreadPool(4)
        pool.map(self.create_model_object, lines)
        pool.close()
        pool.join()

    def create_model_object(self, line_dict):
        try:
            LoggerFile.objects.create(**line_dict)
        except Exception as exc:
            self.stderr.write(str(exc) + str(line_dict))


        