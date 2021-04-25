import re
import logging
import datetime

logger = logging.getLogger(__name__)


class LoggerTextParser:
    """
        Class for parsing logs.
    """
    def __init__(self, regex: str) -> None:
        """
            regex: str [regular expression for parsing log line]
        """
        self.regex = re.compile(regex)

    def parse(self, line: str) -> tuple:
        """ Trying to parse line """
        match = self.regex.findall(line)
        if not match:
            logger.warning('Line does not match regex: ', line)
        return match[0] if match else match
