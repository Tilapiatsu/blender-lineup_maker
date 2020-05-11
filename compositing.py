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

		self.framecount = H.get_current_frame_range(context)

		self.composite_res = self.get_composite_resolution()
		self.render_res = self.get_render_resolution()

		self.text_color = (self.to_srgb(self.context.scene.lm_font_color[0]), self.to_srgb(self.context.scene.lm_font_color[1]), self.to_srgb(self.context.scene.lm_font_color[2]), 255)
		self.text_summary_color = self.color_multiply(self.text_color, 0.6)
		self.text_background_color = (self.to_srgb(self.context.scene.lm_text_background_color[0]), self.to_srgb(self.context.scene.lm_text_background_color[1]), self.to_srgb(self.context.scene.lm_text_background_color[2]), 255)
		self.content_background_color = (self.to_srgb(self.context.scene.lm_content_background_color[0]), self.to_srgb(self.context.scene.lm_content_background_color[1]), self.to_srgb(self.context.scene.lm_content_background_color[2]), 255)

		self.font_size_chapter = int(math.floor(self.composite_res[0]*100/self.composite_res[1]))
		self.character_size_chapter = (math.ceil(self.font_size_chapter/2), self.font_size_chapter)
		self.font_size_title = int(math.floor(self.composite_res[0]*45/self.composite_res[1]))
		self.character_size_title = (math.ceil(self.font_size_title/2), self.font_size_title)
		self.font_size_paragraph = int(math.floor(self.composite_res[0]*25/self.composite_res[1]))
		self.character_size_paragraph = (math.ceil(self.font_size_paragraph/2), self.font_size_paragraph)
		self.font_size_texture = int(math.floor(self.composite_res[0]*20/self.composite_res[1]))
		self.character_size_texture = (math.ceil(self.font_size_texture/2), self.font_size_texture)

		self.font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Fonts')
		self.font_file = os.path.join(self.font_path, 'UbuntuMono-Bold.ttf')
		self.font_chapter = ImageFont.truetype(self.font_file, size=self.font_size_chapter)
		self.font_title = ImageFont.truetype(self.font_file, size=self.font_size_title)
		self.font_paragraph = ImageFont.truetype(self.font_file, size=self.font_size_paragraph)

		self.chapter = ''

		self.curr_page = 0
		self.pages = {}

		self._max_item_per_toc_page = None
	
	@property
	def max_item_per_toc_page(self):
		if self._max_item_per_toc_page is None:
			self._max_item_per_toc_page = self.get_max_item_per_toc_page()
		
		return self._max_item_per_toc_page

	def create_empty_toc_pages(self, pdf):
		toc_page_count = self.get_toc_page_count()

		for i in range(toc_page_count):
			pdf.add_page()
			page_link = pdf.add_link()
			toc_name = 'toc_{}'.format(str(i+1).zfill(2))
			self.pages[toc_name] = [page_link, pdf.page_no()]
			self.curr_page += 1

	def write_pdf_page_number(self, pdf):
		pdf.set_font_size(self.font_size_paragraph)
		# Page
		text = '{}'.format(pdf.page_no())
		position = (self.composite_res[0] - self.character_size_paragraph[0] * len(text) - self.character_size_paragraph[0], self.composite_res[1] - self.character_size_paragraph[1]/2)
		pdf.text(x=position[0], y=position[1], txt=text)

	def composite_pdf_toc(self, pdf):
		print('Lineup Maker : Compositing Summary')
		pdf.add_font(family='UbuntuMono-Bold', style='', fname=self.font_file, uni=True)
		pdf.set_font('UbuntuMono-Bold', size=self.font_size_title)
		pdf.set_text_color(r=self.text_color[0], g=self.text_color[1], b=self.text_color[2])
		pdf.set_fill_color(r=self.text_background_color[0], g=self.text_background_color[1], b=self.text_background_color[2])

		pdf.rect(x=0, y=0, w=self.composite_res[0], h=self.composite_res[1], style='F')

		self.write_pdf_page_number(pdf)

		pdf.set_font_size(self.font_size_title)

		initial_pos = (self.character_size_title[0], self.character_size_title[1])

		asset_name_list = [a.name for a in self.context.scene.lm_asset_list if a.rendered]
		asset_name_list.sort()
		
		i = 0
		for asset in asset_name_list:
			chapter_naming_convention = N.NamingConvention(self.context, self.chapter, self.context.scene.lm_chapter_naming_convention)
			asset_naming_convention = N.NamingConvention(self.context, asset, self.context.scene.lm_asset_naming_convention)

			new_chapter = H.set_chapter(self, chapter_naming_convention, asset_naming_convention)

			pdf.set_text_color(r=self.text_color[0], g=self.text_color[1], b=self.text_color[2])

			# Change page if max_item_per_toc_page is reached
			if i > self.max_item_per_toc_page:
				pdf.page += 1
				pdf.rect(x=0, y=0, w=self.composite_res[0], h=self.composite_res[1], style='F')
				self.write_pdf_page_number(pdf)
				pdf.set_font_size(self.font_size_title)
				i = 0
			
			# Create a new chapter if needed
			if new_chapter:
				column = (self.character_size_title[1] * i) % (self.composite_res[1] - self.character_size_title[1])
				text = self.chapter
				position = self.add_position(initial_pos, (0 if (self.character_size_title[1] * i) < self.composite_res[1] - self.character_size_title[1] else int(self.composite_res[0]/2), column))
				pdf.text(x=position[0], y=position[1], txt=text)
				pdf.link(x=position[0], y=position[1] - self.character_size_title[1], w=len(text)*self.character_size_title[0], h=self.character_size_title[1], link=self.pages[self.chapter][0])
				i += 1
			
			pdf.set_text_color(r=self.text_summary_color[0], g=self.text_summary_color[1], b=self.text_summary_color[2])
			column = (self.character_size_title[1] * i) % (self.composite_res[1] - self.character_size_title[1])
			text = asset
			position = self.add_position(initial_pos, (100 if (self.character_size_title[1] * i) < self.composite_res[1] - self.character_size_title[1] else 100 + int(self.composite_res[0]/2), column))
			pdf.text(x=position[0], y=position[1], txt=text)
			pdf.link(x=position[0], y=position[1] - self.character_size_title[1], w=len(text)*self.character_size_title[0], h=self.character_size_title[1], link=self.pages[asset][0])
			i += 1
	
	def composite_pdf_chapter(self, pdf, chapter_name):
		print('Lineup Maker : Compositing pdf chapter "{}"'.format(chapter_name))
		pdf.add_font(family='UbuntuMono-Bold', style='', fname=self.font_file, uni=True)
		pdf.set_font('UbuntuMono-Bold', size=self.font_size_chapter)
		pdf.set_text_color(r=self.text_color[0], g=self.text_color[1], b=self.text_color[2])
		pdf.set_fill_color(r=self.text_background_color[0], g=self.text_background_color[1], b=self.text_background_color[2])

		pdf.rect(x=0, y=0, w=self.composite_res[0], h=self.composite_res[1], style='F')

		# Chapter Name
		text = chapter_name
		position = (int(math.ceil(self.composite_res[0]/2)) - self.character_size_chapter[0] * math.ceil(len(text)/2), int(math.ceil(self.composite_res[1]/2)) - self.character_size_chapter[1]/2)
		pdf.text(x=position[0], y=position[1], txt=text)

		self.write_pdf_page_number(pdf)

		page_link = pdf.add_link()
		self.pages[chapter_name] = [page_link, pdf.page_no()]
		pdf.set_link(self.pages[chapter_name][0], self.pages[chapter_name][1])

	def composite_chapter(self):
		if self.asset.final_composite_filepath != '':
			naming_convention = N.NamingConvention(self.context, self.asset.name, self.context.scene.lm_asset_naming_convention).naming_convention
			chapter_name = naming_convention[self.context.scene.lm_chapter_naming_convention]

			print('Lineup Maker : Compositing chapter "{}"'.format(chapter_name))
			image = Image.new('RGB', (self.composite_res[0], self.composite_res[1]))

			draw = ImageDraw.Draw(image)
			draw.rectangle(xy=[0, 0, self.composite_res[0], self.composite_res[2] * 2], fill=self.text_background_color)
			draw.rectangle(xy=[0, self.composite_res[1] - self.composite_res[2] * 2, self.composite_res[0], self.composite_res[1]], fill=self.text_background_color)


			# Chapter Name
			text = chapter_name.upper()
			position = (int(math.ceil(self.composite_res[0]/2)) - self.character_size_chapter[0] * math.ceil(len(text)/2), int(math.ceil(self.composite_res[1]/2)) - math.ceil(self.character_size_chapter[1]/2))
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
	
	def convert_png_to_8bit(self, file, output):
		image = Image.open(file)

		converted = Image.new("RGB", image.size, (255, 255, 255, 255))
		converted.paste(image, mask=image.split()[3])
		converted.save(output, "PNG", bits=8)

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

	def get_render_resolution(self):
		return (bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y)

	def get_max_item_per_toc_page(self):
		return (math.floor(self.composite_res[1] / self.character_size_title[1])- 1) * 2 - 1

	def get_toc_page_count(self):
		rendered_assets = [a for a in self.context.scene.lm_asset_list if a.rendered]
		asset_count = len(rendered_assets)
		chapter_count = 0
		for asset in rendered_assets:
			chapter_naming_convention = N.NamingConvention(self.context, self.chapter, self.context.scene.lm_chapter_naming_convention)
			asset_naming_convention = N.NamingConvention(self.context, asset.name, self.context.scene.lm_asset_naming_convention)

			new_chapter = H.set_chapter(self, chapter_naming_convention, asset_naming_convention)

			if new_chapter:
				chapter_count += 1

		max_item = self.max_item_per_toc_page

		if max_item:
			toc_page_count = math.ceil((asset_count + chapter_count) / max_item) - 1
		else:
			toc_page_count = 1
		
		return toc_page_count
	
	def add_position(self, p1, p2):
		return (p1[0] + p2[0], p1[1] + p2[1])

	def to_srgb(self, c):
		if c < 0.0031308:
			srgb = 0.0 if c < 0.0 else c * 12.92
		else:
			srgb = 1.055 * math.pow(c, 1.0 / 2.4) - 0.055

		return max(min(int(srgb * 255 + 0.5), 255), 0)

	def color_multiply(self, color, value):
		result = ()
		for c in color:
			result += (c*value,)
		return result

	def color_add(self, color, value):
		result = ()
		for c in color:
			result += (c+value,)
		return result

	def prettify_number(self, number, separator):
		n_str = str(number)

		n_reverse = list(reversed([n for n in n_str]))

		pretty_reverse = []

		for i,nn in enumerate(n_reverse):
			pretty_reverse.append(nn)
			
			if i%3 == 2:
				pretty_reverse.append(separator)

		pretty_regular = n_reverse = list(reversed(pretty_reverse))

		pretty_number = ''
		for nn in pretty_regular:
			pretty_number += nn
			
		return pretty_number

