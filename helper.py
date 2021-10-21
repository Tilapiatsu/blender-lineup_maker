import bpy, os, shutil, stat
from . import variables as V
from . import naming_convention as N

def create_folder_if_neeed(path):
	if not os.path.exists(path):
			os.makedirs(path)

def delete_folder_if_exist(path):
	if os.path.exists(path):
		shutil.rmtree(path, onerror=file_acces_handler)

def file_acces_handler(func, path, exc_info):
	print('Handling Error for file ' , path)
	print(exc_info)
	# Check if file access issue
	if not os.access(path, os.W_OK):
	   # Try to change the permision of file
	   os.chmod(path, stat.S_IWUSR)
	   # call the calling function again
	   func(path)

def get_layer_collection(layer_collection, collection_name):
	found = None
	if (layer_collection.name == collection_name):
		return layer_collection
	for layer in layer_collection.children:
		found = get_layer_collection(layer, collection_name)
		if found:
			return found

def create_asset_collection(context, name):
	collections = bpy.data.collections
	if name in collections:
		return collections[name], False
	else:
		new_collection = bpy.data.collections.new(name)
		context.collection.children.link(new_collection)
		return new_collection, True


def set_active_collection(context, name):
	context.view_layer.active_layer_collection = get_layer_collection(context.view_layer.layer_collection, name)

def slice(pattern, sep='_'):
	sep_in = '<'
	sep_out = '>'
	
	sliced = pattern.split(sep)

	sliced_result = []

	for s in sliced:
		if sep_in in s:
			sliced_in = s.split(sep_in)
			for ss in sliced_in:
				if ss is not '':
					sliced_result.append(ss.lower()[:-1])
		else:
			sliced_result.append(s.lower())

	return sliced_result


def set_chapter(self, asset,  chapter_nc, asset_nc):
	new_chapter = False
	new_section = False
	if len(chapter_nc.naming_convention['name']):
		for word in chapter_nc.naming_convention['name']:
			if word not in asset_nc.naming_convention['name']:
				new_chapter = True
				break
	else:
		new_chapter = True
	
	if asset.section != self.section:
		new_section = True

	if  new_chapter:
		self.chapter = ''
		for i,word in enumerate(chapter_nc.word_list):
			if word in asset_nc.naming_convention.keys():
				if i < len(chapter_nc.word_list) - 1:
					self.chapter += asset_nc.naming_convention[word].upper() + '_'
				else:
					self.chapter += asset_nc.naming_convention[word].upper()
	
	if new_section:
		self.section = asset.section

	return new_chapter, new_section

def remove_bpy_struct_item(bpy_struct, name):
	for i,item in enumerate(bpy_struct):
		if item.name == name:
			bpy_struct.remove(i)
			return i

def get_current_frame_range(context):
	return context.scene.frame_end + 1 - context.scene.frame_start

def get_curr_render_extension(context):
	return V.LM_OUTPUT_EXTENSION[bpy.context.scene.render.image_settings.file_format]

def clear_composite_tree(context):
	tree = context.scene.node_tree
	nodes = tree.nodes
	nodes.clear()

def get_different_items(list1, list2):
	""" Compare the list1 and list2 and return the elements of list2 that is not in list1 """
	difference = []
	if len(list1) < len(list2):
		for i in list2:
			if i not in list1:
				difference.append(i)
	
	return difference

def get_datas_from_collection(collection_name):
	datas = {'materials' : set(),
			'objects': set(),
			'meshes': set(),
			'images' : set(),
			'actions' : set()}

	if collection_name in bpy.data.collections.keys():
		for o in bpy.data.collections[collection_name].objects:
			datas['objects'].add(o)
			if o.type == 'MESH':
				datas['meshes'].add(o.data)
			if o.animation_data:
				datas['actions'].add(o.animation_data.action)
			for ms in o.material_slots:
				datas['materials'].add(ms.material)
				if ms.material is not None:
					for n in ms.material.node_tree.nodes:
						if n.type == 'TEX_IMAGE':
							datas['images'].add(n.image)
	
	return datas

