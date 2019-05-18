import bpy
import os

def print_node_inputs(node):
	for i, node in enumerate(node.inputs):
		print(i, node.name)

def print_node_outputs(node):
	for i, node in enumerate(node.outupts):
		print(i, node.name)

def feed_input_indices(context, input_indices):
	channels = [c.channel for c in context.scene.lm_texture_channels]
	names = [n.name for n in context.scene.lm_texture_channels]
	for channel, value in input_indices.items():
		if channel in channels:
			input_indices[channel].update({'name':names[channels.index(channel)]})
	
	return input_indices

def create_bsdf_material(context, material, texture_set):
	input_indices = {'Base Color':{'index':0},
					'Metallic':{'index':4},
					'Roughness':{'index':7},
					'Alpha':{'index':18},
					'Normal':{'index':19}}
	
	input_indices = feed_input_indices(context, input_indices)

	tree = material.node_tree
	nodes = tree.nodes

	location = (0, 0)
	incr = 300

	nodes.clear()

	output = nodes.new('ShaderNodeOutputMaterial')
	output.location = location
	location = (location[0] - incr, location[1])

	shader = nodes.new('ShaderNodeBsdfPrincipled')
	shader.location = location
	location = (location[0] - incr - 400, location[1])

	tree.links.new(shader.outputs[0], output.inputs[0])

	for channel, input_idx in input_indices.items():
		try:
			t = texture_set[channel][0]
		except KeyError as k:
			print('No texture found for channel "{}" in the material "{}".'.format(channel, material.name))
			continue

		dir_name = os.path.dirname(t)
		file_name = os.path.basename(t)

		texture = nodes.new('ShaderNodeTexImage')

		bpy.ops.image.open(filepath=t, directory=dir_name, show_multiview=False)
		texture.image = bpy.data.images[file_name]
		texture.label = os.path.splitext(file_name)[0]

		texture.location = location
		

		if texture_set[channel][2]:
			texture.image.colorspace_settings.name = 'Linear'
			normal_map = nodes.new('ShaderNodeNormalMap')
			normal_map.location = (location[0] + incr, location[1])
			tree.links.new(texture.outputs[0], normal_map.inputs[1])
			tree.links.new(normal_map.outputs[0], shader.inputs[input_idx['index']])
		elif texture_set[channel][1]:
			texture.image.colorspace_settings.name = 'Linear'
			tree.links.new(texture.outputs[0], shader.inputs[input_idx['index']])
		else:
			tree.links.new(texture.outputs[0], shader.inputs[input_idx['index']])
	
		location = (location[0], location[1] - incr)
	return output