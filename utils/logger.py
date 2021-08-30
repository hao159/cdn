import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import logging
import graypy
from gelfHandler import GelfHandler

MY_LOGGER = logging.getLogger('SMS_LOG')
MY_LOGGER.setLevel(logging.ERROR)
GRAY_LOG_HOST = os.environ.get('APP_GRAYLOG_HOST')
GRAY_LOG_PORT = os.environ.get('APP_GRAYLOG_UDP_PORT')
handler = graypy.GELFUDPHandler(GRAY_LOG_HOST, int(GRAY_LOG_PORT),  debugging_fields=False)
MY_LOGGER.addHandler(handler)

log_level = {
    'CRITICAL' : logging.CRITICAL,
    'ERROR' : logging.ERROR,
    'WARNING' : logging.WARNING,
    'INFO' : logging.INFO,
    'DEBUG' : logging.DEBUG,
    'NOTSET': logging.NOTSET
}

def log_gray(full_msg, lever = 'INFO', user='default'):
    class LogFilter(logging.Filter):
        def __init__(self):
            self.username = user
            self.full_message  = full_msg
        def filter(self, record):
            record.username = self.username
            record.full_message  = self.full_message
            return True
    MY_LOGGER.addFilter(LogFilter())
    MY_LOGGER.log(log_level[lever], lever + '_' + os.environ.get("APP_NAME"))

