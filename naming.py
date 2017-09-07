# written by: Alon Zaslavsky    # alz@dneg.com
# class based naming API

import maya.cmds as mc

dTypes =    { 'null': 'null',
              'grp': 'group',
              'crv': 'curve',
              'mesh': 'mesh',
              'nurbs': 'nurbs',
              # cloth
              'cloth': 'nCloth',
              'rigid': 'nRigid',
              'nuc': 'nucleus',
              'dynConst': 'dynamicConstraint',
              # rigging
              'bs': 'blendShape',
              'md': 'multiplyDivide',
              }
dFunc =     { 'env': 'env',
              'geo': 'geo',
              'mesh': 'mesh',
              }
dSides =    { 'r': 'R',
             'l': 'L',
             'm': 'M',
             'right': 'R',
             'left': 'L',
              }
dLods =     { 'hi': 'high',
              'lo': 'low',
              'sim': 'sim',
              }
dNamingConvention = { 'dneg': 'side_mod_part_func',
                      'scanline': 'type_lod_side_part_idx'}

class Name(object):
    '''
    Common base class for node names
    '''

    count = 0

    def __init__(self, **kwargs):
        '''

        '''
        # default name token values
        self.type = 'null'
        self.func = 'null'
        self.mod= 'module'
        self.lod = 'high'
        self._side = 'M'
        self.part = 'model'
        self.idx = 0
        self.prodConvention = dNamingConvention['dneg']
        # set name based on passed in arguments
        self.__dict__.update(kwargs)

        # init an actual name string using the class methods
        self.deconstructProdConvention()
        self.constructName()

        Name.count += 1

    def __set__(self, instance, value):
        print '!!! Name.__set__ called ~~~'
        self.constructName(self)

    @property
    def side(self):
      '''
      It's a function that's executed when 'my_class_property' is read.
      '''
      return self._side

    @side.setter
    def side(self, value):
      '''
      It's a function that's executed when 'my_class_property' is written to.
      '''
      if value == 'r' or value == 'right':
        self._side = 'R'
      elif value == 'l' or value ==  'left':
        self._side = 'L'
      elif value == 'm' or value == 'middle':
        self._side = 'M'


    def displayCount(self):
        '''
        function to display count
        '''
        print "Total names created %d" % Name.count

    def constructName(self):
        '''
        function that constructs the name string using the instance variables.
        :return: (string) constructed name
        '''
        formatNameString = '"'
        for i in range(len(self.tokens)):
          formatNameString += '{%i}_' % i
        formatNameString = formatNameString[:-1]
        formatNameString += '".format('
        for tok in (self.tokens):
          formatNameString += 'self.%s,' % tok
        formatNameString += ')'
        #print 'format this: ', formatNameString
        self.name = eval(formatNameString)
        return self.name

    def constructNameConvention(self):
        pass

    def displayName(self):
        self.constructName()
        
        return self.name,

    def deconstructProdConvention(self):
        '''
        Figure out what order the name tokens should be in based on the given prodConvention
        :return:
        '''
        print '\tConvention:', self.prodConvention
        self.tokens = self.prodConvention.split('_')
        print '\t', self.tokens
        for i,t in enumerate(self.tokens):
            dNamingConvention[i] = t
        return self.tokens

    def checkNamingDict(self):
        pass

    def createNode(self, type, **kwargs):
        sNewNode = mc.createNode(type)
        self.type = type

        self.constructName()
        self.displayName()
        sNewNode = mc.rename(sNewNode, self.name)
        return self.name






########### EXAMLE


'''




import sys
sys.path.insert(0, '/u/alz/PycharmProjects/DnegCloth')
import naming as N


reload(N)
bla = N.Name(type='joint')
bla.displayName()
print bla.name

bla.side = 'r'
bla.prodConvention = 'side_part_banana'
bla.deconstructProdConvention()
bla.tokens.remove('side')

bla.tokens

bla.banana = '54'

print bla.func



'''