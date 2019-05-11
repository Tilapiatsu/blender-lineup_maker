import bpy
import re
from os import path

from . import variables as V
from . import preferences as P

class NamingConvention(object):
    def __init__(self, context, name, convention):
        self.context = context
        self.scn = context.scene
        self.param = V.GetParam(self.scn).param
        self.fullname = name
        self.name, self.ext = path.splitext(name)

        if self.ext:
            self.ext = self.ext.lower()
        if self.name:
            self.name = self.name.lower()

        self.convention = convention
        self._naming_convention = None
        self._words = None
        self._names = None

    @property
    def naming_convention(self):
        if self._naming_convention is None:
            self._naming_convention = self.slice_name()

        return self._naming_convention


    @property
    def words(self):
        if self._words is None:
            word_pattern = re.compile(r'[{0}]?(<([a-zA-Z0-9]+)(\?)?>)[{0}]?|[{0}]?([^<][a-zA-Z0-9]+[^>])[{0}]?'.format(self.param['lm_separator']), re.IGNORECASE)
            self._words = word_pattern.finditer(self.convention)
        return self._words

        
    @property
    def names(self):
        if self._names is None:
            name_pattern = re.compile(r'[{0}]?([a-zA-Z0-9]+)[{0}]?'.format(self.param['lm_separator']), re.IGNORECASE)
            self._names = name_pattern.finditer(self.name)
        
        return self._names


    def slice_name(self):
        def assign_value(ckws, value, return_dict, word):
            if word in ckws.keys():
                if len(ckws[word]):
                    if value in ckws[word]:
                        return_dict[word] = value
                else:
                    return_dict[word] = value
            else:
                return_dict[word] = value
            
            return return_dict
            
        naming_convention = {'name':[], 'fullname': self.fullname, 'hardcoded':[], 'match':True}
        names = [n.group(1) for n in self.names]
        name_length = len(names)
        for i,w in enumerate(self.words):
            if i < name_length:
                if w.group(4): # Hardcoded
                    if names[i] == w.group(4):
                        naming_convention['hardcoded'].append(w.group(4))
                        naming_convention['name'].append(w.group(4))
                    else:
                        naming_convention['match'] = False
                        break
                else:
                    if w.group(3): # Optionnal
                        if w.group(2).lower not in self.get_other_ckws(self.param['lm_keyword_values'], w.group(2).lower()):
                            naming_convention = assign_value(self.param['lm_keyword_values'], names[i], naming_convention, w.group(2).lower())
                    else: # Keyword
                        naming_convention = assign_value(self.param['lm_keyword_values'], names[i], naming_convention, w.group(2).lower())
                naming_convention['name'].append(names[i])
            else:
                naming_convention['match'] = False
                break
        return naming_convention

    def pop(self, item):
        new_naming = self.naming_convention
        if item in new_naming['name']:
            new_naming['name'].pop()
        
        if item in new_naming:
            new_naming.pop()
        
        item_pattern = re.compile(r'[{0}]?({1})[{0}]?'.format(self.param['lm_separator'], item), re.IGNORECASE)
        if len(item_pattern.finditer(new_naming['fullname'])):
            new_naming['fullname'] = item_pattern.sub(r'\0')

        self.naming_convention = new_naming

    def get_other_ckws(self, ckw_dict, current_key):
        other_ckws = []
        for ckw, ckws in ckw_dict.items():
            if ckw != current_key:
                other_ckws = other_ckws + ckws

        return other_ckws