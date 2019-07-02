import bpy
from . import variables as V
from . import helper as H
from . import preferences as P
from . import naming_convention as N
from . import material as M
from os import path
import time
import sys
import re
import json, codecs

class BpyAsset(object):
	def __init__(self, context, meshes, textures, jsons):
		self.context = context
		self.scn = context.scene
		self.param = V.GetParam(self.scn).param
		self.asset_name = self.get_asset_name(meshes)
		self.asset_root = self.get_asset_root(meshes)
		self.meshes = meshes
		self.textures = textures
		self.texture_set = {}
		self.jsons = jsons
		
		self._asset_naming_convention = None
		self._mesh_naming_convention = None
		self._texture_naming_convention = None
		self._json_data = None

		self.asset = None
		self.scn_asset = None
		
	# Decorators
	def check_asset_exist(func):
		def func_wrapper(self, *args, **kwargs):
			if self.asset_name in bpy.data.collections:
				return func(self, *args, **kwargs)
			else:
				print('Lineup Maker : Asset doesn\'t exist in current scene')
				return None
		return func_wrapper

	def check_length(func):
		def func_wrapper(self, *args, **kwargs):
			if not len(self.meshes):
				print('Lineup Maker : No file found in the asset folder')
				return None
			else:
				return func(self, *args, **kwargs)
		return func_wrapper

	# Methods
	def import_asset(self):
		self.import_mesh()
		self.import_texture()
	
	def update_asset(self):
		updated = self.update_mesh()
		self.update_texture()

		return updated

	@check_length
	def import_mesh(self, update=False):
		name,ext = path.splitext(path.basename(self.meshes[0]))

		curr_asset_collection, _ = H.create_asset_collection(self.context, self.asset_name)

		H.set_active_collection(self.context, self.asset_name)

		# register the mesh in scene variable
		self.scn_asset = self.context.scene.lm_asset_list.add()
		self.scn_asset.name = self.asset_name
		self.scn_asset.collection = curr_asset_collection
		self.scn_asset.asset_path = path.dirname(self.meshes[0])

		if self.json_data is not None:
			if name in self.json_data.keys():
				if 'isWip' in self.json_data[name].keys():
					self.scn_asset.wip = self.json_data[name]['isWip']
				if 'triangles' in self.json_data[name].keys():
					self.scn_asset.triangles = self.json_data[name]['triangles']
				if 'vertices' in self.json_data[name].keys():
					self.scn_asset.vertices = self.json_data[name]['vertices']
				if 'hasUV2' in self.json_data[name].keys():
					self.scn_asset.has_uv2 = self.json_data[name]['hasUV2']

				if 'HDStatus' in self.json_data[name].keys():
					try:
						self.scn_asset.hd_status = int(self.json_data[name]['HDStatus'])
					except ValueError as v:
						self.scn_asset.hd_status = V.Status.NOT_SET.value
				else:
					self.scn_asset.hd_status = V.Status.NOT_SET.value

				if 'LDStatus' in self.json_data[name].keys():
					try:
						self.scn_asset.ld_status = int(self.json_data[name]['LDStatus'])
					except ValueError as v:
						self.scn_asset.ld_status = V.Status.NOT_SET.value
				else:
					self.scn_asset.ld = V.Status.NOT_SET.value

				if 'BakingStatus' in self.json_data[name].keys():
					try:
						self.scn_asset.baking_status = int(self.json_data[name]['BakingStatus'])
					except ValueError as v:
						self.scn_asset.baking_status = V.Status.NOT_SET.value
				else:
					self.scn_asset.baking_status = V.Status.NOT_SET.value

		global_import_date = 0.0

		for i,f in enumerate(self.meshes):
			file = path.basename(f)
			name,ext = path.splitext(path.basename(f))

			# Import asset
			if ext.lower() in V.LM_COMPATIBLE_MESH_FORMAT.keys():
				if update:
					print('Lineup Maker : Updating file "{}" : {}'.format(file, time.ctime(path.getmtime(f))))
				else:
					print('Lineup Maker : Importing mesh "{}"'.format(name))
				compatible_format = V.LM_COMPATIBLE_MESH_FORMAT[ext.lower()]
				kwargs = {}
				kwargs.update({'filepath':f})
				kwargs.update(compatible_format[1])
				
				# run Import Command
				compatible_format[0](**kwargs)
			else:
				print('Lineup Maker : Skipping file "{}"\n     Incompatible format'.format(f))
				continue

			curr_mesh_list = self.scn_asset.mesh_list.add()
			curr_mesh_list.name = name
			curr_mesh_list.file_path = f
			curr_mesh_list.import_date = path.getmtime(f)
			curr_mesh_list.file_size = path.getsize(f)

			global_import_date += path.getctime(f)
			

			# Updating Materials
			for o in curr_asset_collection.objects:
				curr_mesh_object_list = curr_mesh_list.mesh_object_list.add()
				curr_mesh_object_list.mesh_name = o.name.lower()
				curr_mesh_object_list.mesh = o

				for m in o.material_slots:
					# mat_name = self.scn_asset.name + '_' + m.material.name
					# m.material.name = mat_name
					
					if m.material.name not in self.scn_asset.material_list:
						material_list = self.scn_asset.material_list.add()
						material_list.name = m.material.name
						material_list.material = m.material

						material_list = curr_mesh_list.material_list.add()
						material_list.name = m.material.name
						material_list.material = m.material
						

					curr_mesh_material_list = curr_mesh_object_list.material_list.add()
					curr_mesh_material_list.name = m.material.name
					curr_mesh_material_list.material = m.material
					
					# print(m.material.name)

		if len(self.meshes):
			self.scn_asset.import_date = global_import_date / len(self.meshes)
		else:
			self.scn_asset.import_date = 0.0
		self.asset = self.get_asset()
		# self.param['lm_asset_list'][self.asset_name] = self.scn_asset
	
	@check_length
	def update_mesh(self):
		# _, created = H.create_asset_collection(self.context, self.asset_name)
		H.set_active_collection(self.context, self.asset_name)

		curr_asset = self.param['lm_asset_list'][self.asset_name]

		need_update = False
		for f in self.meshes:
			file_name = path.splitext(path.basename(f))[0]
			file_time = path.getmtime(f)
			file_size = path.getsize(f)
			try:
				mesh_time = curr_asset.mesh_list[file_name].import_date
				mesh_size = curr_asset.mesh_list[file_name].file_size
			except KeyError:
				# The mesh was not there so we need to update
				need_update = True
				break
			if mesh_time + 20 < file_time and mesh_size != file_size:
				need_update = True
				break

		if need_update:
			print('Lineup Maker : Updating asset "{}"'.format(self.asset_name))

			self.remove_asset()
			self.import_mesh(update=True)
			# Dirty fix to avoid bad mesh naming when updating asset
			self.rename_objects()
			updated = True
		else:
			self.scn_asset = self.context.scene.lm_asset_list[self.asset_name]
			self.asset = self.get_asset()
			print('Lineup Maker : Asset "{}" is already up to date'.format(self.asset_name))
			updated = False
		

	def import_texture(self):
		# print(P.get_prefs().textureSet_albedo_keyword)
		# print(P.get_prefs().textureSet_normal_keyword)
		# print(P.get_prefs().textureSet_roughness_keyword)
		# print(P.get_prefs().textureSet_metalic_keyword)
		pass
	
	def update_texture(self):
		pass
		
	def feed_material(self, asset, material, texture_set=None):
		M.create_bsdf_material(self.context, asset, material, texture_set)

	def create_exposure_node(self, world):
		# create a group
		exposure_group = bpy.data.node_groups.new('Exposure', 'ShaderNodeTree')
		
		position = (0, 0)
		incr = 200
		# create group inputs
		group_inputs = exposure_group.nodes.new('NodeGroupInput')
		group_inputs.location = position
		exposure_group.inputs.new('NodeSocketColor', 'Color')
		exposure_group.inputs.new('NodeSocketFloat', 'Exposure')
		exposure_group.inputs[1].default_value = 1
		exposure_group.inputs[1].min_value = 0

		position = (position[0] + incr, position[1])

		# create three math nodes in a group
		node_pow = exposure_group.nodes.new('ShaderNodeMath')
		node_pow.operation = 'POWER'
		node_pow.inputs[1].default_value = 2
		node_pow.location = position

		position = (position[0] + incr, position[1])

		node_separate = exposure_group.nodes.new('ShaderNodeSeparateRGB')
		node_separate.location = position

		position = (position[0] + incr, position[1])

		node_x = exposure_group.nodes.new('ShaderNodeMath')
		node_x.operation = 'MULTIPLY'
		node_x.label = 'X'
		node_x.location = position

		position = (position[0], position[1] + incr)

		node_y = exposure_group.nodes.new('ShaderNodeMath')
		node_y.operation = 'MULTIPLY'
		node_y.label = 'Y'
		node_y.location = position

		position = (position[0], position[1] + incr)

		node_z = exposure_group.nodes.new('ShaderNodeMath')
		node_z.operation = 'MULTIPLY'
		node_z.label = 'Z'
		node_z.location = position

		position = (position[0] + incr, position[1] - incr)

		node_combine = exposure_group.nodes.new('ShaderNodeCombineRGB')
		node_combine.location = position

		position = (position[0] + incr, position[1])

		# create group outputs
		group_outputs = exposure_group.nodes.new('NodeGroupOutput')
		group_outputs.location = position

		exposure_group.outputs.new('NodeSocketColor', 'Output')

		# link nodes together
		exposure_group.links.new(node_x.inputs[1], node_pow.outputs[0])
		exposure_group.links.new(node_y.inputs[1], node_pow.outputs[0])
		exposure_group.links.new(node_z.inputs[1], node_pow.outputs[0])

		exposure_group.links.new(node_x.inputs[0], node_separate.outputs[0])
		exposure_group.links.new(node_y.inputs[0], node_separate.outputs[1])
		exposure_group.links.new(node_z.inputs[0], node_separate.outputs[2])
		
		exposure_group.links.new(node_x.outputs[0], node_combine.inputs[0])
		exposure_group.links.new(node_y.outputs[0], node_combine.inputs[1])
		exposure_group.links.new(node_z.outputs[0], node_combine.inputs[2])

		# link inputs
		exposure_group.links.new(group_inputs.outputs['Color'], node_separate.inputs[0])
		exposure_group.links.new(group_inputs.outputs['Exposure'], node_pow.inputs[0])


		#link output
		exposure_group.links.new(node_combine.outputs[0], group_outputs.inputs['Output'])
		
		return exposure_group
	# Helper
	
	def get_asset_naming_convention(self):
		asset_convention = self.param['lm_asset_naming_convention']
		
		asset_naming_convention = N.NamingConvention(self.context, self.asset_name, asset_convention)
		naming_convention = asset_naming_convention.naming_convention

		naming_convention['assetname'] = self.asset_name

		return naming_convention
	
	def get_mesh_naming_convention(self):
		mesh_convention = self.param['lm_mesh_naming_convention']
		naming_convention = []

		mesh_names = [path.basename(path.splitext(t)[0]) for t in self.meshes]
		for i,m in enumerate(mesh_names):
			mesh_naming_convention = N.NamingConvention(self.context, m, mesh_convention, self.meshes[i])
			naming_convention.append(mesh_naming_convention.naming_convention)

		return naming_convention

	def get_texture_naming_convention(self):
		texture_convention = self.param['lm_texture_naming_convention']

		naming_convention = {}

		for mesh_name,textures in self.textures.items():
			texture_names = [path.basename(path.splitext(t)[0]) for t in textures]

			texture_naming_convention = {}
			if len(self.jsons) == 0: # There is no Json file

				for i,t in enumerate(texture_names):
					t_naming_convention = N.NamingConvention(self.context, t, texture_convention)
					
					try:
						channel = self.param['lm_texture_channels'][t_naming_convention.naming_convention['channel']].channel
					except KeyError as k:
						print('The channel name "{}" doesn\'t exist in the textureset naming convention \nfile skipped : {}'.format(t_naming_convention.naming_convention['channel'], t))
						continue

					basename = t_naming_convention.pop_name(t_naming_convention.naming_convention['channel'])['fullname'].lower()

					if basename not in texture_naming_convention.keys():
						texture_naming_convention[basename] = t_naming_convention.naming_convention

					chan = {'name':t, 'file':self.textures[mesh_name][i]}

					# Feed scn_asset
					texture = self.scn_asset.texture_list.add()
					texture.channel = channel
					texture.file_path = t

					if 'channels' in texture_naming_convention[basename].keys():
						if len(texture_naming_convention[basename]['channels'].keys()):
							texture_naming_convention[basename]['channels'][channel] = chan
						else:
							texture_naming_convention[basename]['channels'] = {channel:chan}
					else:
						texture_naming_convention[basename]['channels'] = {channel:chan}

					t = t.replace(channel, '')
					
			else:
				json_data = self.json_data
				json = json_data[mesh_name]

				for mat in json['materials']:
					scene_materials = [m for m in bpy.data.materials if mat['material'] in m.name]
					if len(scene_materials):
						for m in scene_materials:
							if len(m.name) == len(mat['material']) + 4:
								incr = re.compile(r'[.][0-90-90-9]', re.IGNORECASE)
								incr.finditer(m.name)
						material_name = scene_materials.pop().name
					else:
						material_name = mat['material']
					textures = mat['textures']
					for texture in textures:
						if texture['file'] == 'null':
							texture['file'] = None
							texture_name = None
							texture_path = None
							t_naming_convention = N.NamingConvention(self.context, '', self.param['lm_texture_naming_convention'])
							channel = ''
						else:
							texture_name = path.splitext(texture['file'])[0]
							texture_path = path.join(self.get_asset_texture_folder(mesh_name), texture['file'])

							t_naming_convention = N.NamingConvention(self.context, texture_name, self.param['lm_texture_naming_convention'])
							channel = texture['channel']

							# Feed scn_asset
							scn_texture = self.scn_asset.texture_list.add()
							scn_texture.channel = channel
							scn_texture.file_path = texture['file']

							# try to feed textures per material
							try:
								scn_texture = self.scn_asset.material_list[material_name].texture_list.add()
								scn_texture.channel = channel
								scn_texture.file_path = texture['file']
							except KeyError:
								print('Lineup Maker : The material "{}" is not registered in the asset or is not applied on the mesh'.format(material_name))

						t_naming_convention.naming_convention['channel'] = channel

						if material_name not in texture_naming_convention.keys():
							texture_naming_convention[material_name] = t_naming_convention.naming_convention

						chan = {'name':texture_name, 'file':texture_path}

						if 'channels' in texture_naming_convention[material_name].keys():
							if len(texture_naming_convention[material_name]['channels'].keys()):
								texture_naming_convention[material_name]['channels'][channel] = chan
							else:
								texture_naming_convention[material_name]['channels'] = {channel:chan}
						else:
							texture_naming_convention[material_name]['channels'] = {channel:chan}
						
						# t = t.replace(channel, '')
		
			naming_convention[mesh_name] = texture_naming_convention
		
		return naming_convention

	def get_asset_name(self, meshes):
		return path.basename(path.dirname(meshes[0]))
	
	def get_asset_root(self, meshes):
		return path.dirname(meshes[0])

	def get_asset_texture_folder(self, mesh_name):
		return path.join(self.asset_root, mesh_name)

	def get_json_data(self):
		json_data = {}
		if not len(self.jsons):
			return None
		
		for j in self.jsons:
			json_name = path.splitext(path.basename(j))[0]
			with open(j, 'r', encoding='utf-8-sig') as json_file:  
				data = json.load(json_file)
				json_data[json_name] = data

		return json_data

	@check_asset_exist
	def select_asset(self):
		bpy.data.collections[self.asset_name].select_set(True)

	def create_texture_basename_dict(self, mesh_name, texture_names=None):
		if texture_names is None:
			texture_names = [path.basename(path.splitext(t)[0]) for t in self.textures[mesh_name]]
		
		basename_dict = {}

		for i,t in enumerate(texture_names):
			basename = self.get_texture_basename(t)
			if basename not in basename_dict.keys():
				basename_dict[basename] = {}
		
		return basename_dict

	@check_asset_exist    
	def select_objects(self):
		curr_asset_collection = bpy.data.collections[self.asset_name]
		bpy.ops.object.select_all(action='DESELECT')
		for o in curr_asset_collection.all_objects:
			o.select_set(True)
	
	def remove_objects(self):
		self.select_objects()

		bpy.ops.object.delete()

	@check_asset_exist
	def print_asset_objects_name(self):
		names = self.get_objects_name()
		for n in names:
			print(n)

	@check_asset_exist
	def get_objects_name(self):
		names = []
		curr_asset_collection = bpy.data.collections[self.asset_name]
		for o in curr_asset_collection.all_objects:
			names.append(o.name)
		
		return names
	
	@check_asset_exist
	def rename_objects(self):
		curr_asset_collection = bpy.data.collections[self.asset_name]
		separator = '.'
		for o in curr_asset_collection.all_objects:
			splited_name = o.name.split(separator)[:-1]
			name = ''
			for i,split in enumerate(splited_name):
				name = name + split
				if i < len(splited_name) - 1:
					name = name + separator
			o.name = name

	def remove_asset(self):
		if self.asset_name in bpy.data.collections:
			bpy.data.collections.remove(bpy.data.collections[self.asset_name])
			H.set_active_collection(self.context, V.LM_ASSET_COLLECTION)
		if self.asset_name in self.param['lm_asset_list']:
			for i,mat in enumerate(self.param['lm_asset_list'][self.asset_name].material_list):
				# Trying to remove material to avoid doubles
				if mat.material is not None:
					bpy.data.materials.remove(mat.material)
			
			H.remove_bpy_struct_item(self.context.scene.lm_asset_list, self.asset_name)
			# self.param['lm_asset_list'][self.asset_name].material_list.clear()
			

	# Properties
	@property
	def texture_channel_names(self):
		texture_channels = []
		for c in self.param['lm_texture_channels']:
			if c.name not in texture_channels:
				texture_channels.append(c.name.lower())

		return texture_channels

	@property
	def channels(self):
		channels = {}
		for c in self.param['lm_channels']:
			if c.name not in channels:
				channels[c.name] = {'linear':c.linear, 'normal_map':c.normal_map, 'inverted':c.inverted}

		return channels
	
	@property
	def asset_naming_convention(self):
		if self._asset_naming_convention is None:
			self._asset_naming_convention = self.get_asset_naming_convention()
		
		return self._asset_naming_convention
	
	@property
	def mesh_naming_convention(self):
		if self._mesh_naming_convention is None:
			self._mesh_naming_convention = self.get_mesh_naming_convention()
		
		return self._mesh_naming_convention
	
	@property
	def texture_naming_convention(self):
		if self._texture_naming_convention is None:
			self._texture_naming_convention = self.get_texture_naming_convention()
		
		return self._texture_naming_convention

	@property
	def json_data(self):
		if self._json_data is None:
			self._json_data = self.get_json_data()
		
		return self._json_data

	def get_asset(self):
		if len(self.asset_naming_convention) and len(self.mesh_naming_convention):
			asset = {}
			for m in self.mesh_naming_convention:
				texture_set = {}
				mesh = m['file']

				texture_naming_convention = self.texture_naming_convention

				for t in texture_naming_convention[m['fullname']].keys():
					if t not in texture_set.keys():
						texture_set[t] = {}

				for basename,t in texture_naming_convention[m['fullname']].items():

					for channel_name in t['channels'].keys():
						if channel_name in self.channels.keys():
							texture_set[basename][channel_name] = {'file':t['channels'][channel_name]['file'],
																	'linear':self.channels[channel_name]['linear'],
																	'normal_map':self.channels[channel_name]['normal_map'],
																	'inverted':self.channels[channel_name]['inverted']}

				asset[m['fullname']] = (mesh, texture_set)
			
			return asset

		else:
			print('Lineup Maker : Asset "{}" is not valid'.format(self.asset_name))
			return None

