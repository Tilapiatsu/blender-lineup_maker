import bpy
from . import variables as V
from . import helper as H
from . import preferences as P
from . import naming_convention as N
from . import material as M
from . import logger as L
from os import path, listdir
import time
import sys
import re
import json, codecs
from functools import wraps

class LMAsset(object):
	def __init__(self, context, root_folder):
		self.log = L.Logger(context='ASSET_FORMAT')
		self.context = context
		self.scn = context.scene
		self.param = V.GetParam(self.scn).param
		self.root_folder = root_folder
		self.asset_name = path.basename(root_folder)
		self.texture_set = {}
		self.imported_materials = {}
		self.imported_textures = {}
		
		self._meshes = None
		self._mesh_names = None
		self._textures = None
		self._jsons = None
		self._texture_channels = None
		self._channels = None
		self._asset_naming_convention = None
		self._mesh_naming_convention = None
		self._texture_naming_convention = None
		self._valid = None

		self.asset = None
		self.scn_asset = None
		
	# Decorators
	def check_asset_exist(func):
		def func_wrapper(self, *args, **kwargs):
			if self.asset_name in bpy.data.collections:
				return func(self, *args, **kwargs)
			else:
				self.log.info('Asset doesn\'t exist in current scene')
				return None
		return func_wrapper

	def check_length(func):
		def func_wrapper(self, *args, **kwargs):
			if not len(self.meshes):
				self.log.info('No file found in the asset folder')
				return None
			else:
				return func(self, *args, **kwargs)
		return func_wrapper

	# Methods
	def import_asset(self):
		self.import_mesh()
		self.feed_texture_to_material()

		if not len(self.log.failure):
			self.log.store_success('Asset "{}" imported successfully'.format(self.asset_name))

		return True, self.log.success, self.log.failure
	
	def update_asset(self):
		updated = self.update_mesh()
		if updated:
			self.feed_texture_to_material()

			if not len(self.log.failure):
				self.log.store_success('Asset "{}" updated successfully'.format(self.asset_name))

		return updated, self.log.success, self.log.failure

	@check_length
	def import_mesh(self, update=False):
		curr_asset_collection, _ = H.create_asset_collection(self.context, self.asset_name)

		H.set_active_collection(self.context, self.asset_name)

		# register the mesh in scene variable
		self.scn_asset = self.context.scene.lm_asset_list.add()
		self.scn_asset.name = self.asset_name
		self.scn_asset.collection = curr_asset_collection
		self.scn_asset.asset_root = path.dirname(self.meshes[0].path)

		global_import_date = 0.0

		for m in self.meshes:
			if not m.is_valid:
				self.log.info('Mesh "{}" dosn\'t exist or file format "{}" not compatible'.format(m.name, m.ext))
				continue
			
			if m.use_json:
				self.scn_asset.wip = m.json.is_wip
				self.scn_asset.triangles = m.json.triangles
				self.scn_asset.vertices = m.json.vertices
				self.scn_asset.has_uv2 = m.json.has_uv2

				self.scn_asset.hd_status = m.json.hd_status
				self.scn_asset.ld_status = m.json.ld_status
				self.scn_asset.baking_status = m.json.baking_status
			
			mesh_path = m.path
			file = m.file
			ext = m.ext
			name = m.name

			# Store the list of material in the blender file before importing the mesh
			initial_scene_materials = list(bpy.data.materials)

			if update:
				self.log.info('Updating file "{}" : {}'.format(file, time.ctime(path.getmtime(mesh_path))))
			else:
				self.log.info('Importing mesh "{}"'.format(name))
			
			m.import_mesh()

			# Store the list of material in the blender file after importing the mesh
			new_scene_materials = list(bpy.data.materials)

			# Get the imported materials
			self.imported_materials[name] = H.get_different_items(initial_scene_materials, new_scene_materials)

			self.log.info('{} new materials imported'.format(len(self.imported_materials[name])))
			for m in self.imported_materials[name]:
				self.log.info('		"{}"'.format(m.name))

			# Feed scene mesh list
			curr_mesh_list = self.scn_asset.mesh_list.add()
			curr_mesh_list.name = name
			curr_mesh_list.file_path = mesh_path
			curr_mesh_list.import_date = path.getmtime(mesh_path)
			curr_mesh_list.file_size = path.getsize(mesh_path)

			global_import_date += path.getctime(mesh_path)

			# Updating Materials
			for o in curr_asset_collection.objects:
				curr_mesh_object_list = curr_mesh_list.mesh_object_list.add()
				curr_mesh_object_list.mesh_name = o.name.lower()
				curr_mesh_object_list.mesh = o

				for m in o.material_slots:
					
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

		# Set scene import date
		if len(self.meshes):
			self.scn_asset.import_date = global_import_date / len(self.meshes)
		else:
			self.scn_asset.import_date = 0.0
		
		# Feed assets
		self.asset = self.get_asset()
	
	@check_length
	def update_mesh(self):
		# _, created = H.create_asset_collection(self.context, self.asset_name)
		H.set_active_collection(self.context, self.asset_name)

		curr_asset = self.param['lm_asset_list'][self.asset_name]

		need_update = False
		for f in self.meshes:
			file_name = path.splitext(path.basename(f.path))[0]
			file_time = path.getmtime(f.path)
			file_size = path.getsize(f.path)
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
			self.log.info('Updating asset "{}"'.format(self.asset_name))

			self.remove_asset()
			self.import_mesh(update=True)
			# Dirty fix to avoid bad mesh naming when updating asset
			self.rename_objects()
			self.log.store_success('Asset "{}" updated successfully'.format(self.asset_name))
			updated = True
			
		else:
			self.scn_asset = self.context.scene.lm_asset_list[self.asset_name]
			# self.asset = self.get_asset()
			self.log.store_success('Asset "{}" is already up to date'.format(self.asset_name))
			self.log.info('Asset "{}" is already up to date'.format(self.asset_name))
			updated = False
		
		return updated

	def feed_texture_to_material(self):
		for mesh_name in self.asset.keys():
			
			for mat in self.asset[mesh_name][1]:
				try:
					if len(self.asset[mesh_name][1]) == 0:
						self.log.warning('Mesh "{}" have no material applied to it \n	Applying generic material'.format(mesh_name))
						self.feed_material(self.context.scene.lm_asset_list[self.asset_name].material_list[mat].material)
					else:
						self.log.info('Applying material "{}" to mesh "{}"'.format(mat, mesh_name))
						self.feed_material(self.context.scene.lm_asset_list[self.asset_name].material_list[mat].material, self.asset[mesh_name][1][mat])
				except KeyError as k:
					self.log.warning('{}'.format(k))
					self.log.store_failure('Asset "{}" failed assign material "{}" with mesh "{}" :\n{}'.format(self.asset_name, mat, mesh_name, k))
		
		
	def feed_material(self, material, texture_set=None):
		M.create_bsdf_material( self, material, texture_set)

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

		for i,m in enumerate(self.mesh_names):
			mesh_naming_convention = N.NamingConvention(self.context, m, mesh_convention, self.meshes[i])
			naming_convention.append(mesh_naming_convention.naming_convention)

		return naming_convention

	def get_texture_naming_convention(self):
		texture_convention = self.param['lm_texture_naming_convention']

		naming_convention = {}

		for m in self.meshes:
			mesh_name = m.name
			texture_sets = m.texture_sets

			texture_naming_convention = {}

			if not m.use_json:
				for t in texture_sets:
					t_naming_convention = N.NamingConvention(self.context, t.name, texture_convention)
						
					try:
						channel = self.param['lm_texture_channels'][t_naming_convention.naming_convention['channel']].channel
					except KeyError as k:
						self.log.info('The channel name "{}" doesn\'t exist in the textureset naming convention \nfile skipped : {}'.format(t_naming_convention.naming_convention['channel'], t.name))
						continue
					
					t.channel = channel
					basename = t_naming_convention.pop_name(t_naming_convention.naming_convention['channel'])['fullname'].lower()

					if basename not in texture_naming_convention.keys():
						texture_naming_convention[basename] = t_naming_convention.naming_convention

					chan = {'name':t.name, 'file':t.path}

					# Feed scn_asset
					texture = self.scn_asset.texture_list.add()
					texture.channel = channel
					texture.file_path = t.path

					if 'channels' in texture_naming_convention[basename].keys():
						if len(texture_naming_convention[basename]['channels'].keys()):
							texture_naming_convention[basename]['channels'][channel] = chan
						else:
							texture_naming_convention[basename]['channels'] = {channel:chan}
					else:
						texture_naming_convention[basename]['channels'] = {channel:chan}

					t.name = t.name.replace(channel, '')
			
			else:
				json = m.json_data

				for mat in json['materials']:

					found = False
					for imported_mats in self.imported_materials.values():
						if found:
							break
						for imported_mat in imported_mats:
							if found:
								break
							if mat['material'] in imported_mat.name:
								material_name = imported_mat.name
								# imported_mats.remove(imported_mat)
								found = True
								break

					if not found:
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
								self.log.info('The material "{}" is not registered in the asset or is not applied on the mesh'.format(material_name))

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


			naming_convention[mesh_name] = texture_naming_convention
		
		return naming_convention

	def get_asset_texture_folder(self, mesh_name):
		return path.join(self.root_folder, mesh_name)

	def get_imported_material_name(self, json_material):
		for imported_mats in self.imported_materials.values():
			for imported_mat in imported_mats:
				if json_material and json_material in imported_mat.name:
					return imported_mat.name
				elif json_material and json_material[0:-4] in imported_mat.name:
					return imported_mat.name

		return json_material

	@check_asset_exist
	def select_asset(self):
		bpy.data.collections[self.asset_name].select_set(True)

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
		H.remove_asset(self.context, self.asset_name)
	
	def get_asset(self):
		asset = {}
		asset_files = LMAssetFiles(self.root_folder)
		
		for mesh in asset_files.files:
			texture_sets = {}

			if mesh.use_json:
				for mat_name, texture_set in mesh.materials.items():
					texture_set.material = mat_name
					texture_set.imported_material = self.get_imported_material_name(mat_name)
					texture_sets[texture_set.imported_material] = {}
					for t in texture_set.textures:							
						texture_sets[texture_set.imported_material][t.channel] = {'file':t.path,
																'linear':self.channels[t.channel]['linear'],
																'normal_map':self.channels[t.channel]['normal_map'],
																'inverted':self.channels[t.channel]['inverted']}
			
			else:
				if len(self.asset_naming_convention) and len(self.mesh_naming_convention):
					texture_naming_convention = self.texture_naming_convention
					for t in texture_naming_convention[m['fullname']].keys():
						if t not in texture_sets.keys():
							texture_sets[t] = {}

					for basename,t in texture_naming_convention[m['fullname']].items():
						for channel_name in t['channels'].keys():
							if channel_name in self.channels.keys():
								texture_sets[basename][channel_name] = {'file':t['channels'][channel_name]['file'],
																		'linear':self.channels[channel_name]['linear'],
																		'normal_map':self.channels[channel_name]['normal_map'],
																		'inverted':self.channels[channel_name]['inverted']}
				
				else:
					self.log.info('Asset "{}" is not valid'.format(self.asset_name))
					self.log.info('		"{}"'.format(self.asset_naming_convention))
					self.log.info('		"{}"'.format(self.mesh_naming_convention))
					return None

			asset[mesh.asset_name] = (mesh, texture_sets)

		return asset
	

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

	# Properties
	@property
	def texture_channel_names(self):
		if self._texture_channels is None:
			self._texture_channels = []
			for c in self.param['lm_texture_channels']:
				if c.name not in self._texture_channels:
					self._texture_channels.append(c.name.lower())

		return self._texture_channels

	@property
	def channels(self):
		if self._channels is None:
			self._channels = {}
			if not len(self.param['lm_channels']):
				self._channels = V.LM_DEFAULT_CHANNELS
			else:
				for c in self.param['lm_channels']:
					if c.name not in self._channels:
						self._channels[c.name] = {'linear':c.linear, 'normal_map':c.normal_map, 'inverted':c.inverted}

		return self._channels
	
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
	def is_valid(self):
		if self._valid is None:
			self._valid = True

			if len(self.meshes) < 1:
				self._valid = False
				self.log.error('No valid mesh file in the asset root : {}'.format(self.root_folder))
				return self._valid

			a_nc = self.asset_naming_convention
			kw_nc = N.NamingConvention(self.context, self.asset_name, self.context.scene.lm_asset_naming_convention)
			keywords = '\n'
			for keyword in a_nc['keywords']:
				keywords += keyword + '\n'
				if keyword not in a_nc.keys() and keyword not in kw_nc.optionnal_words:
					self._valid = False
					self.log.error('Invalid Keyword : {}'.format(keyword))
					return self._valid
		
		return self._valid

	@property
	def meshes(self):
		if self._meshes is None:
			self._meshes = [LMMeshFile(path.join(self.root_folder, f)) for f in listdir(self.root_folder) if path.isfile(path.join(self.root_folder, f)) and path.splitext(f)[1].lower() in V.LM_COMPATIBLE_MESH_FORMAT.keys()]
		
		return self._meshes
	
	@property
	def mesh_names(self):
		if self._mesh_names is None:
			self._mesh_names = [n.name for n in self.meshes]
		
		return self._mesh_names
	
	@property
	def textures(self):
		if self._textures is None:
			self._textures = {}
			for m in self.mesh_names:
				try:
					self._textures[m.name] = [path.join(self.root_folder, m.name, t) for t in listdir(path.join(self.root_folder, m.name)) if path.isfile(path.join(self.root_folder, m.name, t)) and path.splitext(t)[1].lower() in V.LM_COMPATIBLE_TEXTURE_FORMAT.keys()]
					for m, textures in self._textures.items():
						self.log.info('{} texture files found for mesh {}'.format(len(textures), m))
						for t in textures:
							self.log.info(' 		{} '.format(t))
				except FileNotFoundError as e:
					self._textures[m] = []
					self.log.warning('folder dosn\'t exist "{}"'.format(path.join(self.root_folder, m)))
		
		return self._textures


