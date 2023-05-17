
import collections, autocorrect, shelve, xml
from xml.dom import minidom
import re
from dreqPy import dreq

re_nm = re.compile( '[0-9]+(nm|m|hPa)' )

class BuildWl(object):
  """Build a list of words."""
  def __init__(self):
    self.cc = collections.defaultdict( set )
  def add(self,k,v):
    """Add a value 'v' to the lsit of words stored under key 'k'"""
    self.cc[k].add(v)


words = collections.defaultdict( set )
wl = collections.defaultdict( set )
def getstuff():
  """Function to extract titles from the data request"""
  khyzz = collections.defaultdict( set )
  for i in dq.coll['var'].items:
    for w in i.title.split():
      words[w].add( i.title )
      wl[w.lower()].add( i.title )

  bl = dict()
  for x in range(1,8):
    bl[x] = [w for w in words if len(w) == x]

  khy = [k for k in words if k.find('-') != -1]
  for k in khy:
    this = k.replace('-',' ').lower()
    for i in dq.coll['var'].items:
      if i.title.lower().find( this ) != -1:
        khyzz[k.lower()].add( i.title )
  return words, wl, khy, khyzz, bl
 

##Articles: a, an, the
## Coordinating Conjunctions: and, but, or, for, nor, etc. 
## Prepositions (fewer than five letters): on, at, to, from, by, etc` ... per

## that: possibly a conjunction, but not likely in this context

class Tables(object):
  def __init__(self):
    """Initialise tables of constants .. exceptions to the general capitalisation rules"""
    self.special = dict()
    self.lower = dict()
    self.lower[1] = ['a','m','s']
    self.lower[2] = ['as', 'at', 'by', 'in', 'nm', 'of', 'on', 'or', 'to']
    self.lower[3] = [ 'and', 'any', 'but', 'for',  'non', 'nor', 'not', 'out', 'per', 'the']
    self.lower[4] = ['into', 'onto', 'over', 'than', 'with', 'from']
    self.lower[5] = ['neither','either','degree']


    self.special[1] = ['X', 'Y', 'T', 'O', 'D' ]
    self.special[2] = ['10', '1H', '1m', '2H', '2m', '3D', '50', 'C3', 'C4', 'CO', 'H2', 'N2', 'NO', 'Ox', 'O2', 'O3', 'OD', 'OH', 'XY', 'pH']
    self.special[3] = ['kgC','100', '10m', '13C', '14C', '17O', '18O', '20C', '440', '443', '500', '550', '850', '865', '870', 'CH4', 'CO2', 'CWD', 'DMS', 'HCl', 'HO2', 'N2O', 'NH3', 'NH4', 'NHx', 'NO2', 'NO3', 'NOx', 'NOy', 'NPP', 'O1D',  'PAN', 'PBL', 'PO2', 'SF6', 'SO2', 'SO4', 'SWE', 'TEM', 'TOA', 'hPa']
    self.special[4] = ['1000', '100m', '300m', '700m', 'C2H2', 'C2H6', 'C3H6', 'C3H8', 'CFAD', 'HNO3', 'MISR', 'PCO2', 'PM10' ]
    self.special[5] = ['10hPa', '13CO2', '14CO2', '2000m', '4XCO2', '550nm', 'CFC11', 'CFC12', 'DI14C', 'ISCCP', 'MODIS', 'NMVOC', 'PM1.0', 'PM2.5', 'UGRID']
    self.special[6] = ['CFC113', 'HCFC22'] 
    self.special[7] = ['CALIPSO', 'PARASOL']
    self.special[8] = ['(=dp/dt)', '13Carbon', '14Carbon', 'CH3COCH3', 'CloudSat']

    self.people = set( ['Leovy', 'Hibler', 'Wesely', 'Eliassen', 'Vaisala', 'Redi', 'Boussinesq' ] )
    self.vocab = set( ['Dianeutral', 'Diazotrophs', 'Downwelling', 'Epineutral', 'Landuse', 'Longwave', 'Meltpond', 'Mesozooplankton', 'Methanogenesis', 'Methanotrophy', 'Microzooplankton', 'Needleleaf', 'Picophytoplankton', 'Streamfunction', 'Submesoscale', 'Thermosteric'] )

