import bpy
import os, math, time
from os import path
from . import variables as V
from . import naming_convention as N
from . import helper as H
from PIL import Image, ImageDraw, ImageFont

class LM_Composite(object):
	def __init__(self, context):
		self.context = context

		self.asset_count = len(self.context.scene.lm_asset_list)

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

		self.curr_page = 0
		self.pages = {}
	
	def composite_pdf_summary(self, pdf):
		# pdf.add_page()
		print('Lineup Maker : Compositing Summary')
		pdf.add_font(family='UbuntuMono-Bold', style='', fname=self.font_file, uni=True)
		pdf.set_font('UbuntuMono-Bold', size=self.font_size_title)
		pdf.set_text_color(r=self.text_color[0], g=self.text_color[1], b=self.text_color[2])
		pdf.set_fill_color(r=0)

		pdf.rect(x=0, y=0, w=self.res[0], h=self.res[1], style='F')

		pdf.set_font_size(self.font_size_paragraph)
		# Page
		text = '{}'.format(pdf.page_no())
		position = (self.res[0] - self.character_size_paragraph[0] * len(text) - self.character_size_paragraph[0], self.res[1] - self.character_size_paragraph[1]/2)
		pdf.text(x=position[0], y=position[1], txt=text)

		pdf.set_font_size(self.font_size_title)

		initial_pos = (self.character_size_title[0], self.character_size_title[1])

		for i,asset in enumerate(self.context.scene.lm_asset_list):
			# Asset Name
			text = asset.name
			column = (self.character_size_title[1] * i) % self.res[1]
			position = self.add_position(initial_pos, (0 if (self.character_size_title[1] * i) < self.res[1] else int(self.res[0]/2), column))
			pdf.text(x=position[0], y=position[1], txt=text)
			pdf.link(x=position[0], y=position[1] - self.character_size_title[1], w=len(text)*self.character_size_title[0], h=self.character_size_title[1], link=self.pages[asset.name][0])
	
	def composite_pdf_chapter(self, pdf, chapter_name):
		print('Lineup Maker : Compositing pdf chapter "{}"'.format(chapter_name))
		pdf.add_font(family='UbuntuMono-Bold', style='', fname=self.font_file, uni=True)
		pdf.set_font('UbuntuMono-Bold', size=self.font_size_chapter)
		pdf.set_text_color(r=self.text_color[0], g=self.text_color[1], b=self.text_color[2])
		pdf.set_fill_color(r=0)

		pdf.rect(x=0, y=0, w=self.res[0], h=self.res[1], style='F')

		# Chapter Name
		text = chapter_name
		position = (int(math.ceil(self.res[0]/2)) - self.character_size_chapter[0] * math.ceil(len(text)/2), int(math.ceil(self.res[1]/2)) - self.character_size_chapter[1]/2)
		pdf.text(x=position[0], y=position[1], txt=text)

		pdf.set_font_size(self.font_size_paragraph)
		# Page
		text = '{}'.format(pdf.page_no())
		position = (self.res[0] - self.character_size_paragraph[0] * len(text) - self.character_size_paragraph[0], self.res[1] - self.character_size_paragraph[1]/2)
		pdf.text(x=position[0], y=position[1], txt=text)

		page_link = pdf.add_link()
		self.pages[chapter_name] = [page_link, pdf.page_no()]
		pdf.set_link(self.pages[chapter_name][0], self.pages[chapter_name][1])

	def composite_chapter(self):
		if self.asset.final_composite_filepath != '':
			naming_convention = N.NamingConvention(self.context, self.asset.name, self.context.scene.lm_asset_naming_convention).naming_convention
			chapter_name = naming_convention[self.context.scene.lm_chapter_naming_convention]

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

	def convert_to_jpeg(self, file, output, quality):
		image = Image.open(file)

		converted = Image.new("RGB", image.size, (255, 255, 255))
		converted.paste(image, mask=image.split()[3])
		converted.save(output, "JPEG", quality=quality)

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