class LMAssetFiles(object):
	def __init__(self, asset_root):
		self.log = L.Logger('LMAssetFiles')
		self._asset_root = asset_root
		self._files = None
		self._texture_root = None

	def __len__(self):
		return len(self.files.keys())

	@property
	def asset_root(self):
		if path.exists(self._asset_root):
			return self._asset_root
		
		return None

	@property
	def is_valid(self):
		return self.asset_root is not None

	@property
	def files(self):
		if self._files is None:
			if self.is_valid:
				self._files = []
				files = [f for f in listdir(self.asset_root) if path.splitext(f)[1] in V.LM_COMPATIBLE_MESH_FORMAT.keys()]
				for f in files:
					file = path.basename(f)
					name, ext = path.splitext(file)

					self._files.append(LMMeshFile(path.join(self.asset_root, f)))
			else:
				self.log.error('Asset {} is not Valid'.format(self._asset_root))

		return self._files


class LMFile(object):
	def __init__(self, path):
		self.log = L.Logger('LMFile')
		self.path = path
		self._name = None
		self._file = None
		self._ext = None
		self._is_compatible_ext = None
		self._compatible_format = None

	@property
	def name(self):
		if self._name is None:
			self._name = path.basename(path.splitext(self.path)[0])

		return self._name

	@property
	def file(self):
		if self._file is None:
			self._file = path.basename(self.path)

		return self._file

	@property
	def ext(self):
		if self._ext is None:
			self._ext = path.splitext(self.file)[1].lower()

		return self._ext
	
	@property
	def dirname(self):
		return path.dirname(self.path)

	@property
	def is_compatible_ext(self):
		if self._is_compatible_ext is None:
			self._is_compatible_ext = self.ext in self.compatible_formats.keys()

		return self._is_compatible_ext
	
	@property
	def compatible_format(self):
		if self._compatible_format is None:
			if self._is_compatible_ext:
				self._compatible_format = self.compatible_formats[self.ext]
			else:
				self._compatible_format = False

		return self._compatible_format

	@property
	def compatible_formats(self):
		return {}


