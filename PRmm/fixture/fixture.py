from PRmm.io import *
from pbcore.io import *
from ConfigParser import ConfigParser

from docopt import docopt
import tempfile, os, os.path as op

from PRmm.model._utils import *
from PRmm.model.utils import cached
from PRmm.fixture.fixtureZmw import FixtureZmw

__all__ = [ "Fixture" ]


class TraceUnavailable(Exception): pass

# we can move this to pbcore.io once we move VP
def _openBasecallsFile(fname):
    if fname.endswith(".bam"):
        return ZmwReadStitcher(fname)
    else:
        return BasH5Reader(fname)

class Fixture(object):
    """
    A *fixture* provides a simple means to collect reader
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

        def perhaps(constructor, fname, *args):
            return (None if not fname else constructor(fname, *args))

        self.trcF = perhaps(TrcH5Reader, trcFname)
        self.basF = perhaps(_openBasecallsFile, basFname)
        self.refF = perhaps(IndexedFastaReader, refFname)
        self.alnF = perhaps(openIndexedAlignmentFile, alnFname, refFname)

        # Pls requires a little bit of special handling
        if plsFname is not None and plsFname.endswith(".bam"):
            if plsFname == basFname:
                self.plsF = self.basF
            else:
                self.plsF = ZmwReadStitcher(plsFname)
            if not self.plsF.hasPulses:
                raise ValueError, "Pulse BAM file lacks required features (need --internal mode basecaller run)"
        else:
            self.plsF = perhaps(PlsH5Reader, plsFname, self.basF)

        if self.alnF is not None:
            if len(self.alnF.movieNames) > 1:
                raise ValueError, "No support for multi-movie jobs"
        if self.trcF is None:
            raise ValueError, "trc.h5 required, for now"

    @staticmethod
    def fromIniFile(iniFilename, sectionName):
        iniFilename = op.abspath(op.expanduser(iniFilename))

        def resolvePath(path):
            """
            Path may be given
              - as relative to the ini file path
              - qualified with "~"
            Resolve it whatever it is.
            None is passed through.
            """
            if path is None: return None
            iniDirectory = op.dirname(iniFilename)
            path = op.expanduser(path)
            if op.isabs(path):
                return path
            else:
                return op.abspath(op.join(iniDirectory, path))

        cp = ConfigParser()
        cp.optionxform=str
        cp.read(iniFilename)
        opts = dict(cp.items(sectionName))
        return Fixture(trcFname=resolvePath(opts.get("Traces")),
                              plsFname=resolvePath(opts.get("Pulses")),
                              basFname=resolvePath(opts.get("Bases")),
                              refFname=resolvePath(opts.get("Reference")),
                              alnFname=resolvePath(opts.get("Alignments")))

    def toIni(self, sectionName=None):
        if sectionName is not None:
            ini = "[%s]\n" % sectionName
        else:
            ini = ""
        if self.trcF is not None: ini += "Traces=%s\n"     % self.trcF.filename
        if self.basF is not None: ini += "Bases=%s\n"      % self.basF.filename
        if self.plsF is not None: ini += "Pulses=%s\n"     % self.plsF.filename
        if self.refF is not None: ini += "Reference=%s\n"  % self.refF.filename
        if self.alnF is not None: ini += "Alignments=%s\n" % self.alnF.filename
        return ini

    def __repr__(self):
        import pprint
        readerFieldNames = [ fn for fn in dir(self) if fn.endswith("F") ]
        readersRepr = "\n  " + ",\n  ".join(["%s=%s" % (fieldName, getattr(self, fieldName))
                            for fieldName in readerFieldNames])
        return "<Fixture %s >" % readersRepr


    # -- Essential info ---

    @property
    def platform(self):
        if self.trcF.numChannels == 2:
            return "Sequel"
        elif self.trcF.numChannels == 4:
            return "RS"
        else:
            raise Exception, "unrecognized platform"

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
    @cached
    def holeNumbers(self):
        return sorted(set.intersection(set(self.trcF.holeNumbers),
                                       set(self.basF.allSequencingZmws)))

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
            return FixtureZmw(self, holeNumber)



__doc__ = \
"""
Usage:
  fixture.py <iniFile> <sectionName>
"""

def main():
    args = docopt(__doc__)
    fx = Fixture.fromIniFile(args["<iniFile>"], args["<sectionName>"])
    print fx

if __name__ == '__main__':
    main()
