from numpy import isin
import bpy
import os, subprocess, json
from . import logger as L
from mathutils import Color
from math import radians, degrees
from bpy_extras.io_utils import ImportHelper
from . import properties as P

INCLUDE = ['lm_asset_path',
			'lm_render_path',
			'lm_separator',
			'lm_asset_naming_convention',
			'lm_mesh_naming_convention',
			'lm_texture_naming_convention',
			'lm_chapter_naming_convention',
			'lm_default_camera',
			'lm_override_material_color',
			'lm_default_material_color',
			'lm_override_material_roughness',
			'lm_default_material_roughness',
			'lm_override_material_specular',
			'lm_default_material_specular',
			'lm_texture_channels',
			'lm_channels',
			'lm_shaders',
			'lm_keywords',
			'lm_keyword_values',
			# 'lm_cameras',
			'lm_content_background_color',
			'lm_text_background_color',
			'lm_font_color',
			'lm_blend_catalog_path',
			'lm_precomposite_frames',
			'lm_override_frames',
			'lm_force_render',
			'lm_pdf_export_last_rendered'
			]
class LM_OP_SavePreset(bpy.types.Operator, ImportHelper):
	bl_idname = "scene.lm_save_preset"
	bl_label = "Save Preset"
	bl_options = {'REGISTER', 'UNDO'}
	filter_glob: bpy.props.StringProperty(
	default='*.json',
	options={'HIDDEN'}
	)
	
	@property
	def prop(self):
		return [getattr(P, p) for p in dir(P)]

	def execute(self, context):
		if os.path.splitext(self.filepath)[1].lower() != '.json':
			print('Filepath is not a .json')
			return {'CANCELLED'}

		print('Saving {}'.format(self.filepath))

		self.json_data = self.lm_properties(parent_dict=self.get_scene_dict(context))
		print(self.json_data)
		self.write_json(context)
		
		return {'FINISHED'}

	def get_scene_dict(self, context):
		scene_dict={}
		for p in dir(context.scene):
			if not p.startswith('lm_') or p not in INCLUDE:
				continue

			scene_dict[p] = getattr(context.scene, p)

		return scene_dict
		

	def get_property_group_dict(self, parent_dict):
		property_dict = {}

		for p in dir(parent_dict):
			if p.startswith('__') or p in ['bl_rna', 'rna_type', '']:
				continue
			
			property_dict[p] = self.parse_property(param=getattr(parent_dict, p), property_name=p, property_dict=property_dict, parent_dict=parent_dict)

		return property_dict

	def parse_dict(self, parent_dict, property_dict):
		i=0
		for k,v in parent_dict.items():
			if k == "":
				k = i
			property_dict[k] = self.parse_property(param=v, property_name=k, property_dict=property_dict, parent_dict=parent_dict)
			i += 1
		
		return property_dict

	def parse_property(self, param, property_name, property_dict, parent_dict):
		if isinstance(param, (bpy.types.bpy_prop_collection, bpy.types.PropertyGroup, bpy.types.CollectionProperty, bpy.types.Struct)):
			sub_dict = {}
			sub_dict = self.lm_properties(parent_dict=param)
			return sub_dict
		elif type(param) in self.prop:
			return self.get_property_group_dict(param)
		elif isinstance(param, (bpy.types.StringProperty, bpy.types.FloatProperty, bpy.types.IntProperty, bpy.types.BoolProperty)):
			return param.default
		elif isinstance(param, bpy.types.PointerProperty):
			return {'datatype' : 'bpy.types.PointerProperty','value' : param.name}
		elif isinstance(param, bpy.types.Image):
			return {'datatype' : 'bpy.types.Image','value' : param.name}
		elif isinstance(param, Color):
			return {'datatype' : 'Color','value' : [param.r, param.g, param.b]}
		elif isinstance(param, bpy.types.Camera):
			cam = {'datatype': 'bpy.types.Camera', 'value': param.name}
			if param.name in bpy.data.objects:
				scene_cam = bpy.data.objects[param.name]
				cam['type'] = scene_cam.data.type
				cam['lens'] = scene_cam.data.lens
				cam['lens_unit'] = scene_cam.data.lens_unit
				cam['shift_x'] = scene_cam.data.shift_x
				cam['shift_y'] = scene_cam.data.shift_y
				cam['clip_start'] = scene_cam.data.clip_start
				cam['clip_end'] = scene_cam.data.clip_end
				cam['location'] = [scene_cam.location[0], scene_cam.location[1], scene_cam.location[2]]
				cam['rotation_euler'] = [scene_cam.rotation_euler[0], scene_cam.rotation_euler[1], scene_cam.rotation_euler[2], scene_cam.rotation_euler.order]
				cam['scale'] = [scene_cam.scale[0], scene_cam.scale[1], scene_cam.scale[2]]
			return cam
		elif isinstance(param, bpy.types.Collection):
			return {'type': 'bpy.types.Collection', 'value': param.name}
		elif isinstance(param, bpy.types.Material):
			return {'type': 'bpy.types.Material', 'value': param.name}
		elif isinstance(param, bpy.types.Object):
			return {'type': 'bpy.types.Object', 'value': param.name}
		else:
			return param
		
	def lm_properties(self, parent_dict=None):
		property_dict = {}

		if parent_dict is None:	
			return property_dict

		# parent_dict is a Lineup Maker property_group --> parse the property group
		if type(parent_dict) in self.prop:
			property_dict = self.get_property_group_dict(parent_dict)
			return property_dict

		# parent_dict is property collection
		if isinstance(parent_dict, bpy.types.bpy_prop_collection) or isinstance(parent_dict, dict):
			# parse children elements
			property_dict = self.parse_dict(parent_dict, property_dict)
			return property_dict

	def merge_dicts(x, y):
		z = x.copy()   # start with keys and values of x
		z.update(y)    # modifies z with keys and values of y
		return z

	def write_json(self, context):
		if len(self.json_data):
			with open(self.filepath, 'w', encoding='utf-8') as outfile:
				json.dump(self.json_data, outfile, ensure_ascii=False, indent=4)