def select_asset(context, asset_name):
	if asset_name in bpy.data.collections:
		bpy.ops.object.select_all(action='DESELECT')
		for o in bpy.data.collections[asset_name].objects:
			o.select_set(True)

def sort_asset_list(asset_name_list, asset_list=None):
	if asset_list is None:
		asset_list = bpy.context.scene.lm_asset_list

	sorted_name_list = []
	asset_dict = {}
	for a in asset_name_list:
		section = asset_list[a].section
		if section not in asset_dict.keys():
			asset_dict[section] = [a,]
		else:
			asset_dict[section] += [a,]
	
	sorted_sections = list(asset_dict.keys())
	sorted_sections.sort()
	for s in sorted_sections:
		sorted_names = asset_dict[s]
		sorted_names.sort()
		sorted_name_list += sorted_names
	
	return sorted_name_list

def renumber_assets(context, asset_list=None):
	if asset_list is None:
		asset_list = context.scene.lm_asset_list

	asset_name_list = [a.name for a in asset_list]

	asset_name_list = sort_asset_list(asset_name_list, asset_list)

	for number,name in enumerate(asset_name_list):
		asset_list[name].asset_number = number + 1

def remove_asset(context, asset_name, remove=True):
	if asset_name in bpy.data.collections:
		# Get data from collection
		datas = get_datas_from_collection(asset_name)
		
		for o in datas['objects']:
			if o is not None and o.name in bpy.data.objects:
				print('Removing object : ', o.name)
				bpy.data.objects.remove(o)
		for m in datas['meshes']:
			if m is not None and m.name in bpy.data.meshes:
				print('Removing mesh : ', m.name)
				bpy.data.meshes.remove(m)
		for a in datas['actions']:
			if a is not None and a.name in bpy.data.actions:
				print('Removing action : ', a.name)
				bpy.data.actions.remove(a)
		for i in datas['images']:
			if i is not None and i.name in bpy.data.images:
				print('Removing image : ', i.name)
				bpy.data.images.remove(i)
		for m in datas['materials']:
			if m is not None and m.name in bpy.data.materials:
				print('Removing material : ', m.name)
				bpy.data.materials.remove(m)
		
		# unused_images_list = unused_images()

		# for i in unused_images_list:
		# 	if i in bpy.data.images:
		# 		print('Removing image : ', i)
		# 		bpy.data.images.remove(bpy.data.images[i])
		
		bpy.data.collections.remove(bpy.data.collections[asset_name])
		set_active_collection(context, V.LM_ASSET_COLLECTION)

	if asset_name in context.scene.view_layers:
		context.scene.view_layers.remove(context.scene.view_layers[context.scene.lm_asset_list[asset_name].view_layer])

	if asset_name in context.scene.lm_asset_list:
		if remove:
			remove_bpy_struct_item(context.scene.lm_asset_list, asset_name)
			remove_bpy_struct_item(context.scene.lm_render_queue, asset_name)
			remove_bpy_struct_item(context.scene.lm_last_render_list, asset_name)


def get_valid_camera(context, asset):
	cam = context.scene.lm_default_camera
	naming_convention = N.NamingConvention(context, asset.name, context.scene.lm_asset_naming_convention)
		
	for camera_keyword in context.scene.lm_cameras:
		match = True
		for keyword in camera_keyword.keywords:
			if keyword.keyword in naming_convention.naming_convention.keys():
				if naming_convention.naming_convention[keyword.keyword] != keyword.keyword_value.lower():
					match = False
					break
		
		if match:		
			cam = camera_keyword.camera
			break
	
	return cam

def set_rendering_camera(context, asset):
		cam = get_valid_camera(context, asset)
		context.scene.camera = bpy.data.objects[cam.name]
		asset.render_camera = cam.name
		