class LMMeshFile(LMFile):
	def __init__(self, mesh_path):
		super(LMMeshFile, self).__init__(mesh_path)
		self.log = L.Logger('LMMeshFile')
		self._json = None
		self._json_data = None
		self._materials = None
		self._asset_root = None
		self._asset_name = None
		self._texture_root = None
		self._texture_names = None
		self._texture_file_path = None

	@property
	def asset_name(self):
		if self._asset_name is None:
			self._asset_name = path.basename(self.asset_root)

		return self._asset_name

	@property
	def is_valid(self):
		return path.isfile(self.path) and self.is_compatible_ext

	@property
	def json(self):
		if self._json is None:
			json = LMJson(path.join(path.dirname(self.path), path.splitext(path.basename(self.path))[0]) + '.json')

			if json.is_valid:
				self._json = json
			else:
				self._json = False

		return self._json

	@property
	def use_json(self):
		if not self.json:
			return False
		else:
			return True

	@property
	def json_data(self):
		if self._json_data is None:
			if not self.use_json:
				self._json_data = False
			else:
				self._json_data = self.json.json_data
		
		return self._json_data

	@property
	def ext(self):
		if self._ext is None:
			self._ext = path.splitext(self.file)[1].lower()
		
		return self._ext

	@property
	def file(self):
		if self._file is None:
			self._file = path.basename(self.path)
		
		return self._file

	@property
	def compatible_formats(self):
		return V.LM_COMPATIBLE_MESH_FORMAT
		
	@property
	def texture_file_path(self):
		if self._texture_file_path is None:
			if path.exists(self.texture_root):
				self._texture_file_path = [path.join(self.texture_root, f) for f in listdir(self.texture_root) if path.splitext(f)[1] in V.LM_COMPATIBLE_TEXTURE_FORMAT.keys()]
			else:
				self._texture_file_path = [] 
		
		return self._texture_file_path
	
	@property
	def texture_root(self):
		if self._texture_root is None:
			self._texture_root = path.join(self.asset_root, self.name)
	
		return self._texture_root

	@property
	def asset_root(self):
		if self._asset_root is None:
			self._asset_root = path.dirname(self.path)
		
		return self._asset_root

	@property
	def texture_names(self):
		if self._texture_names is None:
			self._texture_names = [path.basename(t) for t in self.texture_file_path]

		return self._texture_names

	@property
	def materials(self):
		if self._materials is None:
			self._materials = {}
			all_textures = [path.basename(t) for t in self.texture_file_path]

			if self.use_json:
				for mat in self.json_data['materials']:				
					textures = []
					for t in mat['textures']:
						if t['file'] in all_textures:
							textures.append(path.join(self.texture_root, t['file']))
							
					self._materials[mat['material']] = LMTextureSet(textures, self.json_data)
			else:
				pass

		return self._materials

	def import_mesh(self):
		if not self.is_valid:
			self.log.warning('Mesh is not valid')
			return

		kwargs = {}
		kwargs.update({'filepath':self.path})
		kwargs.update(self.compatible_format[1])
		
		# run Import Command
		self.compatible_format[0](**kwargs)


