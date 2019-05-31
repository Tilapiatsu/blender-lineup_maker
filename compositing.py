import bpy
import os, math
from os import path
from . import variables as V
from PIL import Image, ImageDraw, ImageFont

class LM_Composite_Image(object):
	def __init__(self, context, asset, index=0):
		self.context = context
		self.asset = asset
		self.index = index
		self._output = None

	@property
	def output(self):
		if self._output is None:
			self._output = self.build_composite_nodegraph()
		
		return self._output

	def build_composite_nodegraph(self):
		print('Lineup Maker : Generating composite nodegraph')
		tree = self.context.scene.node_tree
		nodes = tree.nodes

		location = (600, - 1000 * self.index)
		incr = 300

		composite_res = self.get_composite_resolution()
		render_res = (bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y)
		framecount = self.get_current_frame_range()

		composite_image = bpy.data.images.new(name='{}_composite'.format(self.asset.name), width=composite_res[0], height=composite_res[1])
		composite_image.generated_color = (0.1, 0.1, 0.1, 1)
		
		composite = nodes.new('CompositorNodeImage')
		composite.location = (location[0], location[1])
		composite.image = composite_image
		location = (location[0], location[1] - incr)

		mix = None

		files = os.listdir(self.asset.render_path)

		for i,f in enumerate(files):
			image = nodes.new('CompositorNodeImage')
			bpy.ops.image.open(filepath=os.path.join(self.asset.render_path, f), directory=self.asset.render_path, show_multiview=False)
			image.image = bpy.data.images[f]
			image.location = location

			location = (location[0] + incr/2, location[1])
			translate = nodes.new('CompositorNodeTranslate')
			translate.location = location
			translate.inputs[1].default_value = -composite_res[0]/2 + render_res[0] / 2 + ((i%(framecount/2)) * render_res[0])
			translate.inputs[2].default_value = composite_res[1]/2 - render_res[1] / 2 - composite_res[2] - (math.floor(i/framecount*2) * render_res[1])

			tree.links.new(image.outputs[0], translate.inputs[0])

			new_mix = nodes.new('CompositorNodeAlphaOver')
			new_mix.location = (location[0] + incr/2, location[1])
			new_mix.use_premultiply = True

			if mix is not None:
				tree.links.new(mix.outputs[0], new_mix.inputs[1])
				tree.links.new(translate.outputs[0], new_mix.inputs[2])
			else:
				tree.links.new(translate.outputs[0], new_mix.inputs[2])
				tree.links.new(composite.outputs[0], new_mix.inputs[1])

			location = (location[0] + incr, location[1] - incr)

			mix = new_mix
		
		out = nodes.new('CompositorNodeOutputFile')
		out.location = (location[0] + incr, location[1])

		composite_name = self.asset.name + '_composite_'
		composite_path = path.abspath(path.join(self.asset.render_path, os.pardir))

		out.file_slots[0].path = composite_name
		out.base_path = composite_path

		self.asset.composite_filepath = os.path.join(composite_path, composite_name + str(self.context.scene.frame_current).zfill(4) + self.get_output_node_extention(out))

		if mix:
			tree.links.new(mix.outputs[0], out.inputs[0])

		location = (location[0], location[1] - 100)
		
		self.asset.rendered = False
		
		return out

	def composite_asset_info(self):
		if self.asset.composite_filepath != '':
			print('Lineup Maker : Compositing asset info for "{}"'.format(self.asset.name))
			res = self.get_composite_resolution()
			text_color = self.context.scene.lm_font_color
			image = Image.open(self.asset.composite_filepath)
			font_size = int(math.floor(res[0]*50/res[1]))
			character_size = (math.ceil(font_size/2), font_size)
			font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Fonts')
			font_file = os.path.join(font_path, 'UbuntuMono-Bold.ttf')
			font_title = ImageFont.truetype(font_file, size=font_size)

			draw = ImageDraw.Draw(image)
			position = (int(math.ceil(res[0]/2)) - character_size[0] * math.ceil(len(self.asset.name)/2), int(math.ceil(res[2]/3 - character_size[1]/2)))
			draw.text(xy=position, text=self.asset.name, fill=(int(text_color[0] * 255), int(text_color[1] * 255), int(text_color[2] * 255)), font=font_title, align='center')

			image.save(self.asset.composite_filepath, "PNG")

	def get_output_node_extention(self, output_node):
		return V.LM_OUTPUT_EXTENSION[output_node.format.file_format]

	def get_composite_resolution(self):
		fc = self.context.scene.frame_end - self.context.scene.frame_start
		res_x = bpy.context.scene.render.resolution_x
		res_y = bpy.context.scene.render.resolution_y
		margin = math.ceil(res_y/3)

		x = math.ceil(fc/2) * res_x
		y = math.floor(fc/2) * res_y + margin

		return (x, y, margin)

	def get_current_frame_range(self):
		return self.context.scene.frame_end + 1 - self.context.scene.frame_start
