from PRmm.io import *
from pbcore.io import *
from ConfigParser import ConfigParser

from docopt import docopt
import tempfile, os, os.path as op

from PRmm.model._utils import *

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

        if trcFname is not None:
            self.trcF = TrcH5Reader(trcFname)
        else:
            self.trcF = None

        if basFname is not None:
            self.basF = BasH5Reader(basFname)
        else:
            self.basF = None

        if plsFname is not None:
            self.plsF = PlsH5Reader(plsFname, self.basF)
        else:
            self.plsF = None

        if alnFname is not None:
            self.alnF = CmpH5Reader(alnFname)
            if len(self.alnF.movieNames) > 1:
                raise ValueError, "No support for multi-movie jobs yet"
        else:
            self.alnF = None

        referenceFname = referenceFname
        if referenceFname is not None:
            self.refF = IndexedFastaReader(referenceFname)
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

    @staticmethod
    def fromIniFile(iniFilename, sectionName):
        cp = ConfigParser()
        cp.optionxform=str
        cp.read(iniFilename)
        #import ipdb; ipdb.set_trace()
        opts = dict(cp.items(sectionName))
        print opts
        return ReadersFixture(trcFname=opts.get("Traces"),
                              plsFname=opts.get("Pulses"),
                              basFname=opts.get("Bases"),
                              alnFname=opts.get("Alignments"))



    def __repr__(self):
        import pprint
        readerFieldNames = [ fn for fn in dir(self) if fn.endswith("F") ]
        readersRepr = "\n  " + ",\n  ".join(["%s=%s" % (fieldName, getattr(self, fieldName))
                            for fieldName in readerFieldNames])
        return "<ReadersFixture %s >" % readersRepr


    # -- Essential info ---

    @property
    def movieName(self):
        pass

    @property
    def hasTraces(self):
        pass

    @property
    def hasPulses(self):
        pass

    @property
    def hasBases(self):
        pass

    @property
    def hasAlignments(self):
        pass


    # --- Access by holenumber ---

    def holeNumbers(self):
        pass

    def holeNumbersWithAlignments(self):
        pass

    def __getitem__(self, holenumber):
        pass



__doc__ = \
"""
Usage:
  fixture.py fromSecondaryJobPath <secondaryJobPath>
  fixture.py fromPaths <reportsPath> <secondaryJobPath>
  fixture.py fromIni <iniFile> <sectionName>
"""

def main():
    args = docopt(__doc__)
    if args["fromSecondaryJobPath"]:
        fx = ReadersFixture.fromSecondaryJobPath(args["<secondaryJobPath>"])
    elif args["fromPaths"]:
        fx = ReadersFixture.fromPaths(args["<reportsPath>"], args["<secondaryJobPath>"])
    elif args["fromIni"]:
        fx = ReadersFixture.fromIniFile(args["<iniFile>"], args["<sectionName>"])
    else:
        print "Bad command"
        return -1
    import ipdb; ipdb.set_trace()
    print fx

if __name__ == '__main__':
    main()
