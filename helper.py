import bpy, os, shutil
from . import variables as V

def create_folder_if_neeed(path):
	if not os.path.exists(path):
			os.makedirs(path)

def delete_folder_if_exist(path):
	if os.path.exists(path):
		shutil.rmtree(path)

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


def set_chapter(self, chapter_nc, asset_nc):
	match = True
	if len(chapter_nc.naming_convention['name']):
		for word in chapter_nc.naming_convention['name']:
			if word not in asset_nc.naming_convention['name']:
				match = False
				break
	else:
		match = False
	
	if not match:
		self.chapter = ''
		for i,word in enumerate(chapter_nc.word_list):
			if word in asset_nc.naming_convention.keys():
				if i < len(chapter_nc.word_list) - 1:
					self.chapter += asset_nc.naming_convention[word].upper() + '_'
				else:
					self.chapter += asset_nc.naming_convention[word].upper()
		
		return True
	else:
		return False

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

