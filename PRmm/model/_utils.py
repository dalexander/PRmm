from glob import glob
import os, os.path as op

def find(pattern, path):
    return glob(op.join(path, pattern))

def findOne(pattern, path):
    result = find(pattern, path)
    if len(result) < 1:   raise IOError, "No file found matching pattern %s" % pattern
    elif len(result) > 1: raise IOError, "More than one file found matching pattern %s" % pattern
    else: return result[0]

def findOneOrNone(pattern, path):
    result = find(pattern, path)
    if len(result) < 1:   return None
    elif len(result) > 1: raise IOError, "More than one file found matching pattern %s" % pattern
    else: return result[0]

def updir(path):
    return op.abspath(op.join(path, os.pardir))



# Caching decorator
## Implement me!
