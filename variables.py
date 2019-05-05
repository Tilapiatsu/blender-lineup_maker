import bpy

LM_MASTER_COLLECTION = "Master Collection"
LM_ASSET_COLLECTION = "Assets_Collection"
LM_COMPATIBLE_MESH_FORMAT = {".fbx":(bpy.ops.import_scene.fbx, {'filter_glob':'*.fbx;', 'axis_forward':'-Z', 'axis_up':'Y'}),
                                ".obj":(bpy.ops.import_scene.obj, {'filter_glob':'*.obj;*.mtl', 'axis_forward':'-Z', 'axis_up':'Y'})}
LM_COMPATIBLE_TEXTURE_FORMAT = {".png":(),
                                    ".tga":()}

LM_NAMING_CONVENTION_KEYWORDS_COMMON = ['project',
                                        'team',
                                        'category',
                                        'incr',
                                        'gender']
LM_NAMING_CONVENTION_KEYWORDS_MESH = ['plugname']
LM_NAMING_CONVENTION_KEYWORDS_TEXTURE = ['tincr',
                                        'matid']

LM_NAMING_CONVENTION_KEYWORDS = LM_NAMING_CONVENTION_KEYWORDS_COMMON + LM_NAMING_CONVENTION_KEYWORDS_MESH + LM_NAMING_CONVENTION_KEYWORDS_TEXTURE + ['assetname']

LM_SEPARATORS = '_.-'