class Specials(object):
  """Initialise some tables for further special cases"""
  def __init__(self,tables):
    self.ll = set()
    self.uu = set()
    for k,v in tables.lower.items():
      for x in v:
         self.ll.add(x)

    for k,v in tables.special.items():
      for x in v:
         self.uu.add(x)

    hyphen02 = set(['Run-off','Air-to-Sea','2D-Field','3D-Field'])
    self.ehy = dict()
    for k in hyphen02:
      self.ehy[ k.lower() ] = k

tables = Tables()
specials = Specials(tables)

re_x = re.compile( '([;:,\-\(\)"\'\_+*><=/.\[\]])' )
re_n = re.compile( '[0-9]\.*[0-9]' )
re_chem = re.compile( '^(((C|N|O|Br|F|Fe|H|Ca|Cl|Ch|S|Si)[0-9xy]{0,4}){1,6})$' )

def cleantext(ss):
  res = set( re_x.findall( ss ) )
  for x in res:
    ss = ss.replace( x, ' ' )
  ss = ' '.join( [x.strip() for x in ss.split() ] )
  return ss
  

def mycap(s):
  if s in specials.ll:
    return s.lower()
  elif s in specials.uu:
    return s
  elif re_nm.match(s):
    return s
  else:
    return s.capitalize()

def getFrag(name):
 """Returns a Frag class object, with name specified by argument."""
 class Frag(object):
  """Dynamically generated class object. On intiation, it represents a string object with added methods."""
  words = collections.defaultdict( set )
  wl = collections.defaultdict( set )
  wl2 = BuildWl()
  def __init__(self,s,ttl):
    self.prf = ''
    self.sfx = ''
    if s[0] in ['[','(',',','.','"']:
      self.prf = s[0]
    if s[-1] in [']',')',',','.','"',';']:
      self.sfx = s[-1]
    self.word = s[len(self.prf):len(s)-len(self.sfx)]
    self.words[self.word].add( ttl )
    self.ttl = ttl
 
  def cap(self):
    if self.word.find( '-' ) != -1:
      if self.word.lower() in specials.ehy:
        this = specials.ehy[self.word.lower()]
      else:
        this = '-'.join( [mycap(x) for x in self.word.split('-')] )
    else:
      this = mycap( self.word )
      
    if len(this) == 1:
      print( 'L1: %s ' % (self.word, this ) )

    self.wl[this].add( self.ttl )
    self.wl2.add(this, self.ttl )
    self.styled = this

    return ''.join( [self.prf,this,self.sfx] )

  def low(self):
    self.wl[self.word.lower()].add( self.ttl )
    self.wl2.add(self.word.lower(), self.ttl )
    self.styled = self.word.lower()
    return ''.join( [self.prf,self.word.lower(),self.sfx] )

  def full(self,save=True):
    if save:
      self.wl[self.word].add( self.ttl )
      self.wl2.add(self.word, self.ttl )
      self.styled = self.word
    return ''.join( [self.prf,self.word,self.sfx] )

 Frag.__name__ = name
 return Frag

