import bpy, os, logging, tempfile
from os import path

def get_log_file():
    filepath = bpy.data.filepath
    if path.exists(filepath):
        log_file = path.join(path.dirname(filepath), '{}.log'.format(path.splitext(path.basename(filepath))[0]))
    else:
        log_file = tempfile.TemporaryFile()

    return log_file


class Logger(object):
    def __init__(self, context='ROOT'):
        self.context = context

        self.log_file = get_log_file()
        self.timeformat = '%m/%d/%Y %I:%M:%S %p'
        self.set_basic_config()

        self.success = []
        self.failure = []

    def info(self, message):
        self.set_basic_config()
        logging.info(message)
    
    def debug(self, message):
        self.set_basic_config()
        logging.debug(message)

    def warning(self, message):
        self.set_basic_config()
        logging.warning(message)

    def set_basic_config(self):
        self.format = 'LINEUP MAKER : %(asctime)s - %(levelname)s : {} : %(message)s'.format(self.context)
        logging.basicConfig(filename=self.log_file, level=logging.DEBUG, datefmt=self.timeformat)

    def store_success(self, success):
        self.success.append(success)
    
    def store_failure(self, failure):
        self.failure.append(failure)