class LM_Composite_Image(LM_Composite):
	def __init__(self, context, index=0):
		super(LM_Composite_Image, self).__init__(context)
		self.index = index
		self.output = None

	def composite_asset(self, asset):
		print('Lineup Maker : Generating composite')

		composite_image = Image.new('RGBA', (self.composite_res[0], self.composite_res[1]), color=(self.content_background_color))

		if os.path.isdir(asset.render_path):
			files = [f for f in os.listdir(asset.render_path) if path.splitext(f)[1].lower() in V.LM_OUTPUT_EXTENSION.values()]
		else:
			files = []

		for i,f in enumerate(files):
			pos_x = int(((i%(self.framecount/2)) * self.render_res[0]))
			pos_y = int(self.composite_res[2] - self.character_size_paragraph[1] + (math.floor(i/self.framecount*2) * self.render_res[1]))

			offset = (pos_x, pos_y)

			render_filename = path.join(asset.render_path, f)

			image = Image.open(render_filename)
			composite_image.paste(image, offset, mask=image.split()[3])

		composite_name = asset.name + '{}.jpg'.format(V.LM_FINAL_COMPOSITE_SUFFIX)
		composite_path = path.join(self.context.scene.lm_render_path, V.LM_FINAL_COMPOSITE_FOLDER_NAME)

		H.create_folder_if_neeed(composite_path)
		
		composite_filepath = path.join(composite_path, composite_name)

		composite_image.convert('RGB').save(composite_filepath)
		self.context.scene.lm_asset_list[asset.name].final_composite_filepath = composite_filepath
		self.context.scene.lm_asset_list[asset.name].composited = True

	def build_composite_nodegraph(self, name):
		print('Lineup Maker : Generating composite nodegraph')
		tree = self.context.scene.node_tree
		nodes = tree.nodes

		location = (600, - 1000 * self.index)
		incr = 300

		self.render_res = (bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y)
		framecount = H.get_current_frame_range(self.context)

		composite_image = bpy.data.images.new(name='{}_composite'.format(name), width=self.composite_res[0], height=self.composite_res[1])
		composite_image.generated_color = (self.content_background_color[0]/255, self.content_background_color[1]/255, self.content_background_color[2]/255, 1)
		
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
			translate.inputs[1].default_value = -self.composite_res[0]/2 + self.render_res[0] / 2 + ((i%(framecount/2)) * self.render_res[0])
			translate.inputs[2].default_value = self.composite_res[1]/2 - self.render_res[1] / 2 - self.composite_res[2] + self.character_size_paragraph[1] * 2 - (math.floor(i/framecount*2) * self.render_res[1])

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
			draw.rectangle(xy=[0, 0, self.composite_res[0], self.composite_res[2] - self.character_size_paragraph[1]], fill=self.text_background_color)

			draw.rectangle(xy=[0, self.composite_res[1], self.composite_res[0], self.composite_res[1] - self.character_size_paragraph[1]], fill=self.text_background_color)

			# Asset Name
			text = name
			position = (int(math.ceil(self.composite_res[0]/2)) - self.character_size_title[0] * math.ceil(len(text)/2), 0)
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_title, align='center')

			# WIP
			text = 'WIP'
			if self.context.scene.lm_asset_list[name].wip:
				position = (int(math.ceil(self.composite_res[0]/2)) - self.character_size_title[0] * math.ceil(len(text)/2), self.character_size_title[1])
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

			initial_pos = (self.composite_res[0], self.character_size_paragraph[1])
			# texture_Info : Normal map
			for i, texture in enumerate(self.context.scene.lm_asset_list[name].texture_list):
				text = '{} : {}'.format(texture.channel, texture.file_path)
				position = self.add_position(initial_pos, (-len(text) * self.character_size_paragraph[0], self.character_size_paragraph[1] * i))
				draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='right')

			# Updated date
			text = 'Updated : {}'.format(time.ctime(self.context.scene.lm_asset_list[name].import_date))
			position = (0, self.composite_res[1] - self.character_size_paragraph[1])
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='left')

			# Render date
			text = 'Rendered : {}'.format(time.ctime(self.context.scene.lm_asset_list[name].render_date))
			position = (self.composite_res[0]/2 - len(text) * self.character_size_paragraph[0] / 2, self.composite_res[1] - self.character_size_paragraph[1])
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='left')

			# Page
			text = '{}'.format(self.context.scene.lm_asset_list[name].asset_number)
			position = (self.composite_res[0] - self.character_size_paragraph[0] * len(text) - self.character_size_paragraph[0], self.composite_res[1] - self.character_size_paragraph[1])
			draw.text(xy=position, text=text, fill=self.text_color, font=self.font_paragraph, align='right')

			self.context.scene.lm_asset_list[name].final_composite_filepath = path.join(self.context.scene.lm_render_path, '01_Final_Composite')
			H.create_folder_if_neeed(self.context.scene.lm_asset_list[name].final_composite_filepath)
			self.context.scene.lm_asset_list[name].final_composite_filepath = path.join(self.context.scene.lm_asset_list[name].final_composite_filepath, self.context.scene.lm_asset_list[name].name + '_final_composite.jpg')

			converted = Image.new("RGB", image.size, (255, 255, 255))
			converted.paste(image, mask=image.split()[3])
			converted.save(self.context.scene.lm_asset_list[name].final_composite_filepath, "JPEG", quality=80)

	def composite_pdf_asset_info(self, pdf, name):
		asset = self.context.scene.lm_asset_list[name]
		if asset.final_composite_filepath != '':
			print('Lineup Maker : Compositing pdf asset info for "{}"'.format(name))
			pdf.image(asset.final_composite_filepath, x=0, y=0, type='JPEG')

			pdf.add_font(family='UbuntuMono-Bold', style='', fname=self.font_file, uni=True)
			pdf.set_font('UbuntuMono-Bold', size=self.font_size_title)
			pdf.set_text_color(r=self.text_color[0], g=self.text_color[1], b=self.text_color[2])
			pdf.set_fill_color(r=self.text_background_color[0], g=self.text_background_color[1], b=self.text_background_color[2])

			pdf.rect(x=0, y=0, w=self.composite_res[0], h=self.composite_res[2] - self.character_size_paragraph[1], style='F')
			pdf.rect(x=0, y=self.composite_res[1] - self.character_size_paragraph[1]*1.5, w=self.composite_res[0], h=self.composite_res[1], style='F')

			# Asset Name
			text = name
			position = (int(math.ceil(self.composite_res[0]/2)) - self.character_size_title[0] * math.ceil(len(text)/2), self.character_size_title[1])
			pdf.text(x=position[0], y=position[1], txt=text)

			# AssetStatus
			hd_index = self.context.scene.lm_asset_list[name].hd_status
			ld_index = self.context.scene.lm_asset_list[name].ld_status
			baking_index = self.context.scene.lm_asset_list[name].baking_status

			hd_status = V.STATUS_DICT[str(hd_index)][1]
			ld_status = V.STATUS_DICT[str(ld_index)][1]
			baking_status = V.STATUS_DICT[str(baking_index)][1]


			hd_text = 'HD : '
			ld_text = '    LD : '
			baking_text = '    Baking : '


			hd = hd_text + hd_status
			ld = ld_text + ld_status
			baking = baking_text + baking_status

			text_length = len(hd) + len(ld) + len(baking)
			
			pdf.set_font_size(self.font_size_paragraph)

			self.set_status_color(pdf)
			position = (int(math.ceil(self.composite_res[0]/2)) - self.character_size_paragraph[0] * math.ceil(len(hd_text)), self.character_size_title[1]*1.2 + self.character_size_paragraph[1])
			pdf.text(x=position[0], y=position[1], txt=hd_text)

			self.set_status_color(pdf, hd_index)
			position = (int(math.ceil(self.composite_res[0]/2)), self.character_size_title[1]*1.2 + self.character_size_paragraph[1])
			pdf.text(x=position[0], y=position[1], txt=hd_status)

			self.set_status_color(pdf)
			position = (int(math.ceil(self.composite_res[0]/2)) - self.character_size_paragraph[0] * math.ceil(len(ld_text)), self.character_size_title[1]*1.2 + self.character_size_paragraph[1] * 2)
			pdf.text(x=position[0], y=position[1], txt=ld_text)

			self.set_status_color(pdf, ld_index)
			position = (int(math.ceil(self.composite_res[0]/2)), self.character_size_title[1]*1.2 + self.character_size_paragraph[1] * 2)
			pdf.text(x=position[0], y=position[1], txt=ld_status)

			self.set_status_color(pdf)
			position = (int(math.ceil(self.composite_res[0]/2)) - self.character_size_paragraph[0] * math.ceil(len(baking_text)), self.character_size_title[1]*1.2 + self.character_size_paragraph[1] * 3)
			pdf.text(x=position[0], y=position[1], txt=baking_text)

			self.set_status_color(pdf, baking_index)
			position = (int(math.ceil(self.composite_res[0]/2)), self.character_size_title[1]*1.2 + self.character_size_paragraph[1] * 3)
			pdf.text(x=position[0], y=position[1], txt=baking_status)

			pdf.set_text_color(r=self.text_color[0], g=self.text_color[1], b=self.text_color[2])

			pdf.set_font_size(self.font_size_paragraph)

			# Geometry_Info : Triangles
			text = 'Triangle Count : {}'.format(self.prettify_number(self.context.scene.lm_asset_list[name].triangles, ' '))
			position = (self.character_size_paragraph[0], self.character_size_paragraph[1])
			pdf.text(x=position[0], y=position[1], txt=text)

			# Geometry_Info : Vertices
			text = 'Vertices Count : {}'.format(self.prettify_number(self.context.scene.lm_asset_list[name].vertices, ' '))
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

			# Render_Info : Camera
			self.set_status_color(pdf, V.Status.NOT_SET.value)
			text = 'Render Camera : {}'.format(self.context.scene.lm_asset_list[name].render_camera)
			position = self.add_position(position, (0, self.character_size_paragraph[1]))
			pdf.text(x=position[0], y=position[1], txt=text)

			self.set_status_color(pdf)
			self.set_texture_text_size(name)
			pdf.set_font_size(self.font_size_texture)
			initial_pos = (self.composite_res[0] - self.character_size_texture[0], self.character_size_texture[1])
			i = 0
			for material in self.context.scene.lm_asset_list[name].material_list:
				if material.material:
					material_name = '{} - '.format(material.material.name)
				else:
					material_name = ' '
				
				textures = material.texture_list
				for texture in textures:
					filename = path.basename(texture.file_path)
					text = '{}{} : {}'.format(material_name, texture.channel, filename)
					position = self.add_position(initial_pos, (-len(text) * self.character_size_texture[0], self.character_size_texture[1] * i ))
					pdf.text(x=position[0], y=position[1], txt=text)
					material_name = ''
					i += 1

			pdf.set_font_size(self.font_size_paragraph)
			# Updated date
			text = 'Updated : {}'.format(time.ctime(self.context.scene.lm_asset_list[name].import_date))
			position = (self.character_size_paragraph[0], self.composite_res[1] - self.character_size_paragraph[1]/2)
			pdf.text(x=position[0], y=position[1], txt=text)

			# Render date
			text = 'Rendered : {}'.format(time.ctime(self.context.scene.lm_asset_list[name].render_date))
			position = (self.composite_res[0]/2 - len(text) * self.character_size_paragraph[0] / 2, self.composite_res[1] - self.character_size_paragraph[1]/2)
			pdf.text(x=position[0], y=position[1], txt=text)

			self.write_pdf_page_number(pdf)

			page_link = pdf.add_link()
			self.pages[name] = [page_link, pdf.page_no()]
			pdf.set_link(self.pages[name][0], self.pages[name][1])
		else:
			print('Lineup Maker : Skipping asset : "{}"'.format(asset.name))
	
	def set_status_color(self, pdf, status=-2):
		if status == V.Status.NOT_SET.value or status == V.Status.NOT_NEEDED.value:
			contrat_value = 50
			add_color = contrat_value if (self.content_background_color[0]+self.content_background_color[1]+self.content_background_color[2])/3 < 128 else -contrat_value

			color = self.color_add(self.content_background_color, add_color)
			pdf.set_text_color(r=color[0], g=color[1], b=color[2])
		elif status == V.Status.NOT_STARTED.value:
			pdf.set_text_color(r=200, g=50, b=0)
		elif status == V.Status.WIP.value:
			pdf.set_text_color(r=200, g=200, b=0)
		elif status == V.Status.DONE.value:
			pdf.set_text_color(r=50, g=200, b=0)
		else:
			pdf.set_text_color(r=self.text_color[0], g=self.text_color[1], b=self.text_color[2])

	def set_texture_text_size(self, name):
		texture_count = 0
		for material in self.context.scene.lm_asset_list[name].material_list:
			texture_count += len(material.texture_list)
		
		if texture_count:
			if texture_count > 6:
				self.font_size_texture = int(math.floor(self.composite_res[2]*0.83/texture_count))
				self.character_size_texture = (math.ceil(self.font_size_texture/2), self.font_size_texture)
			else:
				self.font_size_texture = int(math.floor(self.composite_res[0]*20/self.composite_res[1]))
				self.character_size_texture = (math.ceil(self.font_size_texture/2), self.font_size_texture)

