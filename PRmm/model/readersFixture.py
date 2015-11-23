from PRmm.io import *
from pbcore.io import *
from ConfigParser import ConfigParser

from docopt import docopt
import tempfile, os, os.path as op

from PRmm.model._utils import *
from PRmm.model.zmwFixture import ZmwFixture

__all__ = [ "ReadersFixture" ]


class TraceUnavailable(Exception): pass


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
                 alnFname=None, refFname=None):

        self.trcF = None if not trcFname else TrcH5Reader(trcFname)
        self.basF = None if not basFname else BasH5Reader(basFname)
        self.plsF = None if not plsFname else PlsH5Reader(plsFname, self.basF)
        self.refF = None if not refFname else IndexedFastaReader(refFname)
        self.alnF = None if not alnFname else CmpH5Reader(alnFname)
        if self.alnF is not None:
            if len(self.alnF.movieNames) > 1:
                raise ValueError, "No support for multi-movie jobs"
        if self.trcF is None:
            raise ValueError, "trc.h5 required, for now"


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
        iniFilename = op.abspath(op.expanduser(iniFilename))
        cp = ConfigParser()
        cp.optionxform=str
        cp.read(iniFilename)
        opts = dict(cp.items(sectionName))
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
        return self.trcF.movieName

    @property
    def frameRate(self):
        return self.trcF.frameRate

    @property
    def hasTraces(self):
        return self.trcF is not None

    @property
    def hasPulses(self):
        return self.plsF is not None

    @property
    def hasBases(self):
        return self.basF is not None

    @property
    def hasReference(self):
        return self.refF is not None

    @property
    def hasAlignments(self):
        return self.alnF is not None

    # --- Access by holenumber ---

    @property
    def holeNumbers(self):
        return self.trcF.holeNumbers

    @property
    def holeNumbersWithAlignments(self):
        if self.hasAlignments:
            return sorted(set.intersection(set(self.holeNumbers), set(self.alnF.holeNumber)))
        else:
            return []

    def __getitem__(self, holeNumber):
        if holeNumber not in self.holeNumbers:
            raise TraceUnavailable, "No trace for desired HN"
        else:
            return ZmwFixture(self, holeNumber)



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
    print fx

if __name__ == '__main__':
    main()
