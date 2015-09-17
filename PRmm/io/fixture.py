
from PRmm.io import *
from pbcore.io import *

from docopt import docopt
import tempfile, os, os.path as op
from glob import glob

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

__all__ = [ "ReadersFixture" ]

class ReadersFixture(object):
    """
    A *readers fixture* provides a simple means to collect reader
    objects associated the the trace, pulse, base, alignment, and
    reference files (or some subset of these files) associated with a
    single job, and further, a means to focus on a single ZMW and see
    different facets exposed by the different readers.

    At present the focus is on *single-movie jobs*.
    """
    # This will not typically be called directly!
    def __init__(self, trcFname=None,
                 plsFname=None, basFname=None,
                 alnFname=None, referenceFname=None):

        self.trcFname = trcFname
        if self.trcFname is not None:
            self.trcF = TrcH5Reader(self.trcFname)
        else:
            self.trcF = None

        self.basFname = basFname
        if self.basFname is not None:
            self.basF = BasH5Reader(self.basFname)
        else:
            self.basF = None

        self.plsFname = plsFname
        if self.plsFname is not None:
            self.plsF = PlsH5Reader(self.plsFname, self.basF)
        else:
            self.plsF = None

        self.alnFname = alnFname
        if self.alnFname is not None:
            self.alnF = CmpH5Reader(self.alnFname)
            if len(self.alnF.movieNames) > 1:
                raise ValueError, "No support for multi-movie jobs yet"
        else:
            self.alnF = None

        self.referenceFname = referenceFname
        if self.referenceFname is not None:
            self.refF = IndexedFastaReader(self.referenceFname)
        else:
            self.refF = None

    @staticmethod
    def fromSecondaryJobPath(jobPath):
        # reckon the reports path from the input fofn ...
        reportsPaths = set([ updir(path) for path in readFofn(op.join(jobPath, "input.fofn"))])
        if len(reportsPaths) > 1:
            raise ValueError, "No support for multi-movie jobs yet"
        else:
            reportsPath = list(reportsPaths)[0]
            return ReadersFixture.fromPaths(reportsPath, jobPath)

    @staticmethod
    def fromPaths(reportsPath, secondaryJobPath=None):
        basFname = findOneOrNone("*.bas.h5", reportsPath)
        plsFname = findOneOrNone("*.pls.h5", reportsPath)
        trcFname = findOneOrNone("*.trc.h5", updir(reportsPath))
        if secondaryJobPath:
            alnFname = findOneOrNone("*.cmp.h5", op.join(secondaryJobPath, "data"))
        else:
            alnFname = None
        return ReadersFixture(trcFname=trcFname, plsFname=plsFname,
                              basFname=basFname, alnFname=alnFname)

    @staticmethod
    def fromTraceSplitPaths(reportsPath, secondaryJobPath=None):
        # ARGGH!
        trcFnames = find("*split*.trc.h5", op.join(updir(reportsPath), "traceSplit"))
        trcFofn = tempfile.NamedTemporaryFile(suffix=".trc.fofn", delete=False)
        for fname in trcFnames:
            trcFofn.file.write(fname)
            trcFofn.file.write("\n")
        trcFofn.close()
        basFname = findOneOrNone("*.bas.h5", reportsPath)
        plsFname = findOneOrNone("*.pls.h5", reportsPath)
        if secondaryJobPath:
            alnFname = findOneOrNone("*.cmp.h5", op.join(secondaryJobPath, "data"))
        else:
            alnFname = None
        return ReadersFixture(trcFname=trcFofn.name, plsFname=plsFname,
                              basFname=basFname, alnFname=alnFname)

    def __repr__(self):
        fnameFields = [ fn for fn in dir(self) if fn.endswith("Fname") ]
        fnames = ", ".join(["%s=%s" % (fieldName, getattr(self, fieldName))
                            for fieldName in fnameFields])
        return "<ReadersFixture { %s }>" % fnames


__doc__ = \
"""
Usage:
  fixture.py fromSecondaryJobPath <secondaryJobPath>
  fixture.py fromPaths <reportsPath> <secondaryJobPath>
"""

def main():
    args = docopt(__doc__)
    if args["fromSecondaryJobPath"]:
        fx = ReadersFixture.fromSecondaryJobPath(args["<secondaryJobPath>"])
    else:
        fx = ReadersFixture.fromPaths(args["<reportsPath>"], args["<secondaryJobPath>"])
    print fx

if __name__ == '__main__':
    main()
