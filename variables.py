import bpy
from . import preferences as P
from enum import Enum

LM_MASTER_COLLECTION = "Master Collection"
LM_ASSET_COLLECTION = "Assets_Collection"
LM_COMPATIBLE_MESH_FORMAT = {".fbx":(bpy.ops.import_scene.fbx, {'filter_glob':'*.fbx;', 'axis_forward':'-Z', 'axis_up':'Y'}),
								".obj":(bpy.ops.import_scene.obj, {'filter_glob':'*.obj;*.mtl', 'axis_forward':'-Z', 'axis_up':'Y'})}
LM_COMPATIBLE_TEXTURE_FORMAT = {".png":(),
									".tga":()}


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

class GetParam(object):
	def  __init__(self, scn):
		param = {}
		for p in dir(scn):
			if 'lm_' == p[0:3]:
				param.update({p:getattr(scn, p)})

		self.param = param

class Status(Enum):
	NOT_STARTED = "Not Started"
	WIP = "WIP"
	DONE = "Done"