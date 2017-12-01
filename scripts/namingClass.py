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
             'm': 'M'
              }
dLods =     { 'hi': 'high',
              'lo': 'low',
              'sim': 'sim',
              }
dNamingConvention = { 'dneg': 'side_mod_part_func',
                      'scanline': 'type_lod_side_part_idx'}

class Name:
    '''
    Common base class for node names
    '''

    count = 0
    prodConvention = 'type_lod_side_part_idx'

    def __init__(self, **kwargs):
        '''
        self.tType = (0, self.type)
        self.tLod = (1, self.lod)
        self.tSide = (2, self.side)
        self.tPart = (3, self.part)
        self.tIdx = (4, self.idx)
        '''
        # default name token values
        self.type = 'null'
        self.func = 'null'
        self.mod= 'module'
        self.lod = 'high'
        self.side = 'M'
        self.part = 'model'
        self.idx = 0
        # set name based on passed in arguments
        self.__dict__.update(kwargs)

        # init an actual name string using the class methods
        self.deconstructProdConvention()
        self.constructName()

        Name.count += 1

    def __set__(self, instance, value):
        print '!!! Name.__set__ called ~~~'
        self.constructName(self)

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
        #self.name = '%s_%s_%s_%s_%3di' %(self.type, self.lod, self.side, self.part, self.idx)
        self.name = '{}_{}_{}_{}_{:03d}'.format(self.type, self.lod, self.side, self.part, self.idx)
        for iprodConvention,t in enumerate(dNamingConvention):
            print t
            if t == 'idx':
                print t, i, self.tokens[i]
                #self.tokens[i] = int(self.tokens[i])

        return self.name

    def constructNameConvention(self):
        pass

    def displayName(self):
        self.constructName()
        print "\tType : ", self.type,  ", lod: ", self.lod,  ", side: ", self.side,  ", part: ", self.part,  ", idx: ", self.idx,
        print '\t',self.name,

    def deconstructProdConvention(self):
        '''
        Figure out what order the name tokens should be in based on the given prodConvention
        :return:
        '''
        print '\tConvention:', Name.prodConvention
        self.tokens = Name.prodConvention.split('_')
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

########### EXAMPLE


'''

import sys
sys.path.insert(0, '/u/alz/PycharmProjects/DnegCloth')
import naming as N
reload(N)



bla = N.Name()
bla.displayName()
print bla.deconstructProdConvention()

N.dNamingConvention

bla.createNode('nucleus')

bla.side = 'right'
bla.displayName()


N.Name.prodConvention = 'side_part_idx_type'
foo = N.Name()
foo.name
bla.prodConvention

print bla.deconstructProdConvention()
dir(bla)


'''
