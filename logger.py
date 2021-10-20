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
		# self.message_list = []

		self._pretty = '---------------------'

	def info(self, message, asset=None, print_log=True):
		self.set_basic_config()
		if asset is not None:
			warning = asset.warnings.add()
			warning.message = message
		# if print_log:
		# 	self.message_list.append(message)
		# 	print_progress(bpy.context, self.message_list, title=self.context, icon='NONE')
		logging.info(message)
	
	def debug(self, message, asset=None, print_log=True):
		self.set_basic_config()
		if asset is not None:
			warning = asset.warnings.add()
			warning.message = message
		# if print_log:
		# 	self.message_list.append(message)
		# 	print_progress(bpy.context, self.message_list, title=self.context, icon='NONE')
		logging.debug(message)

	def warning(self, message, asset=None, print_log=True):
		self.set_basic_config()
		if asset is not None:
			warning = asset.warnings.add()
			warning.message = message
		# if print_log:
		# 	self.message_list.append(message)
		# 	print_progress(bpy.context, self.message_list, title=self.context, icon='NONE')
		logging.warning(message)

	def error(self, message, asset=None, print_log=True):
		self.set_basic_config()
		if asset is not None:
			warning = asset.warnings.add()
			warning.message = message
		# if print_log:
		# 	self.message_list.append(message)
		# 	print_progress(bpy.context, self.message_list, title=self.context, icon='NONE')
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

list_length = 20

def print_progress(context, message_list, title = "Message Box", icon = 'INFO'):
	def draw(self, context):
		layout = self.layout
		col = layout.column()
		message = message_list[-list_length:]
		for m in message:
			col.label(text='{}'.format(m))

	context.window_manager.popup_menu(draw, title = title, icon = icon)

class LoggerPrintLog(bpy.types.Operator):
	bl_idname = "scene.lm_print_progress"
	bl_label = "Show print log"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Show print log"

	message : bpy.props.StringProperty(name="Message", default="")

	message_list = []
	list_length = 20


	def invoke(self, context, event):
		self.message_list.append(self.message)
		wm = context.window_manager
		return wm.popup_menu(self, width=1000)

	def execute(self, context):
		return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		message = self.message_list[-self.list_length:]
		for m in message:
			col.label(text='{}'.format(m))