def image_all(image_key):
	# returns a list of keys of every data-block that uses this image

	return image_compositors(image_key) + \
		   image_materials(image_key) + \
		   image_node_groups(image_key) + \
		   image_textures(image_key) + \
		   image_worlds(image_key)


def image_compositors(image_key):
	# returns a list containing "Compositor" if the image is used in
	# the scene's compositor

	users = []
	image = bpy.data.images[image_key]

	# a list of node groups that use our image
	node_group_users = image_node_groups(image_key)

	# if our compositor uses nodes and has a valid node tree
	if bpy.context.scene.use_nodes and bpy.context.scene.node_tree:

		# check each node in the compositor
		for node in bpy.context.scene.node_tree.nodes:

			# if the node is an image node with a valid image
			if hasattr(node, 'image') and node.image:

				# if the node's image is our image
				if node.image.name == image.name:
					users.append("Compositor")

			# if the node is a group node with a valid node tree
			elif hasattr(node, 'node_tree') and node.node_tree:

				# if the node tree's name is in our list of node group
				# users
				if node.node_tree.name in node_group_users:
					users.append("Compositor")

	return distinct(users)


def image_materials(image_key):
	# returns a list of material keys that use the image

	users = []
	image = bpy.data.images[image_key]

	# list of node groups that use this image
	node_group_users = image_node_groups(image_key)

	for mat in bpy.data.materials:

		# if material uses a valid node tree, check each node
		if mat.use_nodes and mat.node_tree:
			for node in mat.node_tree.nodes:

				# if node is has a not none image attribute
				if hasattr(node, 'image') and node.image:

					# if the nodes image is our image
					if node.image.name == image.name:
						users.append(mat.name)

				# if image in node in node group in node tree
				elif node.type == 'GROUP':

					# if node group has a valid node tree and is in our
					# list of node groups that use this image
					if node.node_tree and \
							node.node_tree.name in node_group_users:
						users.append(mat.name)

	return distinct(users)


def image_node_groups(image_key):
	# returns a list of keys of node groups that use this image

	users = []
	image = bpy.data.images[image_key]

	# for each node group
	for node_group in bpy.data.node_groups:

		# if node group contains our image
		if node_group_has_image(node_group.name, image.name):
			users.append(node_group.name)

	return distinct(users)


def image_textures(image_key):
	# returns a list of texture keys that use the image

	users = []
	image = bpy.data.images[image_key]

	# list of node groups that use this image
	node_group_users = image_node_groups(image_key)

	for texture in bpy.data.textures:

		# if texture uses a valid node tree, check each node
		if texture.use_nodes and texture.node_tree:
			for node in texture.node_tree.nodes:

				# check image nodes that use this image
				if hasattr(node, 'image') and node.image:
					if node.image.name == image.name:
						users.append(texture.name)

				# check for node groups that use this image
				elif hasattr(node, 'node_tree') and node.node_tree:

					# if node group is in our list of node groups that
					# use this image
					if node.node_tree.name in node_group_users:
						users.append(texture.name)

		# otherwise check the texture's image attribute
		else:

			# if texture uses an image
			if hasattr(texture, 'image') and texture.image:

				# if texture image is our image
				if texture.image.name == image.name:
					users.append(texture.name)

	return distinct(users)


def image_worlds(image_key):
	# returns a list of world keys that use the image

	users = []
	image = bpy.data.images[image_key]

	# list of node groups that use this image
	node_group_users = image_node_groups(image_key)

	for world in bpy.data.worlds:

		# if world uses a valid node tree, check each node
		if world.use_nodes and world.node_tree:
			for node in world.node_tree.nodes:

				# check image nodes
				if hasattr(node, 'image') and node.image:
					if node.image.name == image.name:
						users.append(world.name)

				# check for node groups that use this image
				elif hasattr(node, 'node_tree') and node.node_tree:
					if node.node_tree.name in node_group_users:
						users.append(world.name)

	return distinct(users)

