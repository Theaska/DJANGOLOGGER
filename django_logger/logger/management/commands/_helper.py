import asyncio
import os
import re
from typing import Generator, Iterator
import aiofiles
import aiohttp
from django.db import models
import datetime
from django.utils import timezone
from django.conf import settings
from logger.parser import LoggerTextParser
import logging
from asgiref.sync import sync_to_async


logger = logging.getLogger(__name__)
        

def generate_logfile_name() -> str:
    """
        Generate name for logfile
    """
    return f'log_file_{timezone.now().strftime("%d_%m_%y_%H_%M")}.log'


DEFAULT_LOG_PATH = settings.BASE_DIR / 'logs'
NEW_LINE_SYMBOLS = ('\n', '\r', '\r\n', '\n\r')
LOGFILE_NAME_GENERATOR = generate_logfile_name
DEFAULT_LOG_REGEX = re.compile('(\d+\.\d+\.\d+\.\d+)'  # ip address (group 1)
                    '(?:\.(.*)){0,1} ' # additional info for strange addresses (ex. 145.219.89.34.bc.googleusercontent.com) (group 2)
                    '(.*) ' # group 3
                    '(.*) ' # group 4
                    '\[(\d{1,2}/\w+/\d{4}:\d{2}:\d{2}:\d{2} \+\d+)\] '  # date in format 19/Dec/2020:13:57:26 +01000 (group 5) 
                    '\"(\w+) ' # method (GET, POST, PUT, ...) (group 6)
                    '(.+) ' # uri (group 7)
                    '(HTTP/\d.\d)\" ' # http version (group 8)
                    '(\d{3}) ' # status (group 9)
                    '(\d+|-) ' # body length (group 10)
                    '\"(.*)\" ' # referer from (group 11)
                    '\"(.*)\" ' # user agent (group 12)
                    '\"(.*)\"') # hz (group 13)



class ImportLogs(object):
    async def import_from_file(self, filename: str, **import_kwargs):
        log_iterator = self._read_line_from_file(filename)
        await self.__import(log_iterator=log_iterator, **import_kwargs)

    async def import_from_url(self, url: str, **import_kwargs):
        log_iterator = self._read_line_from_url(url)
        await self.__import(log_iterator=log_iterator, **import_kwargs)

    async def __import(self, log_iterator: Iterator[bytearray], save=False, output_model: models.Model = None, chunk_size: int = 5, filepath: str=None):
        chunk = []
        parser = LoggerTextParser(regex=DEFAULT_LOG_REGEX)
        output_file = await self.get_file(filepath) if save else None

        async for line in log_iterator:

            if not line or line in NEW_LINE_SYMBOLS:
                continue

            parsed_line = parser.parse(line=line)
            if not parsed_line:
                continue

            if save:
                output_file.write(parsed_line)
            
            log_dict = pack_apache_logline(parsed_line)

            # create chunk
            if output_model and log_dict:
                if len(chunk) >= chunk_size:
                    await self._write_to_db(output_model, chunk=chunk)
                    chunk = []
                model_obj = self._create_output_object(output_model, **log_dict)
                chunk.append(model_obj)

        # check if chunk is not empty
        if output_model and chunk:
            await self._write_to_db(output_model, chunk=chunk)

        if output_file:
            output_file.close()

    def _create_output_object(self, output_model: models.Model, **info):
        """ Just create class model object """
        try:
            return output_model(**info)
        except (ValueError, AttributeError) as exc:
            logger.warning('Can not create models objects. {exc}'.format(exc))

    async def _write_to_db(self, output_model: models.Model, chunk: tuple):
        """ Create DB entities with builk_crate asynchronously """
        try:
            await sync_to_async(output_model.objects.bulk_create)(chunk)
        except (ValueError, AttributeError) as exc:
            logger.warning('Can not create models objects. {exc}'.format(exc))
    
    async def get_file(self, filepath: str = None):
        """ Get or create file from filepath or check if logs dir exists.
        If doesn't, then create dir and return aiofiles.files
        """
        if not filepath:
            if not os.path.exists(DEFAULT_LOG_PATH):
                os.mkdir(DEFAULT_LOG_PATH)
            filepath = os.path.join(DEFAULT_LOG_PATH, LOGFILE_NAME_GENERATOR())
        return await aiofiles.open(filepath, 'a+')

    async def _read_line_from_url(self, url)-> Iterator[bytearray]:
        """  Yield line bytes from content """
        async with aiohttp.request('get', url) as response:
            response.raise_for_status()

            if not response.headers.get('Content-Type').startswith('text/plain;'):
                raise ValueError('Wait content-type "text/plain", but got {}'.format(response.headers.get('Content-Type')))
            
            async for line in response.content:
                yield line.decode()
    
    async def _read_line_from_file(self, filename: str) -> Iterator[str]:
        async with aiofiles.open(filename) as file:
            async for line in file:
                yield line
                


def pack_apache_logline(parsed_line_tuple: tuple) -> dict:
    """
        Pack received tuple when parsing apache log file into dict.
    """
    try:
        return {
            'ip_address': parsed_line_tuple[0],
            'additional_ip_info': parsed_line_tuple[1],
            'date': datetime.datetime.strptime(parsed_line_tuple[4], '%d/%b/%Y:%H:%M:%S %z'),
            'method': parsed_line_tuple[5],
            'uri': parsed_line_tuple[6],
            'http_version': parsed_line_tuple[7],
            'status': parsed_line_tuple[8],
            'body_length': parsed_line_tuple[9] if parsed_line_tuple[9] != '-' else 0,
            'referer_from': parsed_line_tuple[10],
            'user_agent': parsed_line_tuple[11]
        }
    except Exception as exc:
        logger.warning(str(exc), parsed_line_tuple)
        return {}
