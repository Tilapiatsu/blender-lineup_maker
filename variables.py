import bpy
from . import preferences as P
from enum import Enum

LM_MASTER_COLLECTION = "Master Collection"
LM_ASSET_COLLECTION = "Assets_Collection"
LM_COMPATIBLE_MESH_FORMAT = {".fbx":(bpy.ops.import_scene.fbx, {'filter_glob':'*.fbx;', 'axis_forward':'-Z', 'axis_up':'Y'}),
								".obj":(bpy.ops.import_scene.obj, {'filter_glob':'*.obj;*.mtl', 'axis_forward':'-Z', 'axis_up':'Y'})}
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

class GetParam(object):
	def  __init__(self, scn):
		param = {}
		for p in dir(scn):
			if 'lm_' == p[0:3]:
				param.update({p:getattr(scn, p)})

		self.param = param

class Status(Enum):
	NOT_SET = -1
	NOT_STARTED = 0
	NOT_NEEDED = 1
	WIP = 2
	DONE = 3

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