import bpy, os, logging, tempfile
from os import path

def get_log_file():
	try:
		filepath = bpy.data.filepath
	except AttributeError:
		filepath = ''
	if path.exists(filepath):
		log_file = path.join(path.dirname(filepath), '{}.log'.format(path.splitext(path.basename(filepath))[0]))
	else:
		tempf = tempfile.TemporaryFile().name
		log_file = '{}.log'.format(tempf) 

	return log_file


class Logger(object):
	def __init__(self, context='ROOT'):
		self.context = context

		self.log_file = get_log_file()
		self.timeformat = '%m/%d/%Y %I:%M:%S %p'
		self.set_basic_config()

		self.success = []
		self.failure = []

		self._pretty = '---------------------'

	def info(self, message):
		self.set_basic_config()
		logging.info(message)
	
	def debug(self, message):
		self.set_basic_config()
		logging.debug(message)

	def warning(self, message):
		self.set_basic_config()
		logging.warning(message)

	def error(self, message):
		self.set_basic_config()
		logging.error(message)

	def set_basic_config(self):
		self.format = 'LINEUP MAKER : %(asctime)s - %(levelname)s : {} :    %(message)s'.format(self.context)
		logging.basicConfig(filename=self.log_file, level=logging.DEBUG, datefmt=self.timeformat, filemode='w', format=self.format)

	def store_success(self, success):
		self.success.append(success)
	
	def store_failure(self, failure):
		self.failure.append(failure)

	def pretty(self, str):

		p = self._pretty

		for c in str:
			p += '-'
		
		return p


class LoggerProgress(Logger):
	def __init__(self, context='ROOT'):
		super(LoggerProgress, self).__init__(context)

	def init_progress_asset(self, asset_name):

		pretty = self.pretty(asset_name)

		self.info('----------------------------------------------------------' + pretty)
		self.info('----------------------------- Processing Asset "{}" -----------------------------'.format(asset_name))
		self.info('----------------------------------------------------------' + pretty)

	def complete_progress_asset(self):
		self.info('')
		self.info('----------------------------------------------------------')
		self.info('----------------------------------------------------------')
		self.info('----------------------------------------------------------')
		self.info('')

		self.info('Import/Update Completed with {} success and {} failure'.format(len(self.success), len(self.failure)))
		for s in self.success:
			self.info('{}'.format(s))
		for f in self.failure:
			self.info('{}'.format(f))