class LMJson(LMFile):
	def __init__(self, json_path):
		super(LMJson, self).__init__(json_path)
		self.log = L.Logger('LMJson')
		self._json_data = None

	# Decorator
	def check_status(func):
		@wraps(func)
		def func_wrapper(self):
			try:
				status = int(func(self))
			except ValueError as v:
				status = V.Status.NOT_SET.value
			return status
		return func_wrapper

	# Properties
	@property
	def is_valid(self):
		return path.isfile(self.path)
	
	@property
	def json_data(self):
		if self._json_data is None:
			self._json_data = self.get_json_data()
		
		return self._json_data

	@property
	def is_wip(self):
		return self.get_json_attr('isWip')

	@property
	def triangles(self):
		return self.get_json_attr('triangles')

	@property
	def vertices(self):
		return self.get_json_attr('vertices')

	@property
	def has_uv2(self):
		return self.get_json_attr('hasUV2')

	@property
	@check_status
	def hd_status(self):
		return self.get_json_attr('HDStatus')

	@property
	@check_status
	def ld_status(self):
		return self.get_json_attr('LDStatus')
	
	@property
	@check_status
	def baking_status(self):
		return self.get_json_attr('BakingStatus')
	
	def get_json_attr(self, attr):
		if not self.json_data:
			return ''
		else:
			if attr in self.json_data:
				return self.json_data[attr]
			else:
				self.log.warning('Attribute "{}" doesn\'t exist in json data'.format(attr))
				return ''

	def get_json_data(self):
		json_data = {}
		if not self.is_valid:
			return False

		with open(self.path, 'r', encoding='utf-8-sig') as json_file:  
			data = json.load(json_file)
			json_data = data

		return json_data