class TitleCase(object):
  def __init__(self):
    self.Frag = getFrag( 'FragVar' )
    self.Fragd = getFrag( 'FragDesc' )
    self.sh = shelve.open( 'inSh/titleCase3' )
    self.desc = set()
    self.chem = set()
    specials = set()
    lowers = set()
    for k in tables.special:
      for x in tables.special[k]:
        specials.add(x)
    for k in tables.lower:
      for x in tables.lower[k]:
        lowers.add(x)

    ee = dict()
    for i in dq.coll['var'].items:
      parts = [self.Frag(x,i.title) for x in i.title.split() ]
      for x in cleantext( i.description ).split():
        if len( re_n.findall(x) ) == 0:
          if re_chem.match(x) == None:
            y = self.Fragd(x,i.description)
            y.low()
            self.desc.add( y.word.lower() )
          else:
            self.chem.add( x )

      pold = [x.full(save=False) for x in parts]
      pnew = []
      if parts[0].word in specials:
        pnew.append( parts[0].full() )
      else:
        pnew.append( parts[0].cap() )

      for p in parts[1:]:
        if p.word in specials:
          pnew.append( p.full() )
        elif p.word.lower() in lowers:
          pnew.append( p.low() )
        else:
          pnew.append( p.cap() )
        if p.styled == 'ice':
          print( 'ICE:: %s' % parts )
        elif p.word.lower() == 'ice':
          print( 'ice: %s' % [p.word,p.styled, parts ] )

      if pold != pnew:
         ee[tuple(pnew)] = (i.label,i.uid,i.title)


    
    for l in sorted( ee.keys() ):
         print( '----------------' )
         ## old = ' '.join(ee[l][-1])
         old = ee[l][-1]
         new = ' '.join(l)
         print( "%s: %s ==> %s [%s]" % (ee[l][0],old,new,ee[l][1]) )
         self.sh[old] = new

    print( 'NUMBER OF CHANGES: %s' % len(ee) )

  def list(self):
    for k in sorted(tables.special.keys()):
      print( [k, ':: ',' '.join( sorted( tables.special[k] ) )] )
    for k in sorted(tables.lower.keys()):
      print( [k, ':: ',' '.join( sorted( tables.lower[k] ) )] )
      

class MyChecker(object):
  """Compare a set of words against a list of known words and generate an error report for unknown words.
     Input:
       tag: an string identifier copied into output records;
       frag: a class object generated by getFrag. -- used to manage tokens generated by splitting title;
  """
  def __init__(self,tag,frag,full=True):
    self.full = full
    self.tag = tag
    self.Frag = frag
    self.ns = self.nc = self.ne = 0
    sp = autocorrect.Speller()
    self.known = set( sp.nlp_data.keys() ).union( [x.lower() for x in tables.vocab] ).union( (x.lower() for x in tables.people) )


  def check(self,k,key=None):
    if key == None:
      key = k
    if k in specials.uu:
      self.ns += 1
    elif k.lower() in self.known:
      self.nc += 1
    else:
      if self.full:
        print( '%sUNKNOWN: ' % self.tag, k, self.Frag.wl[key] )
      else:
        print( k )
      self.ne += 1


class CFdesc(object):
  def __init__(self):
    self.Fragd = getFrag( 'FragDesc' )
    self.chem = set()
    self.desc = set()
    self.contentDoc = minidom.parse( 'ing02/inputs/cf-standard-name-table_v60.xml' )
    vl = self.contentDoc.getElementsByTagName( 'description' )
    for v in vl:
      if v.firstChild != None:
        this = v.firstChild.data
        for x in cleantext( this ).split():
          if len( re_n.findall(x) ) == 0:
            if re_chem.match(x) == None:
              y = self.Fragd(x,this)
              y.low()
              self.desc.add( y.word.lower() )
    

def run():
  tc = TitleCase()
  tc.list()

  myCheck = MyChecker('v::', tc.Frag)

  for k in sorted( tc.Frag.wl.keys() ):
    if k.find('-') != -1:
      for x in k.split( '-'):
        myCheck.check(x,key=k)
    else:
      myCheck.check(k)

  myCheck = MyChecker( 'd::', tc.Fragd, full=False)
  for k in sorted( tc.Fragd.wl.keys() ):
    if k.find('-') != -1:
      for x in k.split( '-'):
        myCheck.check(x,key=k)
    else:
      myCheck.check(k)

  print( (myCheck.ns, myCheck.nc, myCheck.ne ) )
  tc.sh.close()
  return tc

def run2():
  cf = CFdesc()


  myCheck = MyChecker( 'd::', cf.Fragd, full=False)
  for k in sorted( cf.Fragd.wl.keys() ):
    if k.find('-') != -1:
      for x in k.split( '-'):
        myCheck.check(x,key=k)
    else:
      myCheck.check(k)

  print( (myCheck.ns, myCheck.nc, myCheck.ne ))
  cf.sh.close()
  return cf

if __name__ == "__main__":
  import sys
  dq = dreq.loadDreq()
  tc = run()
  ##cf = run2()