def unused_images():
	# returns a full list of keys of unused images

	unused = []

	# a list of image keys that should not be flagged as unused
	# this list also exists in images_shallow()
	do_not_flag = ["Render Result", "Viewer Node", "D-NOISE Export"]

	for image in bpy.data.images:
		if not image_all(image.name):

			# check if image has a fake user or if ignore fake users
			# is enabled
			if not image.use_fake_user:

				# if image is not in our do not flag list
				if image.name not in do_not_flag:
					unused.append(image.name)

	return unused

def distinct(seq):
	# returns a list of distinct elements

	return list(set(seq))

def node_group_has_image(node_group_key, image_key):
	# recursively returns true if the node group contains this image
	# directly or if it contains a node group a node group that contains
	# the image indirectly

	has_image = False
	node_group = bpy.data.node_groups[node_group_key]
	image = bpy.data.images[image_key]

	# for each node in our search group
	for node in node_group.nodes:

		# base case
		# if node has a not none image attribute
		if hasattr(node, 'image') and node.image:

			# if the node group is our node group
			if node.image.name == image.name:
				has_image = True

		# recurse case
		# if node is a node group and has a valid node tree
		elif hasattr(node, 'node_tree') and node.node_tree:
			has_image = node_group_has_image(
				node.node_tree.name, image.name)

		# break the loop if the image is found
		if has_image:
			break

	return has_image

def get_global_import_date(meshes):
	global_import_date = 0.0
	mesh_number = len(meshes)
	if mesh_number:
		for m in meshes:
			global_import_date += os.path.getctime(m)
		return global_import_date / mesh_number
	else:
		return 0.0


def switch_current_viewlayer( context, viewlayer_name):
	if viewlayer_name in context.scene.view_layers:
			context.window.view_layer = context.scene.view_layers[viewlayer_name]

def switch_shadingtype(context, shading_type):
	for a in context.screen.areas:
		if a.type == 'VIEW_3D':
			for s in a.spaces:
				if s.type =='VIEW_3D':
					s.shading.type = shading_type

def set_local_camera( context, camera_name):
	if not len(camera_name):
		return
	for a in context.screen.areas:
		if a.type == 'VIEW_3D':
			for s in a.spaces:
				if s.type =='VIEW_3D':
					s.camera = bpy.data.objects[camera_name]
					s.use_local_camera=True

def create_asset_view_layer(context, view_layer, default_view_layer_name):
	if view_layer not in context.scene.view_layers:
		print('LineupMaker : ViewLayer missing - Creating new Viewlayer "{}"'.format(view_layer))
		bpy.ops.scene.view_layer_add()
		context.window.view_layer.name = view_layer
		context.view_layer.use_pass_combined = False
		context.view_layer.use_pass_z = False

		switch_current_viewlayer(context, default_view_layer_name)

def update_view_layer(context, view_layer, updated_asset_list, view_layer_dict):
	print('LineupMaker : Updating Viewlayer "{}"'.format(view_layer))

	if view_layer in updated_asset_list:
		# print('LineupMaker : Updating visibility "{}"'.format(view_layer))
		for n in view_layer_dict.keys():
			if view_layer != n and view_layer != context.scene.lm_render_collection.name:
				curr_asset_view_layer = get_layer_collection(bpy.context.scene.view_layers[view_layer].layer_collection, n)
				if curr_asset_view_layer:
					curr_asset_view_layer.exclude = True
	else:
		# print('LineupMaker : Updating visibility "{}"'.format(view_layer))
		for n in updated_asset_list:
			if view_layer != n and view_layer != context.scene.lm_render_collection.name:
				curr_asset_view_layer = get_layer_collection(bpy.context.scene.view_layers[view_layer].layer_collection, n)
				if curr_asset_view_layer:
					curr_asset_view_layer.exclude = True

				
def get_view_layer_dict(context):
	d = {}
	for a in context.scene.lm_asset_list:
			d[a.view_layer] = get_layer_collection(context.view_layer.layer_collection, a.name)
	return d