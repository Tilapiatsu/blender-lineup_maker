import bpy
import os, math, time
from os import path
from . import variables as V
from . import naming_convention as N
from . import helper as H
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF

class LM_Composite_Image(object):
	def __init__(self, context, asset, index=0):
		self.context = context
		self.asset = asset
		self.index = index
		self._output = None

		self.res = self.get_composite_resolution()

		self.text_color = (int(self.context.scene.lm_font_color[0] * 255), int(self.context.scene.lm_font_color[1] * 255), int(self.context.scene.lm_font_color[2] * 255))

		self.font_size_chapter = int(math.floor(self.res[0]*100/self.res[1]))
		self.character_size_chapter = (math.ceil(self.font_size_chapter/2), self.font_size_chapter)
		self.font_size_title = int(math.floor(self.res[0]*50/self.res[1]))
		self.character_size_title = (math.ceil(self.font_size_title/2), self.font_size_title)
		self.font_size_paragraph = int(math.floor(self.res[0]*25/self.res[1]))
		self.character_size_paragraph = (math.ceil(self.font_size_paragraph/2), self.font_size_paragraph)

		self.font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Fonts')
		self.font_file = os.path.join(self.font_path, 'UbuntuMono-Bold.ttf')
		self.font_chapter = ImageFont.truetype(self.font_file, size=self.font_size_chapter)
		self.font_title = ImageFont.truetype(self.font_file, size=self.font_size_title)
		self.font_paragraph = ImageFont.truetype(self.font_file, size=self.font_size_paragraph)

		self.pdf = fpdf()

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

		render_res = (bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y)
		framecount = self.get_current_frame_range()

		composite_image = bpy.data.images.new(name='{}_composite'.format(self.asset.name), width=self.res[0], height=self.res[1])
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
			translate.inputs[1].default_value = -self.res[0]/2 + render_res[0] / 2 + ((i%(framecount/2)) * render_res[0])
			translate.inputs[2].default_value = self.res[1]/2 - render_res[1] / 2 - self.res[2] + self.character_size_paragraph[1] - (math.floor(i/framecount*2) * render_res[1])

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

		composite_name = self.asset.name + '_raw_composite_'
		composite_path = path.join(self.context.scene.lm_render_path, '00_Raw_Composite')
		
		H.create_folder_if_neeed(composite_path)

		out.file_slots[0].path = composite_name
		out.base_path = composite_path
		# out.format.compression = 0

		self.asset.raw_composite_filepath = os.path.join(composite_path, composite_name + str(self.context.scene.frame_current).zfill(4) + self.get_output_node_extention(out))

		if mix:
			tree.links.new(mix.outputs[0], out.inputs[0])

		location = (location[0], location[1] - 100)
		
		self.asset.rendered = False
		
		return out

	def composite_asset_info(self):
		if self.asset.raw_composite_filepath != '':
			print('Lineup Maker : Compositing asset info for "{}"'.format(self.asset.name))
			image = Image.open(self.asset.raw_composite_filepath)

			draw = ImageDraw.Draw(image)
			draw.rectangle(xy=[0, 0, self.res[0], self.res[2] - self.character_size_paragraph[1]], fill='black')

			draw.rectangle(xy=[0, self.res[1], self.res[0], self.res[1] - self.character_size_paragraph[1]], fill='black')

			# Asset Name
			text = self.asset.name
			position = (int(math.ceil(self.res[0]/2)) - self.character_size_title[0] * math.ceil(len(text)/2), 0)
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_title, align='center')

			# WIP
			text = 'WIP'
			if self.asset.wip:
				position = (int(math.ceil(self.res[0]/2)) - self.character_size_title[0] * math.ceil(len(text)/2), self.character_size_title[1])
				draw.text(xy=position, text=text, fill=self.text_color, font=self.font_title, align='center')
			
			# Geometry_Info : Triangles
			text = 'Triangle Count : {}'.format(self.asset.triangles)
			position = (self.character_size_paragraph[0], self.character_size_paragraph[1])
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='center')

			# Geometry_Info : Vertices
			text = 'Vertices Count : {}'.format(self.asset.vertices)
			position = self.add_position(position, (0, self.character_size_paragraph[1]))
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='center')

			# Geometry_Info : Has UV2
			text = 'UV2 : {}'.format(self.asset.has_uv2)
			position = self.add_position(position, (0, self.character_size_paragraph[1]))
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='center')

			initial_pos = (self.res[0], self.character_size_paragraph[1])
			# texture_Info : Normal map
			for i, texture in enumerate(self.asset.texture_list):
				text = '{} : {}'.format(texture.channel, texture.file_path)
				position = self.add_position(initial_pos, (-len(text) * self.character_size_paragraph[0], self.character_size_paragraph[1] * i))
				draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='right')

			# Updated date
			text = 'Updated : {}'.format(time.ctime(self.asset.import_date))
			position = (0, self.res[1] - self.character_size_paragraph[1])
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='left')

			# Render date
			text = 'Rendered : {}'.format(time.ctime(self.asset.render_date))
			position = (self.res[0]/2 - len(text) * self.character_size_paragraph[0] / 2, self.res[1] - self.character_size_paragraph[1])
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='left')

			# Page
			text = '{}'.format(self.asset.asset_number)
			position = (self.res[0] - self.character_size_paragraph[0] * len(text) - self.character_size_paragraph[0], self.res[1] - self.character_size_paragraph[1])
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='right')

			self.asset.final_composite_filepath = path.join(self.context.scene.lm_render_path, '01_Final_Composite')
			H.create_folder_if_neeed(self.asset.final_composite_filepath)
			self.asset.final_composite_filepath = path.join(self.asset.final_composite_filepath, self.asset.name + '_final_composite.jpg')

			converted = Image.new("RGB", image.size, (255, 255, 255))
			converted.paste(image, mask=image.split()[3])
			converted.save(self.asset.final_composite_filepath, "JPEG", quality=80)

	def composite_pdf_asset_info(self, pdf):
		if self.asset.raw_composite_filepath != '':
			print('Lineup Maker : Compositing pdf asset info for "{}"'.format(self.asset.name))
			pdf.set_font(self.font_file, size=self.font_size_title)

			draw = ImageDraw.Draw(image)
			draw.rectangle(xy=[0, 0, self.res[0], self.res[2] - self.character_size_paragraph[1]], fill='black')

			draw.rectangle(xy=[0, self.res[1], self.res[0], self.res[1] - self.character_size_paragraph[1]], fill='black')

			# Asset Name
			text = self.asset.name
			position = (int(math.ceil(self.res[0]/2)) - self.character_size_title[0] * math.ceil(len(text)/2), 0)
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_title, align='center')

			# WIP
			text = 'WIP'
			if self.asset.wip:
				position = (int(math.ceil(self.res[0]/2)) - self.character_size_title[0] * math.ceil(len(text)/2), self.character_size_title[1])
				draw.text(xy=position, text=text, fill=self.text_color, font=self.font_title, align='center')
			
			# Geometry_Info : Triangles
			text = 'Triangle Count : {}'.format(self.asset.triangles)
			position = (self.character_size_paragraph[0], self.character_size_paragraph[1])
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='center')

			# Geometry_Info : Vertices
			text = 'Vertices Count : {}'.format(self.asset.vertices)
			position = self.add_position(position, (0, self.character_size_paragraph[1]))
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='center')

			# Geometry_Info : Has UV2
			text = 'UV2 : {}'.format(self.asset.has_uv2)
			position = self.add_position(position, (0, self.character_size_paragraph[1]))
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='center')

			initial_pos = (self.res[0], self.character_size_paragraph[1])
			# texture_Info : Normal map
			for i, texture in enumerate(self.asset.texture_list):
				text = '{} : {}'.format(texture.channel, texture.file_path)
				position = self.add_position(initial_pos, (-len(text) * self.character_size_paragraph[0], self.character_size_paragraph[1] * i))
				draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='right')

			# Updated date
			text = 'Updated : {}'.format(time.ctime(self.asset.import_date))
			position = (0, self.res[1] - self.character_size_paragraph[1])
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='left')

			# Render date
			text = 'Rendered : {}'.format(time.ctime(self.asset.render_date))
			position = (self.res[0]/2 - len(text) * self.character_size_paragraph[0] / 2, self.res[1] - self.character_size_paragraph[1])
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='left')

			# Page
			text = '{}'.format(self.asset.asset_number)
			position = (self.res[0] - self.character_size_paragraph[0] * len(text) - self.character_size_paragraph[0], self.res[1] - self.character_size_paragraph[1])
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='right')

			self.asset.final_composite_filepath = path.join(self.context.scene.lm_render_path, '01_Final_Composite')
			H.create_folder_if_neeed(self.asset.final_composite_filepath)
			self.asset.final_composite_filepath = path.join(self.asset.final_composite_filepath, self.asset.name + '_final_composite.jpg')

			converted = Image.new("RGB", image.size, (255, 255, 255))
			converted.paste(image, mask=image.split()[3])
			converted.save(self.asset.final_composite_filepath, "JPEG", quality=80)

	def composite_chapter(self):
		if self.asset.final_composite_filepath != '':
			naming_convention = N.NamingConvention(self.context, self.asset.name, self.context.scene.lm_asset_naming_convention).naming_convention
			chapter_name = naming_convention[self.context.scene.lm_chapter_name]

			print('Lineup Maker : Compositing chapter "{}"'.format(chapter_name))
			image = Image.new('RGB', (self.res[0], self.res[1]))

			draw = ImageDraw.Draw(image)
			draw.rectangle(xy=[0, 0, self.res[0], self.res[2] * 2], fill='black')
			draw.rectangle(xy=[0, self.res[1] - self.res[2] * 2, self.res[0], self.res[1]], fill='black')


			# Chapter Name
			text = chapter_name.upper()
			position = (int(math.ceil(self.res[0]/2)) - self.character_size_chapter[0] * math.ceil(len(text)/2), int(math.ceil(self.res[1]/2)) - math.ceil(self.character_size_chapter[1]/2))
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_chapter, align='center')

			filename = 'MAD_CHR_' + chapter_name + '_Chapter.jpg'
			filepath = path.join(path.dirname(self.asset.final_composite_filepath), filename)
			H.create_folder_if_neeed(path.dirname(self.asset.final_composite_filepath))

			converted = Image.new("RGB", image.size, (255, 255, 255))
			converted.paste(image)
			converted.save(filepath, "JPEG", quality=80)


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

	def add_position(self, p1, p2):
		return (p1[0] + p2[0], p1[1] + p2[1])