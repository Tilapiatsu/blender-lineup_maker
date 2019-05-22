import bpy
import re
import json
import os
from os import path

from . import variables as V
from . import preferences as P

class NamingConvention(object):
	def __init__(self, context, name,  convention, filepath=None):
		self.context = context
		self.scn = context.scene
		self.param = V.GetParam(self.scn).param
		self.fullname = name
		self.name, self.ext = path.splitext(name)

		if self.ext:
			self.ext = self.ext.lower()
		if self.name:
			self.name = self.name.lower()
		
		self.filepath = filepath
		self.convention = convention
		self._naming_convention = None
		self._words = None
		self._names = None

		self._keywords = None
		self._channels = None

		self._json = None

	def __eq__(self, other):
		if isinstance(other, NamingConvention):
			is_equal = True

			if len(self.naming_convention['included']) != len(other.naming_convention['included']):
				return False
			
			for i,c in enumerate(self.naming_convention['included']):
				if c != other.naming_convention['included'][i]:
					is_equal = False
					break

			return is_equal
		return NotImplemented
	
	@property
	def naming_convention(self):
		if self._naming_convention is None:
			self._naming_convention = self.slice_name()

		return self._naming_convention

	@naming_convention.setter
	def naming_convention(self, naming_convention):
		if isinstance(naming_convention, dict):
			self._naming_convention = naming_convention

		else:
			print('"{}" need to be a dict'.format(naming_convention))

	@property
	def json(self):
		if self._json is None:
			self._json = self.get_json_data
		
		return self._json

	@property
	def words(self):
		word_pattern = re.compile(r'[{0}]?(<([a-zA-Z0-9]+)(\?)?(\!)?>)[{0}]?|[{0}]?([^<][a-zA-Z0-9]+[^>])[{0}]?'.format(self.param['lm_separator']), re.IGNORECASE)
		self._words = word_pattern.finditer(self.convention)
		return self._words
	
	@property
	def word_list(self):
		return [w.group(2).lower() for w in self.words]
	
	@property
	def optionnal_words(self):
		return [False if w.group(3) is None else True for w in self.words]
	
	@property
	def included_words(self):
		return [w.group(2).lower() if w.group(4) is None else False for w in self.words]

	@property
	def names(self):
		name_pattern = re.compile(r'[{0}]?([a-zA-Z0-9]+)[{0}]?'.format(self.param['lm_separator']), re.IGNORECASE)
		self._names = name_pattern.finditer(self.name)
		
		return self._names
	
	@property
	def name_list(self):
		return [n.group(1) for n in self.names]

	@property
	def channels(self):
		if self._channels is None:
			channels = {}
			for c in self.param['lm_texture_channels']:
				if c.shader not in channels.keys():
					channels.update({c.shader:{c.channel:c.name}})
				else:
					if c.channel not in channels[c.shader].keys():
						channels[c.shader] = {c.channel:[c.name]}
					else:
						try:
							channels[c.shader][c.channel].append(c.name)
						except KeyError:
							channels[c.shader].update({c.channel:[c.name]})

			self._channels = channels
		
		return self._channels

	@property
	def keywords(self):
		if self._keywords is None:
			keywords = {}
			for k in self.param['lm_keywords']:
				keywords.update({k.name:[]})
			for k in self.param['lm_keyword_values']:
				if k.keyword not in keywords.keys():
					keywords.update({k.keyword:[k.name]})
				else:
					keywords[k.keyword].append(k.name)

			self._keywords = keywords
		
		return self._keywords

	def slice_name(self):
		def assign(return_dict, word, value, excluded):
			return_dict[word] = value
			if excluded is None:
				return_dict['included'].append(value)

			return True

		def assign_value(ckws, value, return_dict, word, optionnal, excluded, count):
			assigned = False
			if word in ckws.keys():
				if len(ckws[word]):
					if value in ckws[word]:
						assigned = assign(return_dict, word, value, excluded)
					elif '#' in ckws[word][0]: # Numeric
						pattern = re.compile(r'([a-zA-Z]?)([#]+)([a-zA-Z]?)', re.IGNORECASE)
						matches = pattern.finditer(ckws[word][0])

						p = r''
						for m in matches:
							if m.group(1):
								p = p + m.group(1)
							if m.group(2):
								p = '\d{{0}}'.format(len(m.group(2)))
							if m.group(3):
								p = p + m.group(3)
						
						pattern = re.compile(p, re.IGNORECASE)
						matches = pattern.finditer(ckws[word][0])

						for m in matches:
							if m:
								assigned = assign(return_dict, word, value, excluded)
								break
				else:
					if optionnal is None: # Not Optionnal
						assigned = assign(return_dict, word, value, excluded)
						return_dict['included'].append(value)
					else: # Optionnal
						assigned = assign(return_dict, word, value, excluded)
						
			
			return return_dict, assigned
			
		naming_convention = {'name':[], 'fullname': self.fullname, 'hardcoded':[], 'match':True, 'included':[]}

		if self.filepath:
			naming_convention.update({'file':self.filepath})

		names = self.name_list
		optionnal_words = self.optionnal_words

		name_length = len(self.name_list)
		optionnal_words_length = len(self.optionnal_words)

		i = 0
		remaining = optionnal_words_length
		for w in self.words:
			word = w.group(1)
			keyword = w.group(2)
			optionnal = w.group(3)
			excluded = w.group(4)
			hardcoded = w.group(5)

			assigned = True
			if i < name_length:
				if hardcoded is not None: # Hardcoded
					if names[i] == hardcoded.lower():
						naming_convention['hardcoded'].append(hardcoded)
						naming_convention['name'].append(hardcoded)
						remaining = remaining -1
					else:
						naming_convention['match'] = False
						break
				else:
					if optionnal is None: # Keyword
						naming_convention, assigned = assign_value(self.keywords, names[i], naming_convention, keyword.lower(), optionnal, excluded, i)
						remaining = remaining -1
					else: # Optionnal
						if len(self.keywords[keyword.lower()]): # If the Optionnal Keyword have a list or keyword values
							if names[i] in self.keywords[keyword.lower()]: # if the name is in the keyword values
								naming_convention, assigned = assign_value(self.keywords, names[i], naming_convention, keyword.lower(), optionnal, excluded, i)
								remaining = remaining -1
							else:
								assigned = False

						else: # If the Optionnal Keyword is undefined
							if len(names) < len(optionnal_words): # the name is shorter than the keywords
								if remaining > name_length - i + 1: # The name should be skipped
									assigned = False
								else:
									if keyword.lower() not in self.get_other_ckws(self.keywords, keyword.lower()):
										naming_convention, assigned = assign_value(self.keywords, names[i], naming_convention, keyword.lower(), optionnal, excluded, i)
										remaining = remaining -1

				
				if assigned is False:
					i = i - 1
				else:
					naming_convention['name'].append(names[i])

			i = i + 1

		return naming_convention

	def pop_name(self, item, duplicate=True):
		new_naming = self.naming_convention
		if item not in new_naming['fullname']:
			print('Lineup Maker : Naming Convention : Word "{}" is not in the filename {}'.format(item, new_naming['fullname']))
			return

		if item in new_naming['name']:
			new_naming['name'].remove(item)
		
		key_to_del = False
		for key,value in new_naming.items():
			if value == item:
				key_to_del = key
				break

		if key_to_del:
			del new_naming[key]

		item_pattern = re.compile(r'[{0}]?({1})[{0}]?'.format(self.param['lm_separator'], item), re.IGNORECASE)
		matches = item_pattern.finditer(new_naming['fullname'])

		for m in matches:
			new_naming['fullname'] = new_naming['fullname'].replace(m.group(0), '')

		if duplicate:
			return new_naming
		else:
			self.naming_convention = new_naming
			return None

	def get_other_ckws(self, ckw_dict, current_key):
		other_ckws = []
		for ckw, ckws in ckw_dict.items():
			if ckw != current_key:
				other_ckws = other_ckws + ckws

		return other_ckws

	def get_json_data(self):
		files = os.listdir(self.filepath)

		json = [path.join(self.filepath, f) for f in files if path.splitext(f)[1].lower() == '.json' ]

		json_data = {}
		for j in json:
			json_name = path.splitext(path.basename(j))[0]
			with open(j) as json_file:  
				data = json.load(json_file)
				json_data[json_name] = data

		return json_data