class LMTextureFile(LMFile):
	def __init__(self, texture_path):
		super(LMTextureFile, self).__init__(texture_path)
		self.log = L.Logger('LMTextureFile')
		self._channel = None

	@property
	def channel(self):
		return self._channel

	@channel.setter
	def channel(self, channel):
		self._channel = channel

	
	@property
	def compatible_formats(self):
		return V.LM_COMPATIBLE_TEXTURE_FORMAT

	
class LMTextureSet(object):
	def __init__(self, texture_file_path, json_data=None):
		self.log = L.Logger('LMTextureSet')
		self.texture_file_path = texture_file_path
		self.json_data = json_data
		self._material = None
		self._imported_material = None
		self._texture_root = None
		self._textures = None
		self._texture_names = None
	
	def __len__(self):
		return len(self.textures)

	@property
	def texture_root(self):
		if self._texture_root is None:
			if len(self.texture_file_path) and path.exists(self.texture_file_path[0]):
				self._texture_root = path.dirname(self.texture_file_path[0])
	
		return self._texture_root

	@property
	def textures(self):
		if self._textures is None:
			if self.json_data:
				self._textures = []
				for m in self.json_data['materials']:
					if m['material'] == self.material:
						for t in m['textures']:
							if t['file'] not in [None, 'null'] and self.texture_root is not None:
								texture_path = path.join(self.texture_root, t['file'])
								tf = LMTextureFile(texture_path)

								tf.channel = t['channel']

								self._textures.append(tf)
						break
			else:
				self._textures = [LMTextureFile(t) for t in self.texture_file_path if path.isfile(t)]

		return self._textures

	@property
	def texture_names(self):
		if self._texture_names is None:
			self._texture_names = [path.basename(t) for t in self.texture_file_path]

		return self._texture_names

	@property
	def material(self):
		if self._material is None:
			if self.json_data:
				for mat in self.json_data['materials']:
					for t in mat['textures']:
						if t['file'] in self.texture_names:
							self._material = mat['material']
							return self._material
			else:
				pass

		return self._material

	@material.setter
	def material(self, material):
		self._material = material

	@property
	def imported_material(self):
		return self._imported_material

	@imported_material.setter
	def imported_material(self, material):
		self._imported_material = material