class LM_Composite_Image(LM_Composite):
	def __init__(self, context, index=0):
		super(LM_Composite_Image, self).__init__(context)
		self.index = index
		self.output = None


	def build_composite_nodegraph(self, name):
		print('Lineup Maker : Generating composite nodegraph')
		tree = self.context.scene.node_tree
		nodes = tree.nodes

		location = (600, - 1000 * self.index)
		incr = 300

		render_res = (bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y)
		framecount = self.get_current_frame_range()

		composite_image = bpy.data.images.new(name='{}_composite'.format(name), width=self.res[0], height=self.res[1])
		composite_image.generated_color = (0.1, 0.1, 0.1, 1)
		
		composite = nodes.new('CompositorNodeImage')
		composite.location = (location[0], location[1])
		composite.image = composite_image
		location = (location[0], location[1] - incr)

		mix = None

		files = os.listdir(self.context.scene.lm_asset_list[name].render_path)

		for i,f in enumerate(files):
			image = nodes.new('CompositorNodeImage')
			bpy.ops.image.open(filepath=os.path.join(self.context.scene.lm_asset_list[name].render_path, f), directory=self.context.scene.lm_asset_list[name].render_path, show_multiview=False)
			image.image = bpy.data.images[f]
			image.location = location

			location = (location[0] + incr/2, location[1])
			translate = nodes.new('CompositorNodeTranslate')
			translate.location = location
			translate.inputs[1].default_value = -self.res[0]/2 + render_res[0] / 2 + ((i%(framecount/2)) * render_res[0])
			translate.inputs[2].default_value = self.res[1]/2 - render_res[1] / 2 - self.res[2] + self.character_size_paragraph[1] * 2 - (math.floor(i/framecount*2) * render_res[1])

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

		composite_name = name + '_raw_composite_'
		composite_path = path.join(self.context.scene.lm_render_path, '00_Raw_Composite')
		
		H.create_folder_if_neeed(composite_path)

		out.file_slots[0].path = composite_name
		out.base_path = composite_path
		# out.format.compression = 0

		self.context.scene.lm_asset_list[name].raw_composite_filepath = os.path.join(composite_path, composite_name + str(self.context.scene.frame_current).zfill(4) + self.get_output_node_extention(out))

		if mix:
			tree.links.new(mix.outputs[0], out.inputs[0])

		location = (location[0], location[1] - 100)
		
		self.context.scene.lm_asset_list[name].rendered = False
		
		self.output = out

		return out

	def composite_asset_info(self, name):
		if self.context.scene.lm_asset_list[name].raw_composite_filepath != '':
			print('Lineup Maker : Compositing asset info for "{}"'.format(name))
			image = Image.open(self.context.scene.lm_asset_list[name].raw_composite_filepath)

			draw = ImageDraw.Draw(image)
			draw.rectangle(xy=[0, 0, self.res[0], self.res[2] - self.character_size_paragraph[1]], fill='black')

			draw.rectangle(xy=[0, self.res[1], self.res[0], self.res[1] - self.character_size_paragraph[1]], fill='black')

			# Asset Name
			text = name
			position = (int(math.ceil(self.res[0]/2)) - self.character_size_title[0] * math.ceil(len(text)/2), 0)
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_title, align='center')

			# WIP
			text = 'WIP'
			if self.context.scene.lm_asset_list[name].wip:
				position = (int(math.ceil(self.res[0]/2)) - self.character_size_title[0] * math.ceil(len(text)/2), self.character_size_title[1])
				draw.text(xy=position, text=text, fill=self.text_color, font=self.font_title, align='center')
			
			# Geometry_Info : Triangles
			text = 'Triangle Count : {}'.format(self.context.scene.lm_asset_list[name].triangles)
			position = (self.character_size_paragraph[0], self.character_size_paragraph[1])
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='center')

			# Geometry_Info : Vertices
			text = 'Vertices Count : {}'.format(self.context.scene.lm_asset_list[name].vertices)
			position = self.add_position(position, (0, self.character_size_paragraph[1]))
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='center')

			# Geometry_Info : Has UV2
			text = 'UV2 : {}'.format(self.context.scene.lm_asset_list[name].has_uv2)
			position = self.add_position(position, (0, self.character_size_paragraph[1]))
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='center')

			initial_pos = (self.res[0], self.character_size_paragraph[1])
			# texture_Info : Normal map
			for i, texture in enumerate(self.context.scene.lm_asset_list[name].texture_list):
				text = '{} : {}'.format(texture.channel, texture.file_path)
				position = self.add_position(initial_pos, (-len(text) * self.character_size_paragraph[0], self.character_size_paragraph[1] * i))
				draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='right')

			# Updated date
			text = 'Updated : {}'.format(time.ctime(self.context.scene.lm_asset_list[name].import_date))
			position = (0, self.res[1] - self.character_size_paragraph[1])
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='left')

			# Render date
			text = 'Rendered : {}'.format(time.ctime(self.context.scene.lm_asset_list[name].render_date))
			position = (self.res[0]/2 - len(text) * self.character_size_paragraph[0] / 2, self.res[1] - self.character_size_paragraph[1])
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='left')

			# Page
			text = '{}'.format(self.context.scene.lm_asset_list[name].asset_number)
			position = (self.res[0] - self.character_size_paragraph[0] * len(text) - self.character_size_paragraph[0], self.res[1] - self.character_size_paragraph[1])
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='right')

			self.context.scene.lm_asset_list[name].final_composite_filepath = path.join(self.context.scene.lm_render_path, '01_Final_Composite')
			H.create_folder_if_neeed(self.context.scene.lm_asset_list[name].final_composite_filepath)
			self.context.scene.lm_asset_list[name].final_composite_filepath = path.join(self.context.scene.lm_asset_list[name].final_composite_filepath, self.context.scene.lm_asset_list[name].name + '_final_composite.jpg')

			converted = Image.new("RGB", image.size, (255, 255, 255))
			converted.paste(image, mask=image.split()[3])
			converted.save(self.context.scene.lm_asset_list[name].final_composite_filepath, "JPEG", quality=80)

	def composite_pdf_asset_info(self, pdf, name):
		print('Lineup Maker : Compositing pdf asset info for "{}"'.format(name))
		pdf.add_font(family='UbuntuMono-Bold', style='', fname=self.font_file, uni=True)
		pdf.set_font('UbuntuMono-Bold', size=self.font_size_title)
		pdf.set_text_color(r=self.text_color[0], g=self.text_color[1], b=self.text_color[2])
		pdf.set_fill_color(r=0)

		pdf.rect(x=0, y=0, w=self.res[0], h=self.res[2] - self.character_size_paragraph[1], style='F')
		pdf.rect(x=0, y=self.res[1] - self.character_size_paragraph[1]*1.5, w=self.res[0], h=self.res[1], style='F')

		# Asset Name
		text = name
		position = (int(math.ceil(self.res[0]/2)) - self.character_size_title[0] * math.ceil(len(text)/2), self.character_size_title[1])
		pdf.text(x=position[0], y=position[1], txt=text)

		# WIP
		text = 'WIP'
		if self.context.scene.lm_asset_list[name].wip:
			pdf.set_text_color(r=200, g=50, b=0)
			position = (int(math.ceil(self.res[0]/2)) - self.character_size_title[0] * math.ceil(len(text)/2), self.character_size_title[1] * 2)
			pdf.text(x=position[0], y=position[1], txt=text)
			pdf.set_text_color(r=self.text_color[0], g=self.text_color[1], b=self.text_color[2])

		pdf.set_font_size(self.font_size_paragraph)

		# Geometry_Info : Triangles
		text = 'Triangle Count : {}'.format(self.context.scene.lm_asset_list[name].triangles)
		position = (self.character_size_paragraph[0], self.character_size_paragraph[1])
		pdf.text(x=position[0], y=position[1], txt=text)

		# Geometry_Info : Vertices
		text = 'Vertices Count : {}'.format(self.context.scene.lm_asset_list[name].vertices)
		position = self.add_position(position, (0, self.character_size_paragraph[1]))
		pdf.text(x=position[0], y=position[1], txt=text)

		# Geometry_Info : Has UV2
		text = 'UV2 : {}'.format(self.context.scene.lm_asset_list[name].has_uv2)
		position = self.add_position(position, (0, self.character_size_paragraph[1]))
		pdf.text(x=position[0], y=position[1], txt=text)

		# Geometry_Info : asset number
		text = 'Asset Number : {} / {}'.format(self.context.scene.lm_asset_list[name].asset_number, self.asset_count)
		position = self.add_position(position, (0, self.character_size_paragraph[1]))
		pdf.text(x=position[0], y=position[1], txt=text)

		initial_pos = (self.res[0] - self.character_size_paragraph[0], self.character_size_paragraph[1])
		# texture_Info : Normal map
		for i, texture in enumerate(self.context.scene.lm_asset_list[name].texture_list):
			text = '{} : {}'.format(texture.channel, texture.file_path)
			position = self.add_position(initial_pos, (-len(text) * self.character_size_paragraph[0], self.character_size_paragraph[1] * i))
			pdf.text(x=position[0], y=position[1], txt=text)

		# Updated date
		text = 'Updated : {}'.format(time.ctime(self.context.scene.lm_asset_list[name].import_date))
		position = (self.character_size_paragraph[0], self.res[1] - self.character_size_paragraph[1]/2)
		pdf.text(x=position[0], y=position[1], txt=text)

		# Render date
		text = 'Rendered : {}'.format(time.ctime(self.context.scene.lm_asset_list[name].render_date))
		position = (self.res[0]/2 - len(text) * self.character_size_paragraph[0] / 2, self.res[1] - self.character_size_paragraph[1]/2)
		pdf.text(x=position[0], y=position[1], txt=text)

		# Page
		text = '{}'.format(pdf.page_no())
		position = (self.res[0] - self.character_size_paragraph[0] * len(text) - self.character_size_paragraph[0], self.res[1] - self.character_size_paragraph[1]/2)
		pdf.text(x=position[0], y=position[1], txt=text)

		page_link = pdf.add_link()
		self.pages[name] = [page_link, pdf.page_no()]
		pdf.set_link(self.pages[name][0], self.pages[name][1])
		