class LM_OP_LoadPreset(bpy.types.Operator, ImportHelper):
	bl_idname = "scene.lm_load_preset"
	bl_label = "Lineup Maker: Load Preset"
	bl_options = {'REGISTER', 'UNDO'}
	filter_glob: bpy.props.StringProperty(
	default='*.json',
	options={'HIDDEN'}
	)
	
	def execute(self, context):
		
		json_data = self.get_json_data()

		self.load_json_data(json_data, json_data, "bpy.context.scene")

		return {'FINISHED'}

	def join_scene_path(self, scene_path, subpath, is_list=False):
		if is_list:
			return scene_path + '["' + subpath + '"]'
		else:
			return scene_path + '.' + subpath

	def get_json_data(self):
		json_data = {}
		if not os.path.isfile(self.filepath):
			print('Lineup Maker : The folder path "{}" is not valid'.format(self.filepath))
			return{'CANCELLED'}
		
		print('loading preset {}'.format(self.filepath))
		with open(self.filepath, 'r', encoding='utf-8-sig') as json_file:  
			data = json.load(json_file)
			json_data = data

		return json_data

	
	def load_json_data(self, json_data={}, parent=None, scene_path=None):
		if 'datatype' in json_data.keys():
			value = scene_path.split('.')[-1]
			self.set_property_value(value, eval(json_data['datatype']), parent, scene_path)
			return
		for k,v in json_data.items():
			curr_scene_path = self.join_scene_path(scene_path, k)
			if k in INCLUDE:
				self.set_property_value(k, v, parent, curr_scene_path)
			elif k == 'datatype':
				self.set_property_value(k, v, parent, curr_scene_path)
			elif isinstance(v, dict):
				if 'datatype' in v.keys():
					self.set_property_value(k, v, parent, curr_scene_path)
				else:
					self.load_json_data(v, json_data, parent, curr_scene_path)
			else:
				self.set_property_value(k, v, parent, curr_scene_path)


	def set_property_value(self, prop_name, value, parent=None, scene_path=None):
		if isinstance(eval(scene_path), (bpy.types.bpy_prop_collection, bpy.types.PropertyGroup, bpy.types.CollectionProperty, bpy.types.Struct)):
			for sub_prop, sub_value in value.items():
				if sub_prop not in dir(eval(scene_path)):
					new_prop = eval(scene_path).add()
					new_prop.name = sub_prop
					self.set_property_value(new_prop.name, sub_value, eval(scene_path), self.join_scene_path(scene_path, new_prop.name, is_list=True))
				else:
					self.set_property_value(sub_prop, sub_value, eval(scene_path), self.join_scene_path(scene_path, sub_prop))
		elif isinstance(value, dict):
			self.load_json_data(value, parent, scene_path)
		elif value in [bpy.types.StringProperty, bpy.types.FloatProperty, bpy.types.IntProperty, bpy.types.BoolProperty]:
			exec('{} = {}'.format(scene_path, value))
		elif value == Color:
			eval(scene_path).r = parent[prop_name]['value'][0]
			eval(scene_path).g = parent[prop_name]['value'][1]
			eval(scene_path).b = parent[prop_name]['value'][2]
		elif value == bpy.types.Object:
			ob = parent[prop_name]['value']
			if ob in bpy.data.objects:
				parent[prop_name] = bpy.data.objects[ob]
		elif value == bpy.types.Camera:
			cam = parent[prop_name]['value']
			if cam in bpy.data.objects:
				if cam in bpy.data.cameras:
					exec('{} = bpy.data.cameras["{}"]'.format(scene_path, cam))
			else:
				bpy.ops.object.camera_add('INVOKE_DEFAULT')
				new_cam = bpy.context.active_object
				new_cam.name = cam
				new_cam.data.name = cam
				new_cam.data.type = parent[prop_name]['type']
				new_cam.data.lens = parent[prop_name]['lens'] 
				new_cam.data.lens_unit = parent[prop_name]['lens_unit']
				new_cam.data.shift_x = parent[prop_name]['shift_x']
				new_cam.data.shift_y = parent[prop_name]['shift_y']
				new_cam.data.clip_start = parent[prop_name]['clip_start']
				new_cam.data.clip_end = parent[prop_name]['clip_end']
				new_cam.location[0] = parent[prop_name]['location'][0]
				new_cam.location[1] = parent[prop_name]['location'][1]
				new_cam.location[2] = parent[prop_name]['location'][2]
				new_cam.rotation_euler.order = parent[prop_name]['rotation_euler'][3]
				new_cam.rotation_euler[0] = parent[prop_name]['rotation_euler'][0]
				new_cam.rotation_euler[1] = parent[prop_name]['rotation_euler'][1]
				new_cam.rotation_euler[2] = parent[prop_name]['rotation_euler'][2]
				new_cam.scale[0] = parent[prop_name]['scale'][0]
				new_cam.scale[1] = parent[prop_name]['scale'][1]
				new_cam.scale[2] = parent[prop_name]['scale'][2]
				exec('{} = bpy.data.cameras["{}"]'.format(scene_path, new_cam.name))
		else:
			if type(value) == str:
				exec("{} = {}".format(scene_path, repr(value)))
			else:
				exec('{} = {}'.format(scene_path, value))