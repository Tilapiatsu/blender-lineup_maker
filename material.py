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

def create_bsdf_material(context, material, texture_set=None):
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

	# Override default Material parameters
	if context.scene.lm_override_material_color:
		shader.inputs[0].default_value = (context.scene.lm_default_material_color[0], context.scene.lm_default_material_color[1], context.scene.lm_default_material_color[2], 1)
	if context.scene.lm_override_material_roughness:
		shader.inputs[7].default_value = context.scene.lm_default_material_roughness

	location = (location[0] - incr - 400, location[1])

	tree.links.new(shader.outputs[0], output.inputs[0])
	
	if texture_set is not None:
		for channel, input_idx in input_indices.items():
			try:
				t = texture_set[channel]['file']
			except KeyError as k:
				print('No texture found for channel "{}" in the material "{}".'.format(channel, material.name))
				continue
			
			if t is None:
				continue

			dir_name = os.path.dirname(t)
			file_name = os.path.basename(t)

			texture = nodes.new('ShaderNodeTexImage')

			bpy.ops.image.open(filepath=t, directory=dir_name, show_multiview=False)
				
			texture.image = bpy.data.images[file_name]
			texture.label = os.path.splitext(file_name)[0]

			texture.location = location
			
			inverted = texture_set[channel]['inverted']

			if texture_set[channel]['normal_map']:
				normal_map = nodes.new('ShaderNodeNormalMap')
				normal_map.location = (location[0] + incr, location[1])

				if inverted:
					combine = nodes.new('ShaderNodeCombineRGB')
					combine.location = location
					location = (location[0] - incr/2, location[1])

					invert = nodes.new('ShaderNodeInvert')
					invert.location = location
					location = (location[0] - incr/2, location[1])

					separate = nodes.new('ShaderNodeSeparateRGB')
					separate.location = location
					location = (location[0] - incr, location[1])

					texture.location = location

					tree.links.new(texture.outputs[0], separate.inputs[0])

					tree.links.new(separate.outputs[0], combine.inputs[0])
					tree.links.new(separate.outputs[1], invert.inputs[1])
					tree.links.new(separate.outputs[2], combine.inputs[2])

					tree.links.new(invert.outputs[0], combine.inputs[1])

					
				texture.image.colorspace_settings.name = 'Linear'
				
				if inverted:
					tree.links.new(combine.outputs[0], normal_map.inputs[1])
				else:
					tree.links.new(texture.outputs[0], normal_map.inputs[1])

				tree.links.new(normal_map.outputs[0], shader.inputs[input_idx['index']])
			else:
				if texture_set[channel]['linear']:
					texture.image.colorspace_settings.name = 'Linear'
				
				if inverted:
					invert = nodes.new('ShaderNodeInvert')
					invert.location = location
					location = (location[0] - incr, location[1])

					tree.links.new(texture.outputs[0], invert.inputs[1])
					tree.links.new(invert.outputs[0], shader.inputs[input_idx['index']])
				else:
					tree.links.new(texture.outputs[0], shader.inputs[input_idx['index']])
		
			location = (location[0], location[1] - incr)
	return output