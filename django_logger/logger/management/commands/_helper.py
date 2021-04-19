import os
import re
import aiofiles
import aiohttp
import datetime
from django.utils import timezone
from django.conf import settings
import logging


logger = logging.getLogger(__name__)


DEFAULT_LOG_PATH = settings.BASE_DIR / 'logs'
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


class ImportLoggerFile(object):
    """
        Async importer loggers from url. Example of running:

        import asyncio

        async def run():
            importer_loggs = ImportLoggerFile('http://www.almhuette-raith.at/apache-log/access.log')
            importer_loggs_error = ImportLoggerFile('http://www.almhuette-raith.at/apache-log/error.log')
            await asyncio.gather(
                importer_loggs.import_from_url(),
                importer_loggs_error.import_from_url(),
            )

        def main():
            asyncio.run(self.run())

        main()
    """

    def __init__(self, url: str):
        self.url = url
        self._text = None

    async def import_logs(self):
        """
            Import logger file text with aiohttp.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                if not response.status == 200:
                    raise ValueError('Can not get log text. Status code of response {}'.format(response.status))

                content_type = response.headers.get('Content-Type')
                if not content_type.startswith('text/plain;'):
                    raise ValueError('Wait content-type "text/plain", but got {}'.format(content_type))
                
                return await response.text()
                
        

def generate_logfile_name() -> str:
    """
        Generate name for logfile
    """
    return f'log_file_{timezone.now().strftime("%d_%m_%y_%H_%M")}.log'


LOGFILE_NAME_GENERATOR = generate_logfile_name


class LoggerTextParser:
    """
        Class for parsing log text or saving it as a file.
    """
    regex = DEFAULT_LOG_REGEX

    def set_regex(self, regex: str = None):
        """
            Set regular expression for parsing logger file
        """
        if regex is None:
            self.regex = DEFAULT_LOG_REGEX
        else:
            self.regex = re.compile(regex)

    def parse(self, text: str):
        for line in text.strip().splitlines():
            match = self.regex.match(line)
            if not match:
                logger.warning('Line does not match regex: ', line)
                inp = input('Print "c" to continue: ')
                if inp.lower() == 'c':
                    continue
                else:
                    return
            yield self.regex.findall(line)[0]

    async def save(self, text: str, filename: str = LOGFILE_NAME_GENERATOR(), path: str = DEFAULT_LOG_PATH):
        """
            Save logger file asynchronously.
        """
        path = os.path.join(path, filename)
        async with aiofiles.open(path, 'a+') as file:
            await file.write(text)



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
        logger.exception(str(exc), parsed_line_tuple)
