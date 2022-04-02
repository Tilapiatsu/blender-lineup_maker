import bpy, os
from . import preferences as P
from enum import Enum

LM_DEPENDENCIES = ['Pillow', 'fpdf']
LM_CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
LM_PACKAGE = os.path.basename(LM_CURRENT_DIR)
LM_DEPENDENCIES_FOLDER_NAME = 'LineupMakerDependencies'
LM_DEPENDENCIES_PATH = os.path.join(LM_CURRENT_DIR, LM_DEPENDENCIES_FOLDER_NAME)
LM_ASSET_COLLECTION = "Assets_Collection"
LM_PREVIEW_COLLECTION = "Preview_Collection"
LM_COMPATIBLE_MESH_FORMAT = {".fbx":(bpy.ops.import_scene.fbx, {'filter_glob':'*.fbx;', 'axis_forward':'-Z', 'axis_up':'Y'}, "bpy.ops.import_scene.fbx"),
								".obj":(bpy.ops.import_scene.obj, {'filter_glob':'*.obj;*.mtl', 'axis_forward':'-Z', 'axis_up':'Y'}, "bpy.ops.import_scene.obj")}
LM_COMPATIBLE_EXPORT_FORMAT = ['MESH']
LM_COMPATIBLE_TEXTURE_FORMAT = {".png":(),
								".tga":(),
								".psd":()}


LM_OUTPUT_EXTENSION = {'BMP':'.bmp',
						'IRIS':'.iris',
						'PNG':'.png',
						'JPEG':'.jpg',
						'JPEG2000':'.jpg',
						'TARGA':'.tga',
						'TARGA_RAW':'.tga',
						'CINEON':'.cin',
						'DPX':'.dpx',
						'OPEN_EXR_MULTILAYER':'.exr',
						'OPEN_EXR':'.exr',
						'HDR':'.exr',
						'TIFF':'.tif'}

LM_FINAL_COMPOSITE_FOLDER_NAME = '00_Final_Composite'
LM_FINAL_COMPOSITE_SUFFIX = '_final_composite'

LM_DEFAULT_SECTION = 'UNCATEGORIZED'

LM_CATALOG_PATH = os.path.join(LM_CURRENT_DIR, 'StartupCatalog', "StartupCatalog.blend")

class GetParam(object):
	def  __init__(self, scn):
		param = {}
		for p in dir(scn):
			if 'lm_' == p[0:3]:
				param.update({p:getattr(scn, p)})

		self.param = param

class Status(Enum):
	NOT_SET = -1
	NOT_STARTED = 1
	NOT_NEEDED = 2
	WIP = 3
	DONE = 4

STATUS_DICT = {str(Status.NOT_SET.value):('NOT_SET', 'Not Set', '', 'NOT_STARNOT_SETTED', Status.NOT_SET.value),
				str(Status.NOT_STARTED.value):('NOT_STARTED', 'Not Started', '', 'NOT_STARTED', Status.NOT_STARTED.value),
				str(Status.NOT_NEEDED.value):('NOT_NEEDED', 'Not Needed', '', 'NOT_NEEDED', Status.NOT_NEEDED.value),
				str(Status.WIP.value):('WIP', 'WIP', '', 'WIP', Status.WIP.value),
				str(Status.DONE.value):('DONE', 'Done', '', 'DONE', Status.DONE.value)
				}

STATUS = [
        STATUS_DICT[str(Status.NOT_STARTED.value)],
		STATUS_DICT[str(Status.NOT_NEEDED.value)],
        STATUS_DICT[str(Status.WIP.value)],
        STATUS_DICT[str(Status.DONE.value)]
    	]

LM_DEFAULT_CHANNELS = {	'Base Color': {'linear':False, 'normal_map':False, 'inverted':False},
						'Nomal': {'linear':True, 'normal_map':True, 'inverted':True},
						'Roughness': {'linear':True, 'normal_map':False, 'inverted':False},
						'Metallic': {'linear':True, 'normal_map':False, 'inverted':False},
						'Opacity': {'linear':False, 'normal_map':False, 'inverted':False}}