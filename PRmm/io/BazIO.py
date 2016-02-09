import json, struct, mmap

class Sanity(object):
    C0 = 0xD2
    C1 = 0x58
    C2 = 0x4C
    C3 = 0x52
    C  = [C0, C1, C2, C3]
    STRING = "".join(map(chr, C))

M = 1024*1024    
         
exampleBaz = "/pbi/collections/315/3150057/r54006_20160119_011818/1_A01/bz30019_x1E3_i0/m54006_160119_012200.baz"

f = open(exampleBaz, "rb")
m = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)

pos = m.find(Sanity.STRING)

bazHeader = json.loads(m[:pos])["HEADER"]

# In [10]: bazHeader.keys()
# Out[10]:    
# [u'ZMW_UNIT_FEATURES_LUT',
#   u'BAZWRITER_VERSION',
#   u'MOVIE_NAME',
#   u'COMPLETE',
#   u'TRUNCATED',
#   u'BAZ_MAJOR_VERSION',
#   u'P4_VERSION',
#   u'FRAME_RATE_HZ',
#   u'PACKET',
#   u'BAZ_PATCH_VERSION',
#   u'ZMW_NUMBER_LUT',
#   u'MOVIE_LENGTH_FRAMES',
#   u'LF_METRIC',
#   u'BASE_CALLER_VERSION',
#   u'SLICE_LENGTH_FRAMES',
#   u'HF_METRIC',
#   u'MF_METRIC',
#   u'BAZ_MINOR_VERSION']

mfMetricsDesc = bazHeader["MF_METRIC"]

#jsonHeader = f.read(1*M)
