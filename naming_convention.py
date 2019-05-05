import bpy
import re
from os import path

from . import variables as V
from . import preferences as P

class NamingConvention(object):
    def __init__(self, name, naming_convention):
        self.name, self.ext = path.splitext(name)

        if self.ext:
            self.ext = self.ext.lower()
        if self.name:
            self.name = self.name.lower()
        self.naming_convention = naming_convention.lower()


    
    def slice(self):
        # person = {'first': 'Jean-Luc', 'last': 'Picard'}
        # string = '{p[first]} {p[last]}'.format(p=person)
        # <PROJECT>_<TEAM>_<CATEGORY>_<INCR>_<GENDER>
        spans = {}
        keyword_pattern = re.compile(r'<[{0}]?(\w+)>[{0}]?'.format(V.LM_SEPARATORS), re.IGNORECASE)
        name_pattern = re.compile(r'[{0}]?([a-zA-Z0-9]+)[{0}]?'.format(V.LM_SEPARATORS))
        separator_pattern = re.compile(r'[{}]'.format(V.LM_SEPARATORS))
        
        keywords = keyword_pattern.finditer(self.naming_convention)
        names = name_pattern.finditer(self.name)
        separators = separator_pattern.finditer(self.naming_convention)
        
        for n in names:
            print(n.group(1))

        for i,k in enumerate(keywords):
            print(k)
            print(k.group(1))
            if k.group(1) in V.LM_NAMING_CONVENTION_KEYWORDS:
                spans[k.group(1)] = names[i].group(1)

        print(spans)

        return keywords

        